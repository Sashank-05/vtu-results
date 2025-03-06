import logging
import os
import sqlite3
import threading
from io import BytesIO

import cv2 as cv
import numpy as np
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure paths and imports based on project structure
if os.getcwd().endswith("helpers"):
    from captcha import Captcha
    from extract import Extract
    from formats import dataframe_to_sql,get_subject_code
    import dbhandler

    BASE_DIR = "../tempwork/"
else:
    from new_helpers.captcha import Captcha
    from new_helpers.extract import Extract
    from new_helpers.formats import dataframe_to_sql,get_subject_code
    from new_helpers import dbhandler

    BASE_DIR = "tempwork/"

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, 'scraper.log'))
    ]
)


class ThreadSafeSet:
    """Thread-safe set to store failed USNs using a semaphore for mutual exclusion."""

    def __init__(self):
        self._set = set()  # Internal set to store items
        self._semaphore = threading.Semaphore(1)  # Semaphore initialized to 1 (acts as a mutex)

    def add(self, item):
        """Add an item to the set in a thread-safe manner."""
        self._semaphore.acquire()  # Lock the semaphore (enter critical section)
        try:
            self._set.add(item)  # Add the item to the set
        finally:
            self._semaphore.release()  # Unlock the semaphore (exit critical section)

    def pop_all(self):
        """Remove and return all items from the set in a thread-safe manner."""
        self._semaphore.acquire()  # Lock the semaphore (enter critical section)
        try:
            items = list(self._set)  # Copy all items to a list
            self._set.clear()  # Clear the set
            return items  # Return the list of items
        finally:
            self._semaphore.release()  # Unlock the semaphore (exit critical section)


# Global variable to track failed USNs
global_fails = ThreadSafeSet()


class FillForm:
    def __init__(self, usn_list, base_url, usn_prefix, db_table, socketio=None, is_retry=False):
        self.usn_list = usn_list
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.db_table = db_table
        self.socketio = socketio
        self.is_retry = is_retry
        self.driver = self._create_driver()
        self._prepare_directories()

    def _create_driver(self):
        """Create and configure the Selenium WebDriver."""
        chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")
        return webdriver.Chrome(service=Service(), options=chrome_options)

    def _prepare_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(os.path.join(BASE_DIR, "pages"), exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, "current"), exist_ok=True)

    def _process_captcha(self):
        """Process CAPTCHA image and extract text."""
        try:
            captcha_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//img[@alt="CAPTCHA code"]'))
            )
            png_data = captcha_element.screenshot_as_png
            image = cv.imdecode(np.frombuffer(png_data, np.uint8), cv.IMREAD_COLOR)
            return Captcha(image).solve_color()
        except Exception as e:
            logging.error(f"CAPTCHA processing failed: {e}")
            return None

    def _handle_alert(self):
        """Handle any alert popups."""
        try:
            alert = WebDriverWait(self.driver, 2).until(EC.alert_is_present())
            alert_text = alert.text
            alert.accept()
            return alert_text
        except:
            return None

    def _process_usn(self, usn):
        """Process a single USN."""
        max_attempts = 10 if self.is_retry else 5
        for attempt in range(1, max_attempts + 1):
            try:
                self.driver.get(self.base_url)
                status_prefix = "[RETRY] " if self.is_retry else ""
                logging.info(f"{status_prefix}Processing {usn} (Attempt {attempt}/{max_attempts})")

                captcha_text = self._process_captcha()
                if not captcha_text or len(captcha_text) != 6:
                    raise ValueError("Invalid CAPTCHA generated")

                self.driver.find_element(By.NAME, "lns").send_keys(usn)
                self.driver.find_element(By.NAME, "captchacode").send_keys(captcha_text)
                self.driver.find_element(By.ID, "submit").click()

                alert_text = self._handle_alert()
                if alert_text:
                    if "Invalid captcha" in alert_text:
                        logging.warning(f"{status_prefix}Invalid CAPTCHA for {usn}")
                        continue
                    if "not available" in alert_text:
                        logging.info(f"{status_prefix}USN not found: {usn}")
                        return False

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Student Name')]"))
                )

                self._save_results(usn)
                logging.info(f"{status_prefix}Successfully processed {usn}")
                return True

            except Exception as e:
                logging.error(f"{status_prefix}Error processing {usn}: {str(e)}")
                if attempt == max_attempts:
                    logging.error(f"{status_prefix}Failed to process {usn} after {max_attempts} attempts")
                    global_fails.add(usn)
                    if self.socketio:
                        self.socketio.emit('update', {'failed': usn}, namespace='/')
        return False

    def _save_results(self, usn):
        """Save the results page for a successful USN."""
        page_path = os.path.join(BASE_DIR, "pages", f"{usn}.html")
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        if self.socketio:
            self.socketio.emit('update', {'usn': usn}, namespace='/')

    def run(self):
        """Process all USNs in the list."""
        total = len(self.usn_list)
        for i, usn in enumerate(self.usn_list, 1):
            success = self._process_usn(usn)
            progress = f"[{'RETRY' if self.is_retry else 'MAIN'}] [{i}/{total}]".ljust(15)
            status = "SUCCESS" if success else "FAILED"
            print(f"{progress} {usn}: {status}")


class ThreadManager:
    def __init__(self, base_url, usn_prefix, db_table, end_usn=None, ranges=None, num_threads=4, socketio=None):
        self.base_url = base_url
        self.usn_prefix = usn_prefix
        self.db_table = db_table
        self.socketio = socketio
        self.num_threads = num_threads
        self.ranges = ranges or self._calculate_ranges(end_usn, num_threads)
        self.max_retries = 2  # Configurable retry attempts

    def _calculate_ranges(self, end_usn, num_threads):
        """Divide USNs into ranges for threading."""
        num_threads=int(num_threads)
        end_usn=int(end_usn)
        base_range = int(end_usn) // int(num_threads)
        remainder = end_usn % num_threads
        ranges = []
        current = 1

        for i in range(num_threads):
            end = current + base_range - 1
            if i < remainder:
                end += 1
            ranges.append((current, end))
            current = end + 1

        return ranges

    def _generate_usns(self, range_tuple):
        """Generate USNs from a range tuple."""
        start, end = range_tuple
        return [f"{self.usn_prefix}{num:03d}" for num in range(start, end + 1)]

    def _chunk_list(self, lst, n):
        """Split list into n roughly equal chunks."""
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

    def _process_batch(self, batches, phase_name, is_retry=False):
        """Process a batch of USNs."""
        print(f"\n{' %s Phase ' % phase_name:=^50}")
        threads = []
        for batch in batches:
            thread = threading.Thread(
                target=FillForm(
                    usn_list=self._generate_usns(batch) if not is_retry else batch,
                    base_url=self.base_url,
                    usn_prefix=self.usn_prefix,
                    db_table=self.db_table,
                    socketio=self.socketio,
                    is_retry=is_retry
                ).run
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def _count_processed_usns(self):
        """Count successfully processed USNs."""
        processed = set()
        for f in os.listdir(os.path.join(BASE_DIR, "pages")):
            if f.startswith(self.usn_prefix) and f.endswith(".html"):
                processed.add(f.split(".")[0])
        return len(processed)

    def run_threads(self):
        """Main method to run the scraper with retries."""
        # Initial processing
        self._process_batch(self.ranges, "Main")

        # Retry failed USNs
        for retry_attempt in range(1, self.max_retries + 1):
            failed_usns = global_fails.pop_all()
            if not failed_usns:
                break

            print(f"\n{' Retrying Failed USNs ':=^50}")
            print(f"Retry attempt {retry_attempt}/{self.max_retries}")
            print(f"Failed USNs to retry: {len(failed_usns)}")
            print("USNs: ", ", ".join(sorted(failed_usns)))

            retry_batches = self._chunk_list(failed_usns, self.num_threads)
            self._process_batch(retry_batches, f"Retry {retry_attempt}", is_retry=True)

        # Final output
        remaining_fails = global_fails.pop_all()
        print(f"\n{' Final Results ':=^50}")
        print(f"Total successfully processed: {self._count_processed_usns()}")
        print(f"Total permanent failures: {len(remaining_fails)}")
        if remaining_fails:
            print("Permanent failures:", ", ".join(sorted(remaining_fails)))

        if self.socketio:
            self.socketio.emit('update', {'usn': 'done'}, namespace='/')
        self._save_to_db()

    def _save_to_db(self):
        """Save processed results to the database."""
        print("\nSaving results to database...")
        db = dbhandler.DBHandler()
        files = [f for f in os.listdir(os.path.join(BASE_DIR, "pages"))
                 if f.startswith(self.usn_prefix) and f.endswith(".html")]

        for i, filename in enumerate(files, 1):
            try:
                print(f"Processing file {i}/{len(files)}: {filename}")
                filepath = os.path.join(BASE_DIR, "pages", filename)
                df = Extract(filepath)
                dfdict = df.get_dfs()
                #print(dfdict)
                oth=[]
                for sem, data in dfdict.items():
                    
                    if sem in ("Name", "USN") :
                        oth.append(data)
                        continue

                    if data is None:
                        continue
                        
                    
                    details = df.calculate(data)
                    print(details)
                    table_name = f"X{self.usn_prefix}_SEM_{sem}"
                    
                    try :
                        db.create_table_columns(table_name,get_subject_code(details[0]))
                    except Exception as e:
                        pass

                    inte,exte=dataframe_to_sql(details[0])
                    print(oth)
                    db.push_data_into_table(table_name , inte , exte , oth+details[1])

            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")

        print("Database update completed!")

        

    


if __name__ == "__main__":
    scraper = ThreadManager(
        base_url="https://results.vtu.ac.in/DJcbcs24/index.php",
        usn_prefix="1BI23EC",
        db_table="1BI23EC",
        end_usn=280,
        num_threads=20
    )
    #scraper.run_threads()

    scraper._save_to_db()
