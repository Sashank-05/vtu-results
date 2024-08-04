import os

import numpy as np
from selenium import types
from selenium import webdriver
from selenium.common import UnexpectedAlertPresentException
from selenium.webdriver.chrome import service
import time
import cv2 as cv
import pytesseract

# branch, year = map(str, input("Enter branch and year").split())
# usn_last = int(input("Enter the last USN of the branch"))

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'


def fill_form(usn):
    driver = webdriver.Chrome(service=webdriver.ChromeService())
    print(usn)
    driver.get("https://results.vtu.ac.in/DJcbcs24/index.php")
    driver.implicitly_wait(25)
    usnbox = driver.find_element("name", "lns")
    cap = driver.find_element("name", "captchacode")
    usnbox.send_keys(usn)

    capt = driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")
    image = cv.imread("current.png")
    mask = cv.inRange(image, np.array([102, 102, 102]), np.array([103, 103, 103]))

    res = cv.bitwise_and(image, image, mask=mask)
    inverted = cv.bitwise_not(mask)

    cv.imwrite(f"inverted.bmp", inverted)
    cv.imwrite(f"masked.bmp", mask)
    text = pytesseract.image_to_string(mask)
    print(text)

    try:
        cap.send_keys(text)
        # driver.find_element('id', "submit").click()

    except:
        # Catches all types of errors like Invalid Captcha and Invalid USN
        alert = driver.switch_to.alert
        if alert.text == "University Seat Number is not available or Invalid..!":
            print("No results for : " + usn + "\n")
            alert.accept()

        elif alert.text == "Invalid captcha code !!!":
            print("Invalid CAPTCHA Detected for USN : " + usn + "\n")
            alert.accept()
            fill_form(usn)

    try:
        with open("pages/" + str(usn) + ".html", "w", encoding="utf8") as file:
            file.write(driver.page_source)
    except:
        # Catches all types of errors like Invalid Captcha and Invalid USN
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
            pass


for i in range(1, 54):
    usn = f"1BI23CD{i:03d}"

    fill_form(usn)
time.sleep(50)
