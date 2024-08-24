import os
import random

import cv2 as cv
import pytesseract
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from captcha import Captcha
from helper import dbhandler, extract_table, processing, df_to_csv

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
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

text, image, cap = None, None, None


def handle_alert(usn):
    global fail_count, image

    alert = driver.switch_to.alert
    if alert.text == "University Seat Number is not available or Invalid..!" or alert.text=="You have not applied for reval or reval results are awaited !!!":
        print("No results for: " + usn + "\n")
        alert.accept()
    
    

    elif alert.text == "Invalid captcha code !!!":
        print("Invalid CAPTCHA Detected for USN: " + usn + "\n")
        alert.accept()
        fail_count += 1

        fill_form(usn)


def fill_form(usn):
    global text, cap, image
    print(usn)
    try:
        #driver.get("https://results.vtu.ac.in/JJEcbcs24/index.php") sem 2 
        #driver.get("https://results.vtu.ac.in/DJcbcs24/index.php") SEM1
        driver.get("https://results.vtu.ac.in/DJRVcbcs24/index.php") #sem reval

        driver.implicitly_wait(25)
        usnbox = driver.find_element("name", "lns")
        cap = driver.find_element("name", "captchacode")
        usnbox.send_keys(usn)
        capt = driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")
        image = cv.imread("current.png")
        # text = Captcha(image).solve_invert()
        text = Captcha(image).solve_color()
        # check if text 1 and text 2 are same
        # if text1 == text2:
        #    text = text1
        # else:
        #   text = text2
        print(text)
    except selenium.common.exceptions.UnexpectedAlertPresentException:
        handle_alert(usn)
        cv.imwrite(f"invalid_captchas/{usn}_{random.Random(2000)}.png", image)

    try:
        cap.send_keys(text)
        driver.find_element('id', "submit").click()
        try:
            handle_alert(usn)
        except selenium.common.exceptions.NoAlertPresentException:
            pass
        except:
            raise
    except Exception as e:
        print(e)
        fill_form(usn)
        return
    finally:
        if "Student Name" in driver.page_source:
            with open("reval_pages/" + str(usn) + ".html", "w", encoding="utf8") as file:
                file.write(driver.page_source)
        else:
            print("Couldn't Save page for USN :", usn)
            #fill_form(usn)
            return


def main():
    for i in range(55,57):
        usn = f"1BI23CD{i:03d}"
        fill_form(usn)

    print(f"Total failed attempts: {fail_count}")


def check_pages():
    cool = 0
    nah = 0
    whoisnah = []
    for i in os.listdir("pages"):
        if i.endswith(".html"):
            with open("pages/" + i, "r", encoding="utf8") as file:
                if "Student Name" in file.read():
                    cool += 1
                else:
                    nah += 1
                    whoisnah.append(i)

    print(f"Cool attempts: {cool}")
    print(f"Nah attempts: {nah}")
    print(f"Whoisnah: {whoisnah}")


def save_to_db():
    files = os.listdir("pages")
    df, _ = extract_table.extractor(fr"pages\{files[0]}")
    columns = processing.get_subject_code(df)

    table = dbhandler.DBHandler()
    table.create_table_columns('BI23CD_SEM_1', columns)

    for file in files:
        df_new, other = extract_table.extractor(fr"pages\{file}")
        df_to_csv.convert(df_new, other)
        inte, ext, lis = processing.df_to_sql(df_new, other)
        table.push_data_into_table('BI23CD_SEM_1', inte, ext, lis)

    table.close()


def show_columns():
    table = dbhandler.DBHandler()
    columns=table.get_columns('BI23CD_SEM_2')
    print(columns)





if __name__ == "__main__":
    main()
    #check_pages()
    #save_to_db()
    #show_columns()



