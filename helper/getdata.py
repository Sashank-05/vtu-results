import os
import random
import cv2 as cv
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from helper import dbhandler, extract_table, processing, df_to_csv
from captcha import Captcha

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'


class FillForm:
    def __init__(self, base_url, usn_prefix, start_range, end_range, db_table):
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.start_range = start_range
        self.end_range = end_range
        self.db_table = db_table
        self.fail_count = 0

        # Selenium Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(service=Service(), options=chrome_options)

        # Directory for invalid CAPTCHA images
        self.invalid_captcha_dir = "invalid_captchas"
        os.makedirs(self.invalid_captcha_dir, exist_ok=True)

    def handle_alert(self, usn):
        alert = self.driver.switch_to.alert
        if alert.text == "University Seat Number is not available or Invalid..!":
            print("No results for: " + usn + "\n")
            alert.accept()

        elif alert.text == "Invalid captcha code !!!":
            print("Invalid CAPTCHA Detected for USN: " + usn + "\n")
            alert.accept()
            self.fail_count += 1

            self.fill_form(usn)

    def fill_form(self, usn):
        print(usn)
        try:
            self.driver.get(self.base_url)
            self.driver.implicitly_wait(25)
            usnbox = self.driver.find_element("name", "lns")
            cap = self.driver.find_element("name", "captchacode")
            usnbox.send_keys(usn)
            capt = self.driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")
            image = cv.imread("current.png")
            text = Captcha(image).solve_color()
            print(text)
        except UnexpectedAlertPresentException:
            self.handle_alert(usn)
            cv.imwrite(f"{self.invalid_captcha_dir}/{usn}_{random.randint(1000, 9999)}.png", image)
            return

        try:
            cap.send_keys(text)
            self.driver.find_element('id', "submit").click()
            try:
                self.handle_alert(usn)
            except NoAlertPresentException:
                pass
            except Exception as e:
                raise e
        except Exception as e:
            print(e)
            self.fill_form(usn)
            return
        finally:
            if "Student Name" in self.driver.page_source:
                with open(f"pages/{usn}.html", "w", encoding="utf8") as file:
                    file.write(self.driver.page_source)
            else:
                print(f"Couldn't Save page for USN: {usn}")
                self.fill_form(usn)
                return

    def run(self):
        for i in range(self.start_range, self.end_range + 1):
            usn = f"{self.usn_prefix}{i:03d}"
            self.fill_form(usn)

        print(f"Total failed attempts: {self.fail_count}")

    def check_pages(self):
        cool = 0
        nah = 0
        whoisnah = []
        for i in os.listdir("pages"):
            if i.endswith(".html"):
                with open(f"pages/{i}", "r", encoding="utf8") as file:
                    if "Student Name" in file.read():
                        cool += 1
                    else:
                        nah += 1
                        whoisnah.append(i)

        print(f"Cool attempts: {cool}")
        print(f"Nah attempts: {nah}")
        print(f"Whoisnah: {whoisnah}")

    def save_to_db(self):
        files = os.listdir("pages")
        df, _ = extract_table.extractor(fr"pages\{files[0]}")
        columns = processing.get_subject_code(df)

        table = dbhandler.DBHandler()
        table.create_table_columns(self.db_table, columns)

        for file in files:
            df_new, other = extract_table.extractor(fr"pages\{file}")
            # df_to_csv.convert(df_new, other)
            inte, ext, lis = processing.df_to_sql(df_new, other)
            table.push_data_into_table(self.db_table, inte, ext, lis)

            os.remove(fr"pages\{file}")

        table.close()
