import cv2 as cv
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

img1 = cv.imread('../background_image_median.png')
img2 = cv.imread('../images/2.jpg')

img1 = cv.resize(img1, (img2.shape[1], img2.shape[0]))
img1 = cv.bitwise_not(img1)
# cv.imshow('img1', img1)
result = cv.bitwise_or(img1, img2)
# result = cv.bitwise_or(img1,result)
# result = cv.bitwise_not(result)

cv.imwrite('result_image.png', result)
# cv.imshow('Result Image', result)
cv.waitKey(0)
cv.destroyAllWindows()

print(pytesseract.image_to_string(result))
