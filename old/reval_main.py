import os
import cv2 as cv
import pytesseract
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from helpers.captcha import Captcha
from helper import extract_table, processing, df_to_csv
from helpers import dbhandler

# Configuration for pytesseract and Chrome WebDriver
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(service=Service(), options=chrome_options)

# Directories and counters
os.makedirs("invalid_captchas", exist_ok=True)
fail_count = 0
no_usn = []


def handle_alert(usn):
    """Handle alert pop-ups during the process."""
    global fail_count, no_usn
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()

        if "Invalid" in alert_text or "not available" in alert_text:
            print(f"No results for: {usn}")
            no_usn.append(usn)
        elif "Invalid captcha" in alert_text:
            print(f"Invalid CAPTCHA Detected for USN: {usn}")
            fail_count += 1
            fill_form(usn)
    except selenium.common.NoAlertPresentException:
        pass


def fill_form(usn):
    """Fill the form on the page and handle CAPTCHA."""
    global fail_count
    print(f"Processing USN: {usn}")

    try:
        driver.get("https://results.vtu.ac.in/DJRVcbcs24/index.php")
        driver.implicitly_wait(25)

        driver.find_element("name", "lns").send_keys(usn)
        driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")

        image = cv.imread("current.png")
        text = Captcha(image).solve_color()
        print(f"CAPTCHA solved: {text}")

        driver.find_element("name", "captchacode").send_keys(text)
        driver.find_element('id', "submit").click()

        handle_alert(usn)

        if "Student Name" in driver.page_source:
            save_page(usn)
        else:
            retry_form(usn)
    except Exception as e:
        print(f"Error processing USN {usn}: {e}")
        retry_form(usn)


def retry_form(usn):
    """Retry filling the form if the process failed."""
    if usn not in no_usn:
        print(f"Retrying USN: {usn}")
        fill_form(usn)


def save_page(usn):
    """Save the result page if the data is present."""
    page_content = driver.page_source
    if "Student Name" in page_content:
        with open(f"reval_pages/{usn}.html", "w", encoding="utf8") as file:
            file.write(page_content)
        print(f"Page saved for USN: {usn}")
    else:
        retry_form(usn)


def main():
    """Main function to process a list of USNs."""
    for i in range(1, 56):
        usn = f"1BI23CD{i:03d}"
        fill_form(usn)
    print(f"Total failed CAPTCHA attempts: {fail_count}")


def check_pages():
    """Check saved pages for successful data extraction."""
    cool, nah = 0, 0
    whoisnah = []

    for filename in os.listdir("pages"):
        if filename.endswith(".html"):
            with open(f"pages/{filename}", "r", encoding="utf8") as file:
                if "Student Name" in file.read():
                    cool += 1
                else:
                    nah += 1
                    whoisnah.append(filename)

    print(f"Successful attempts: {cool}")
    print(f"Failed attempts: {nah}")
    print(f"Failed USNs: {whoisnah}")


def save_to_db():
    """Save extracted data to the database."""
    files = os.listdir("pages")
    df, _ = extract_table.extractor(f"pages/{files[0]}")
    columns = processing.get_subject_code(df)

    table = dbhandler.DBHandler()
    table.create_table_columns('BI23CD_SEM_1', columns)

    for file in files:
        df_new, other = extract_table.extractor(f"pages/{file}")
        df_to_csv.convert(df_new, other)
        inte, ext, lis = processing.df_to_sql(df_new, other)
        table.push_data_into_table('BI23CD_SEM_1', inte, ext, lis)

    table.close()


def show_columns():
    """Show database columns."""
    table = dbhandler.DBHandler()
    columns = table.get_columns('BI23CD_SEM_2')
    print(columns)


if __name__ == "__main__":
    main()
    # Uncomment the following lines if you need to use these functions
    # check_pages()
    # save_to_db()
    # show_columns()
