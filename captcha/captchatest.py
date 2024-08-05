import cv2 as cv
import numpy as np

img1 = cv.imread('background.png')
img2 = cv.imread('images/2.jpg')

img1 = cv.resize(img1, (img2.shape[1], img2.shape[0]))

diff = cv.absdiff(img1, img2)

lower_bound = np.array([50, 50, 50])
upper_bound = np.array([255, 255, 255])
mask = cv.inRange(diff, lower_bound, upper_bound)

result = cv.bitwise_and(img2, img2, mask=mask)

cv.imwrite('result_image.png', result)
cv.imshow('Result Image', result)
cv.waitKey(0)
cv.destroyAllWindows()
