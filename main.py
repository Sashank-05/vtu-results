import os
import random

import cv2 as cv
import pytesseract
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from captcha import Captcha
from helper import dbhandler, extract_table, processing, df_to_csv, test

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# Selenium Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Uncomment this if you want to run headless
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(service=Service(), options=chrome_options)

# Directory for invalid CAPTCHA images
invalid_captcha_dir = "invalid_captchas"
os.makedirs(invalid_captcha_dir, exist_ok=True)

# Counter for failed CAPTCHA attempts
fail_count = 0


def handle_alert(usn):
    global fail_count
    try:
        alert = driver.switch_to.alert
        if alert.text == "University Seat Number is not available or Invalid..!":
            print(f"No results for: {usn}\n")
            alert.accept()

        elif alert.text == "Invalid captcha code !!!":
            print(f"Invalid CAPTCHA Detected for USN: {usn}\n")
            alert.accept()
            fail_count += 1
            fill_form(usn)

    except selenium.common.exceptions.NoAlertPresentException:
        pass


def fill_form(usn):
    global fail_count
    try:
        driver.get("https://results.vtu.ac.in/DJcbcs24/index.php")
        driver.implicitly_wait(25)
        usnbox = driver.find_element("name", "lns")
        cap = driver.find_element("name", "captchacode")
        usnbox.send_keys(usn)
        driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")

        image = cv.imread("current.png")
        text = Captcha(image).solve_color()
        print(f"Detected CAPTCHA Text: {text}")

        cap.send_keys(text)
        driver.find_element('id', "submit").click()

        handle_alert(usn)

        if "Student Name" in driver.page_source:
            with open(f"pages/{usn}.html", "w", encoding="utf8") as file:
                file.write(driver.page_source)
        else:
            print(f"Couldn't Save page for USN: {usn}")
            fail_count += 1
            fill_form(usn)

    except selenium.common.exceptions.UnexpectedAlertPresentException:
        handle_alert(usn)
        save_invalid_captcha(usn)
        fill_form(usn)

    except Exception as e:
        print(f"Exception occurred: {e}")
        save_invalid_captcha(usn)
        fill_form(usn)


def save_invalid_captcha(usn):
    image = cv.imread("current.png")
    file_name = f"{usn}_{random.randint(1000, 9999)}.png"
    cv.imwrite(os.path.join(invalid_captcha_dir, file_name), image)
    print(f"Saved invalid CAPTCHA image for USN: {usn}")


def main():
    global fail_count
    for i in range(1, 57):
        usn = f"1BI23CD{i:03d}"
        fill_form(usn)
    print(f"Total failed attempts: {fail_count}")


def check_pages():
    cool = 0
    nah = 0
    whoisnah = []
    for filename in os.listdir("pages"):
        if filename.endswith(".html"):
            with open(f"pages/{filename}", "r", encoding="utf8") as file:
                if "Student Name" in file.read():
                    cool += 1
                else:
                    nah += 1
                    whoisnah.append(filename)

    print(f"Cool attempts: {cool}")
    print(f"Nah attempts: {nah}")
    print(f"Whoisnah: {whoisnah}")


def save_to_db():
    files = os.listdir("pages")
    x, y = extract_table.extractor(f"pages/{files[0]}")
    df, _ = extract_table.cal(x, y)
    columns = processing.get_subject_code(df)

    table = dbhandler.DBHandler()
    table.create_table_columns('BI23CD_SEM_1', columns)

    for file in files:
        x, y = extract_table.extractor(f"pages/{file}")
        df_new, other = extract_table.cal(x, y)
        df_to_csv.convert(df_new, other)
        inte, ext, lis = processing.df_to_sql(df_new, other)
        table.push_data_into_table('BI23CD_SEM_1', inte, ext, lis)

    table.close()


def show_columns():
    table = dbhandler.DBHandler()
    columns = table.get_columns('BI23CD_SEM_2')
    print(columns)


if __name__ == "__main__":
    test.neat_marks(2,"1bi23cd055")

    main()
    check_pages()
    #save_to_db()
    #show_columns()
