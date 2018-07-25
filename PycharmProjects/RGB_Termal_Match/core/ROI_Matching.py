from core.Visualize_Thermal_Image import *
import os
from datetime import datetime
from datetime import timedelta
from libxmp import XMPFiles


def match_images(rgb_path, thermal_image_path):
    rgb_image = cv2.imread(rgb_path, 0)
    # rgb_image = cv2.resize(rgb_image, (1280, 960), interpolation=cv2.INTER_LINEAR)
    equ_rgb = cv2.equalizeHist(rgb_image)
    blur_rgb = cv2.blur(equ_rgb, (5, 5))
    rgb_edges = cv2.Canny(blur_rgb, 50, 100)
    rgb_edges = cv2.blur(rgb_edges, (3, 3))

    template = visualize_thermal_image(thermal_image_path)
    template = cv2.resize(template, (1728, 1296), interpolation=cv2.INTER_CUBIC)
    equ_template = cv2.equalizeHist(template)
    blur_template = cv2.blur(equ_template, (3, 3))
    template_edges = cv2.Canny(blur_template, 40, 70)
    template_edges = cv2.blur(template_edges, (3, 3))

    # cv2.imshow("1", rgb_edges)
    # cv2.imshow("2", template_edges)
    # cv2.waitKey()

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

    cv2.rectangle(rgb_image, top_left, bottom_right, 0, 2)

    return top_left, bottom_right, rgb_image  # cropped_image


def match_by_time(thermal_image_path, tif_image_path):
    thermal_images_times = {}
    for root, subs, files in os.walk(thermal_image_path):
        for file in files:
            try:
                thermal_images_times[(root, file)] = datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
            except:
                pass

    # print(thermal_images_times)
    sync_time = timedelta(hours=1, minutes=59, seconds=26)

    matched_files = {}
    counter = 0
    for root, subs, files in os.walk(tif_image_path):
        for sub in subs:
            for _root, _subs, _files in os.walk(os.path.join(root, sub)):
                for file in _files:
                    if "JPG" in file:
                        if '.' in _root:
                            continue
                        image_date_time = datetime.strptime(file.split('.')[0][:-8], 'IMG_%y%m%d_%H%M%S_')
                        image_date_time += sync_time
                        print(image_date_time, file)

                        closest_image = sorted(
                            list(thermal_images_times.keys())[:],
                            key=lambda x: abs(image_date_time - thermal_images_times[x])
                        )[0]

                        time_span = abs(image_date_time - thermal_images_times[closest_image])
                        if time_span < timedelta(seconds=5):
                            print(thermal_images_times[closest_image], closest_image[1], '\n', time_span)
                            counter += 1
                            matched_files[(_root, file)] = (closest_image, time_span)
                        else:
                            print("    No Image Found!")

    print("{} out of {} thermal images matched with RGB images.".format(len(matched_files),
                                                                        len(thermal_images_times.items())))
    print("%d images saved to dict." % counter)

    return matched_files


def copy_xmp(original_file, target_file):
    xmp_file_original = XMPFiles(file_path=original_file, open_forupdate=True)
    xmp_original = xmp_file_original.get_xmp()

    xmp_crop_file = XMPFiles(file_path=target_file, open_forupdate=True)
    assert xmp_crop_file.can_put_xmp(xmp_original), "Houston, we have a problem!"

    xmp_crop_file.put_xmp(xmp_original)
    xmp_crop_file.close_file()
    print("\tXMP Updated!")


if __name__ == "__main__":
    thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
    tif_path = "/Volumes/NO NAME/PT_5/DCIM/"
    print(match_by_time(thermal_path, tif_path))

    ###############################################################

    pic = match_images("/Volumes/NO NAME/PT_5/DCIM/0000/IMG_180621_093908_0000_GRE.TIF",
                       "Images/Thermal_Images/20180621_113834.tiff")
    # cv2.imshow("Result", pic)
    # cv2.waitKey()
    cv2.imwrite("ROI_Image.PNG", pic)
    # plt.imshow(pic, cmap='gray')
    # plt.show()
