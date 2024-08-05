import time
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from captcha import *

# branch, year = map(str, input("Enter branch and year").split())
# usn_last = int(input("Enter the last USN of the branch"))

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
driver = webdriver.Chrome(service=Service())


def handle_alert():
    try:
        alert = driver.switch_to.alert
        if alert.text == "University Seat Number is not available or Invalid..!":
            print("No results for : " + usn + "\n")
            alert.accept()

        elif alert.text == "Invalid captcha code !!!":
            print("Invalid CAPTCHA Detected for USN : " + usn + "\n")
            alert.accept()
            fill_form(usn)
    except:
        fill_form(usn)


def fill_form(usn):
    print(usn)
    try:
        driver.get("https://results.vtu.ac.in/DJcbcs24/index.php")

        driver.implicitly_wait(25)
        usnbox = driver.find_element("name", "lns")
        cap = driver.find_element("name", "captchacode")
        usnbox.send_keys(usn)
        capt = driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")
        image = cv.imread("current.png")
        text = Captcha(image).solve_color()
        print(text)

    except selenium.common.exceptions.UnexpectedAlertPresentException as e:
        handle_alert()

    try:
        cap.send_keys(text)

        try:
            driver.find_element('id', "submit").click()
        except selenium.common.exceptions.NoSuchElementException:
            pass

        driver.implicitly_wait(25)
        with open("pages/" + str(usn) + ".html", "w", encoding="utf8") as file:
            file.write(driver.page_source)


    except:
        handle_alert()


l = [54, 55]
for i in range(1, 57):
    usn = f"1BI23CD{i:03d}"

    fill_form(usn)
