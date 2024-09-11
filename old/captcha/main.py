from collections import Counter

import cv2 as cv
import numpy as np
import pytesseract


class Captcha:
    def __init__(self, image: cv.imread):
        self.image = image
        self.background = cv.imread('background_image_median.png')
        self.ivtbackground = cv.bitwise_not(self.background)

    def solve_color(self):
        mask = cv.inRange(self.image, np.array([101, 101, 101]), np.array([104, 104, 104]))
        res = cv.bitwise_and(self.image, self.image, mask=mask)
        # inverted = cv.bitwise_not(mask)
        # cv.imwrite(f"inverted.bmp", inverted)
        # cv.imwrite(f"masked.bmp", mask)
        text = [pytesseract.image_to_string(mask) for x in range(3)]
        x = max(Counter(text))[:-1]
        return x

    def solve_invert(self):
        result = cv.bitwise_or(self.image, self.ivtbackground)
        text = [pytesseract.image_to_string(result) for x in range(3)]
        return max(Counter(text))[:-1]
