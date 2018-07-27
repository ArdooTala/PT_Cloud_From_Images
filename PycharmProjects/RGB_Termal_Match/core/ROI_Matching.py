import os
from datetime import datetime
from datetime import timedelta
from libxmp import XMPFiles
import numpy as np
from scipy import ndimage
import cv2


def mix_chanels(tif_image_path):
    for root, subs, files in os.walk(tif_image_path):
        for sub in subs:

            for _root, _subs, _files in os.walk(os.path.join(root, sub)):
                for file in _files:
                    if "GRE" in file:
                        gre = cv2.imread(os.path.join(_root, file), 0)
                        gre = gre.reshape(gre.shape[0], gre.shape[1], 1)
                        print(gre.shape)

                    if "NIR" in file:
                        nir = cv2.imread(os.path.join(_root, file), 0)
                        nir = nir.reshape(nir.shape[0], nir.shape[1], 1)

                    if "RED" in file:
                        red = cv2.imread(os.path.join(_root, file), 0)
                        red = red.reshape(red.shape[0], red.shape[1], 1)

                # if not gre == None and not nir == None and not red == None:
                mix = np.append(np.append(red, nir, 2), gre, 2)
                cv2.imshow("mix", mix)
                cv2.waitKey()


def visualize_thermal_image(path):
    t_image = ndimage.imread(path, flatten=True)
    v_image = ((t_image - t_image.min()) * 256) / max(1, (t_image.max() - t_image.min()))
    return v_image.astype(np.uint8)


def match_images(rgb_path, thermal_image_path):
    rgb_image = cv2.imread(rgb_path, 0)
    # rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2GRAY)
    equ_rgb = cv2.equalizeHist(rgb_image)
    blur_rgb = cv2.GaussianBlur(equ_rgb, (11, 11), 0)
    rgb_edges = cv2.Canny(blur_rgb, 100, 100)
    # rgb_edges = cv2.blur(rgb_edges, (21, 21))

    template = cv2.imread(thermal_image_path, -1).astype('uint8')
    template = cv2.resize(template, (1728, 1296), interpolation=cv2.INTER_CUBIC)
    equ_template = cv2.equalizeHist(template)
    blur_template = cv2.GaussianBlur(equ_template, (3, 3), 0)
    template_edges = cv2.Canny(blur_template, 50, 80)
    # template_edges = cv2.blur(template_edges, (7, 7))

    # orb = cv2.ORB_create(nfeatures=1500)
    # kp1, ds1 = orb.detectAndCompute(blur_template, None)
    # kp2, ds2 = orb.detectAndCompute(blur_rgb, None)
    # bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    # matches = bf.match(ds1, ds2)
    # matches = sorted(matches, key=lambda x: x.distance)
    # timg2 = np.zeros(rgb_edges.shape)
    # timg2 = cv2.drawMatches(blur_template, kp1, blur_rgb, kp2, matches[:50], timg2, flags=2)
    # cv2.imshow("img2", timg2)
    # cv2.waitKey()

    # cv2.imshow('dst_rt', template_edges)
    # cv2.imshow('ds_rt', rgb_edges)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

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

    return top_left, bottom_right, equ_template  # cropped_image


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
    thermal_path = "/Volumes/PABLITO/THERMAL"
    tif_path = "/Volumes/NO NAME/PT_5/DCIM/"
    # for root, sub, files in os.walk(thermal_path):
    #     for file in files:
    #         pic = visualize_thermal_image(os.path.join(root, file))
    #         cv2.imwrite('/Users/Ardoo/Desktop/TT/'+file[:-5]+'.PNG', pic)

    mix_chanels(tif_path)