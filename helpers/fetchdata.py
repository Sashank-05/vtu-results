import logging
import os
import random
import threading

import cv2 as cv
import pytesseract
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

if os.getcwd().endswith("helpers"):
    from captcha import Captcha
    from extract_table import extractor,cal
    from formats import dataframe_to_sql,df_to_csv,get_subject_code
    import dbhandler

    base = "../tempwork/"
else:
    from helpers.captcha import Captcha
    from extract_table import extractor,cal
    from formats import dataframe_to_sql,df_to_csv,get_subject_code
    import dbhandler

    base = "tempwork/"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

history = {}
global_fails = 0


class FillForm:
    def __init__(self, base_url, usn_prefix, start_range, end_range, db_table, socketio):
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.start_range = start_range
        self.end_range = end_range
        self.db_table = db_table
        self.fail_count = 0
        self.socketio = socketio

        logging.info(f"Starting thread for USN range: {self.start_range} to {self.end_range} (-_-\")")

        # Selenium Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(service=Service(), options=chrome_options)

        # Prepare directory for saving HTML pages
        self.pages_dir = "pages"
        self.current_dir="current"
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
            logging.error(f"Exception occurred: {e}")
            self.fill_form(usn)
            return

    def save_invalid_captcha(self, usn):
        image = cv.imread("current.png")
        file_name = f"{usn}_{random.randint(1000, 9999)}.png"
        cv.imwrite(os.path.join(self.invalid_captcha_dir, file_name), image)
        logging.info(f"Saved invalid CAPTCHA image for USN: {usn}")

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
        paths= os.path.join(base,"pages/")
        print(paths)
        print(os.listdir(paths))
        x, y = extractor()
        print()
        df, _ = cal(x, y)
        columns = get_subject_code(df)
        # vtu-results\tempwork\pages
        table = dbhandler.DBHandler()
        try:
            table.create_table_columns(self.db_table, columns)
        except:
            print("Table already created")

        for file in files:
            x, y = extractor(f"pages/{file}")
            df_new, other = cal(x, y)
            df_to_csv.convert(df_new, other)
            inte, ext, lis = dataframe_to_sql(df_new, other)
            table.push_data_into_table(self.db_table, inte, ext, lis)
            os.remove('pages/'+file)

        table.close()




if __name__ == "__main__":
    #thread_manager = ThreadManager("https://results.vtu.ac.in/DJcbcs24/index.php", "1BI23CD",
       #                            "BI23ec_SEM_1", 50, num_threads=5)
    #thread_manager.run_threads()
    #print(f"Total global failed attempts: {global_fails}")
    ThreadManager.save_to_db("self")
