import cv2
import numpy as np
import os

# Path to the directory containing the images
images_path = 'images'

# Get a list of all image files in the directory
image_files = [f for f in os.listdir(images_path) if f.endswith(('png', 'jpg', 'jpeg'))]

# Read all images into a list
images = []
for file in image_files:
    img_path = os.path.join(images_path, file)
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if img is not None:
        images.append(img)

# Stack images along a new dimension
stack_images = np.stack(images, axis=-1)

# Compute the median along the new dimension
median_image = np.median(stack_images, axis=-1)

# Convert the median image to uint8 type
median_image = np.uint8(median_image)

# Save the resulting background image
cv2.imwrite('background_image_median.png', median_image)

print('Background image created and saved as background_image_median.png')
