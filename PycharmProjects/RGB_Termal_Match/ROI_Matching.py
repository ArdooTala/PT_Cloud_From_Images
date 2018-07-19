import cv2
import numpy as np
from Visualize_Thermal_Image import *


def match_images(rgb_path, thermal_path):
    rgb_image = cv2.imread(rgb_path, 0)
    equ_rgb = cv2.equalizeHist(rgb_image)
    blur_rgb = cv2.blur(equ_rgb, (3, 3))
    rgb_edges = cv2.Canny(blur_rgb, 140, 200)  # cv2.Canny(blur_rgb, 50, 100)cv2.Sobel(blur_rgb, cv2.CV_8U, 0, 1, ksize=5)
    rgb_edges = cv2.blur(rgb_edges, (9, 9))

    template = visualize_thermal_image(thermal_path)
    template = cv2.resize(template, (480, 360), interpolation=cv2.INTER_CUBIC)
    equ_template = cv2.equalizeHist(template)
    blur_template = cv2.blur(equ_template, (1, 1))
    template_edges = cv2.Canny(blur_template, 100, 200)  # cv2.Sobel(blur_template, cv2.CV_8U, 0, 1, ksize=5)cv2.Canny(blur_template, 50, 100)
    template_edges = cv2.blur(template_edges, (9, 9))

    h, w = template.shape

    # All the 6 methods for comparison in a list
    methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
               'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']

    method = eval(methods[0])
    res = cv2.matchTemplate(rgb_edges, template_edges, method)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    # cv2.imshow("J", rgb_edges)
    # cv2.imshow("JJ", template_edges)
    # cv2.waitKey()

    cv2.rectangle(rgb_image, top_left, bottom_right, 0, 2)

    # cropped_image = rgb_image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
    # print(cropped_image.shape)
    return top_left, bottom_right, rgb_image  # cropped_image


if __name__ == "__main__":
    pic = match_images("/Volumes/NO NAME/PT_5/DCIM/0000/IMG_180621_093908_0000_GRE.TIF",
                       "Images/Thermal_Images/20180621_113834.tiff")
    # cv2.imshow("Result", pic)
    # cv2.waitKey()
    cv2.imwrite("ROI_Image.PNG", pic)
    plt.imshow(pic, cmap='gray')
    plt.show()