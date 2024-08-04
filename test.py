import cv2 as cv
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

tex = pytesseract.image_to_string(cv.imread("data/solved.png"))

print(tex)
