import numpy as np
from matplotlib import pyplot as plt
from scipy import ndimage
import cv2


def visualize_thermal_image(path):
    t_image = ndimage.imread(path, flatten=True)
    v_image = ((t_image - t_image.min()) * 512) / max(1, (t_image.max() - t_image.min()))
    return v_image.astype(np.uint8)


if __name__ == "__main__":
    pic = visualize_thermal_image("Images/Thermal_Images/20180621_113834.tiff")
    cv2.imshow("PIC", pic)
    cv2.waitKey(0)
    cv2.imwrite("Thermal.png", pic)