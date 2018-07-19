import math
import numpy as np
import cv2
import os
from datetime import datetime
from datetime import timedelta
import pickle
from matplotlib import pyplot
from ROI_Matching import *

thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
save_path = "/Users/Ardoo/Desktop/PT_5_Crop/"
tif_path = "/Volumes/NO NAME/PT_5/DCIM/"

thermal_Images_Times = {}
for root, subs, files in os.walk(thermal_path):
    for file in files:
        try:
            thermal_Images_Times[(root, file)] = datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
        except:
            pass

# print(thermal_Images_Times)
sync_time = timedelta(hours=1, minutes=59, seconds=26)

matched_files = {}
for root, subs, files in os.walk(tif_path):
    for sub in subs:
        for _root, _subs, _files in os.walk(os.path.join(root, sub)):
            for file in _files:
                if "GRE" in file:
                    if '.' in _root: continue
                    image_date_time = datetime.strptime(file.split('.')[0][:-8], 'IMG_%y%m%d_%H%M%S_')
                    image_date_time += sync_time
                    print(image_date_time, file)

                    closest_image = sorted(
                        list(thermal_Images_Times.keys())[:],
                        key=lambda x: abs(image_date_time - thermal_Images_Times[x])
                    )[0]

                    time_span = abs(image_date_time - thermal_Images_Times[closest_image])
                    if time_span < timedelta(seconds=5):
                        print(thermal_Images_Times[closest_image], closest_image[1], '\n', time_span)
                        matched_files[(_root, file)] = (closest_image, time_span)
                    else:
                        print("    No Image Found!")

print("{} out of {} thermal images matched with RGB images.".format(len(matched_files),
                                                                    len(thermal_Images_Times.items())))

# pickling_on = open("Emp.pickle", "wb")
# pickle.dump(matched_files, pickling_on)
# pickling_on.close()

# for channel, thermal in matched_files.items():
#     print(thermal[0][1])
#     print(channel[0])
#     for root, subs, files in os.walk(channel[0]):
#         for file in files:
#             if file.endswith(".TIF") and "REG" not in file:
#                 crop = match_images(os.path.join(root, file), os.path.join(thermal[0][0], thermal[0][1]))
#                 file_name = save_path + file[:-4] + "_Cropped.TIF"
#                 print("\t" + file_name)
#                 img = cv2.imread(os.path.join(root, file))
#                 cropped = img[crop[0][1]:crop[1][1], crop[0][0]:crop[1][0]]
#
#                 cv2.imshow("1", cv2.imread((os.path.join(root, file))))
#                 cv2.imshow("3", cropped)
#                 cv2.waitKey(0)
#
#                 cv2.imwrite(file_name, cropped)

for channel, thermal in matched_files.items():
    print(thermal[0][1])
    print(channel[1])
    crop = match_images(os.path.join(channel[0], channel[1]), os.path.join(thermal[0][0], thermal[0][1]))
    for root, subs, files in os.walk(channel[0]):
        for file in files:
            if file.endswith(".TIF") and "REG" not in file:

                if "GRE" in file:
                    offset_correction_x = 0
                    offset_correction_y = 0
                if "RED" in file:
                    offset_correction_x = -7
                    offset_correction_y = 16
                if "NIR" in file:
                    offset_correction_x = -6
                    offset_correction_y = 2

                file_name = save_path + file[:-4] + "_Cropped.TIF"
                print("\t" + file_name)
                img = cv2.imread(os.path.join(root, file))
                # cropped = img[(crop[0][1] + offset_correction_y):(crop[1][1] + offset_correction_y),
                #           (crop[0][0] + offset_correction_x):(crop[1][0] + offset_correction_x)]

                # cropped = img[crop[0][1]:crop[1][1], crop[0][0]:crop[1][0]]

                try:
                    y_min = crop[0][1] + offset_correction_y
                    y_max = crop[1][1] + offset_correction_y
                    x_min = crop[0][0] + offset_correction_x
                    x_max = crop[1][0] + offset_correction_x
                    assert y_min >= 0
                    assert y_max >= 0
                    assert x_min >= 0
                    assert x_max >= 0
                except:
                    y_min = crop[0][1]
                    y_max = crop[1][1]
                    x_min = crop[0][0]
                    x_max = crop[1][0]

                print(y_min, y_max, "<>", x_min, x_max)
                cropped = img[y_min:y_max, x_min:x_max]

                cv2.imwrite(file_name, cropped)