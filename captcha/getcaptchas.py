import cv2 as cv
import selenium
from selenium import webdriver

driver = webdriver.Chrome(service=webdriver.ChromeService())

for i in range(0, 50):
    driver.get("https://results.vtu.ac.in/DJcbcs24/index.php")
    driver.implicitly_wait(25)

    cap = driver.find_element("name", "captchacode")
    capt = driver.find_element('xpath', '//img[@alt="CAPTCHA code"]').screenshot("current.png")
    image = cv.imread("current.png")
    cv.imwrite(f"{i}.jpg", image)

