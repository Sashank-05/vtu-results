import logging
import os
import sqlite3
import threading

import cv2 as cv
import pytesseract
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

if os.getcwd().endswith("helpers"):
    from captcha import Captcha
    from extract import Extract
    from new_helpers.formats import dataframe_to_sql

    import dbhandler

    base = "../tempwork/"
else:
    from new_helpers.captcha import Captcha
    from new_helpers.extract import Extract
    from new_helpers.formats import dataframe_to_sql, get_subject_code
    from new_helpers import dbhandler

    base = "tempwork/"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s - '
                                               '[%(filename)s:%(lineno)d in %(funcName)s]')

history = {}
global_fails = 0


class FillForm:
    def __init__(self, base_url, usn_prefix, start_range, end_range, db_table, socketio, driver=None):
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.start_range = start_range
        self.end_range = end_range
        self.db_table = db_table
        self.fail_count = 0
        self.socketio = socketio

        logging.info(f"Starting thread for USN range: {self.start_range} to {self.end_range}")

        if driver is None:
            # Selenium Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")

            self.driver = webdriver.Chrome(service=Service(), options=chrome_options)
        else:
            self.driver = driver

        # Prepare directory for saving HTML pages
        self.pages_dir = "pages"
        self.current_dir = "current"
        os.makedirs(base + self.pages_dir, exist_ok=True)
        os.makedirs(base + self.current_dir, exist_ok=True)

    def handle_alert(self, usn):
        try:
            alert = self.driver.switch_to.alert
            if alert.text == "University Seat Number is not available or Invalid..!":
                logging.info(f"No results for: {usn}")
                alert.accept()
                return

            elif alert.text == "Invalid captcha code !!!":
                logging.info(f"Invalid CAPTCHA Detected for USN: {usn}")
                alert.accept()
                self.fail_count += 1
                self.fill_form(usn)

        except selenium.common.exceptions.NoAlertPresentException:
            pass

    def fill_form(self, usn):
        if usn in history:
            history[usn] += 1
        else:
            history[usn] = 1
        if history[usn] > 20:
            logging.info(f"Failed more than 20 times for USN: {usn}")
            self.socketio.emit('update', {'failed': usn}, namespace='/')
            return
        try:
            self.driver.get(self.base_url)
            self.driver.implicitly_wait(25)
            usnbox = self.driver.find_element("name", "lns")
            cap = self.driver.find_element("name", "captchacode")
            usnbox.send_keys(usn)
            self.driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot(
                base + "current/" + usn + "_current.png")

            image = cv.imread(base + "current/" + usn + "_current.png")
            text = Captcha(image).solve_color()

            os.remove(base + "current/" + usn + "_current.png")

            logging.info(f"Detected CAPTCHA Text: {text}")
            if len(text) > 6 or ' ' in text:
                raise Exception("Invalid CAPTCHA detected; Length not 6")

            cap.send_keys(text)

            self.driver.find_element('id', "submit").click()

            self.handle_alert(usn)

            self.driver.implicitly_wait(25)

            if "Student Name" in self.driver.page_source:
                with open(base + f"pages/{usn}.html", "w", encoding="utf8") as file:
                    file.write(self.driver.page_source)
                    try:
                        self.socketio.emit('update', {'usn': usn}, namespace='/')
                    except AttributeError:
                        pass
            else:
                logging.info(f"Couldn't Save page for USN: {usn}")
                self.fail_count += 1
                self.fill_form(usn)

        except selenium.common.exceptions.UnexpectedAlertPresentException:
            self.handle_alert(usn)
            # self.save_invalid_captcha(usn)
            self.fill_form(usn)
            return

        except Exception as e:
            logging.error(f"Exception occurred: {e}", exc_info=True)
            self.fill_form(usn)
            return

    def run(self):
        global global_fails
        for i in range(self.start_range, self.end_range + 1):
            usn = f"{self.usn_prefix}{i:03d}"
            self.fill_form(usn)

        logging.info(f"Total failed attempts: {self.fail_count}")
        global_fails += self.fail_count


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
        try:
            self.socketio.emit('update', {'usn': 'started', 'end_usn': self.end_usn}, namespace='/')
        except AttributeError:
            pass

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

        try:
            self.socketio.emit('update', {'usn': 'done'}, namespace='/')
            print(f"Total global failed attempts: {global_fails}")
            self.save_to_db()
        except AttributeError:
            pass

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
        files = os.listdir(base + "pages")
        files = [f for f in files if f.endswith(".html") and f.startswith(self.usn_prefix)]
        dbcursor = dbhandler.DBHandler()
        # extract tables
        for file in files:
            df = Extract(base + f"pages/{file}")
            print(df)
            dfdict = df.get_dfs()

            for sem in dfdict.keys():
                if sem == "Name" or sem == "USN" or dfdict[sem] is None:
                    continue
                details = df.calculate(dfdict[sem])
                # now get table name from usn_prefix and sem
                table_name = f"X{self.usn_prefix}_SEM_{sem}"
                try:
                    columns = []
                    for col in dfdict[sem]["Subject Code"]:
                        columns.append(col + "_internal")
                        columns.append(col + "_external")
                    columns.append("Total")
                    columns.append("CGPA")
                    columns.append("Pass")
                    columns.append("Absent")
                    
                    dbcursor.create_table_columns(table_name, columns)
                    print("created table")


                except sqlite3.OperationalError as e:
                    if "already exists" in str(e):
                        print("already exists")
                    elif "duplicate column name" in str(e):
                        print("duplicate")
                    else:
                        logging.error(f"Error creating table: {e}")
                finally:
                    inte, exte = dataframe_to_sql(details[0])
                    additional_data = [dfdict["Name"], dfdict["USN"]]+details[1]
                    dbcursor.push_data_into_table(table_name, inte, exte, additional_data)
                    print(f"Pushed data for {table_name}")
                    print(inte, exte, additional_data)

        # check if table is already created
        # if not create table
        # if table and data exists => get the table, check for changed values, then update
        # push data into table



if __name__ == "__main__":
    thread_manager = ThreadManager("https://results.vtu.ac.in/DJcbcs24/index.php", "1BI22CD",
                                   "1BI22CD", 240, num_threads=8)
    # thread_manager.run_threads()
    print(f"Total global failed attempts: {global_fails}")
    thread_manager.save_to_db()
