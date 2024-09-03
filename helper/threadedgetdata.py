import os
import random
import threading

import cv2 as cv
import pytesseract
import selenium.common.exceptions
from flask_socketio import emit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from captcha import Captcha
from helper import extract_table, df_to_csv, processing, dbhandler

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'


class FillForm:
    def __init__(self, base_url, usn_prefix, start_range, end_range, db_table, socketio):
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.start_range = start_range
        self.end_range = end_range
        self.db_table = db_table
        self.fail_count = 0
        self.socketio = socketio

        print(f"Starting thread for USN range: {self.start_range} to {self.end_range} (-_-\")")

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

        # Prepare directory for saving HTML pages
        self.pages_dir = "pages"
        os.makedirs(self.pages_dir, exist_ok=True)

    def handle_alert(self, usn):
        try:
            alert = self.driver.switch_to.alert
            if alert.text == "University Seat Number is not available or Invalid..!":
                print(f"No results for: {usn}\n")
                alert.accept()

            elif alert.text == "Invalid captcha code !!!":
                print(f"Invalid CAPTCHA Detected for USN: {usn}\n")
                alert.accept()
                self.fail_count += 1
                self.fill_form(usn)

        except selenium.common.exceptions.NoAlertPresentException:
            pass

    def fill_form(self, usn):
        try:
            self.driver.get(self.base_url)
            self.driver.implicitly_wait(25)
            usnbox = self.driver.find_element("name", "lns")
            cap = self.driver.find_element("name", "captchacode")
            usnbox.send_keys(usn)
            self.driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")

            image = cv.imread("current.png")
            text = Captcha(image).solve_color()
            print(f"Detected CAPTCHA Text: {text}")

            cap.send_keys(text)
            self.driver.find_element('id', "submit").click()

            self.handle_alert(usn)

            self.driver.implicitly_wait(25)

            if "Student Name" in self.driver.page_source:
                with open(f"pages/{usn}.html", "w", encoding="utf8") as file:
                    file.write(self.driver.page_source)
                    self.socketio.emit('update', {'usn': usn}, namespace='/')
            else:
                print(f"Couldn't Save page for USN: {usn}")
                self.fail_count += 1
                self.fill_form(usn)

        except selenium.common.exceptions.UnexpectedAlertPresentException:
            self.handle_alert(usn)
            self.save_invalid_captcha(usn)
            self.fill_form(usn)

        except Exception as e:
            print(f"Exception occurred: {e}")
            self.save_invalid_captcha(usn)
            self.fill_form(usn)

    def save_invalid_captcha(self, usn):
        image = cv.imread("current.png")
        file_name = f"{usn}_{random.randint(1000, 9999)}.png"
        cv.imwrite(os.path.join(self.invalid_captcha_dir, file_name), image)
        print(f"Saved invalid CAPTCHA image for USN: {usn}")

    def run(self):
        for i in range(self.start_range, self.end_range + 1):
            usn = f"{self.usn_prefix}{i:03d}"
            self.fill_form(usn)

        print(f"Total failed attempts: {self.fail_count}")


class ThreadManager:
    def __init__(self, base_url, usn_prefix, db_table, end_usn=None, ranges=None, num_threads=4, socketio=None):
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.ranges = ranges
        self.db_table = db_table
        self.num_threads = num_threads
        self.end_usn = int(end_usn)
        self.socketio = socketio

        if end_usn is None and ranges is None:
            raise ValueError("Either end_usn or ranges must be provided")

        if ranges is None:
            self.ranges = self.div_usns()

    def run_threads(self):
        threads = []
        for r in self.ranges:
            start_range, end_range = r
            fill_form_instance = FillForm(self.base_url, self.usn_prefix, start_range, end_range, self.db_table,
                                          self.socketio)
            thread = threading.Thread(target=fill_form_instance.run)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.save_to_db()

        emit('update', {'usn': 'done'}, namespace='/')

    def div_usns(self):
        # divide into ranges
        total_usns = int(self.end_usn)
        num_threads = int(self.num_threads)

        base_range_size = int(total_usns // num_threads)
        remainder = int(total_usns % num_threads)

        current_start = 1
        ranges = []

        for i in range(num_threads):
            range_size = base_range_size + (1 if i < remainder else 0)
            current_end = current_start + range_size - 1
            ranges.append((current_start, current_end))
            current_start = current_end + 1

        return ranges


def save_to_db(self):
    files = os.listdir("pages")
    print(files)
    x, y = extract_table.extractor(f"pages/{files[0]}")
    df, _ = extract_table.cal(x, y)
    columns = processing.get_subject_code(df)

    table = dbhandler.DBHandler()
    try:
        table.create_table_columns(self.db_table, columns)
    except:
        print("Table already created")

    for file in files:
        x, y = extract_table.extractor(f"pages/{file}")
        df_new, other = extract_table.cal(x, y)
        df_to_csv.convert(df_new, other)
        inte, ext, lis = processing.df_to_sql(df_new, other)
        table.push_data_into_table(self.db_table, inte, ext, lis)

    table.close()


if __name__ == "__main__":
    # 1 to 56 divided into 5 ranges
    start_usn = 1
    end_usn = 56
    num_threads = 10

    thread_manager = ThreadManager("https://results.vtu.ac.in/DJcbcs24/index.php", "1BI23CD", "BI23CD_SEM_1", 56,
                                   num_threads=10)
    thread_manager.run_threads()
