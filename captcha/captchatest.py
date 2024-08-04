import os
import time
import cv2 as cv
import numpy as np
import pytesseract
from PIL import Image

# cv.imshow("Original", image)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

for i in os.listdir("data"):
    print(i)
    image = cv.imread("data/" + i)
    mask = cv.inRange(image, np.array([102, 102, 102]), np.array([103, 103, 103]))

    res = cv.bitwise_and(image, image, mask=mask)
    inverted = cv.bitwise_not(mask)

    cv.imwrite(f"processing/{i}inverted.bmp", inverted)
    cv.imwrite(f"processing/{i}masked.bmp", mask)
    tex = pytesseract.image_to_string(mask)

    print(tex)
