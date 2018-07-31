import os
from datetime import datetime
from datetime import timedelta
from libxmp import XMPFiles
import numpy as np
from scipy import ndimage
import cv2
import sqlite3


def show(*args):
    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    chnls = np.concatenate([arg for arg in args], axis=1)
    cv2.imshow('image', chnls)
    cv2.waitKey()
    # cv2.destroyAllWindows()


def mix_channels(tif_image_path):
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
    rgb_img = cv2.imread(rgb_path, 1)
    # r_image = rgb_img[:, :, 2]

    # r_image = cv2.equalizeHist(r_image)
    r_image = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2GRAY)
    blur_rgb = cv2.GaussianBlur(r_image, (7, 7), 5)
    rgb_edges = cv2.Canny(blur_rgb, 60, 80)
    rgb_edges = cv2.dilate(rgb_edges, np.ones((5, 5)), iterations=1)
    rgb_edges = cv2.erode(rgb_edges, np.ones((3, 3)), iterations=1)
    rgb_edges = cv2.dilate(rgb_edges, np.ones((5, 5)), iterations=1)
    # rgb_edges = cv2.blur(rgb_edges, (7, 7))

    # show(rgb_edges)

    template = cv2.imread(thermal_image_path, -1).astype('uint8')
    template = cv2.resize(template, (1728, 1217), interpolation=cv2.INTER_CUBIC)
    template = cv2.equalizeHist(template)
    blur_template = cv2.GaussianBlur(template, (7, 7), 5)
    template_edges = cv2.Canny(blur_template, 50, 70)
    template_edges = cv2.dilate(template_edges, np.ones((5, 5)), iterations=1)
    template_edges = cv2.erode(template_edges, np.ones((3, 3)), iterations=1)
    template_edges = cv2.dilate(template_edges, np.ones((5, 5)), iterations=1)
    # template_edges = cv2.blur(template_edges, (5, 5))

    # show(template_edges)

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

    overlap = np.zeros((rgb_edges.shape[0], rgb_edges.shape[1], 3))
    overlap[:, :, 0] = rgb_edges
    overlap[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0], 2] = template_edges

    # show(overlap)

    return top_left, bottom_right, template  # cropped_image


def match_by_time(thermal_image_path, tif_image_path):
    thermal_images_times = {}
    for root, subs, files in os.walk(thermal_image_path):
        for file in files:
            try:
                thermal_images_times[(root, file)] = \
                    datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
            except:
                pass

    sync_time = timedelta(hours=1, minutes=59, seconds=26)

    rgb_date_times = {}
    for root, subs, files in os.walk(tif_image_path):
        for sub in subs:
            for _root, _subs, _files in os.walk(os.path.join(root, sub)):
                if '.' in _root:
                    continue
                for file in _files:
                    if "JPG" in file:
                        try:
                            image_date_time = datetime.strptime(
                                file.split('.')[0][:-8], 'IMG_%y%m%d_%H%M%S_'
                            )
                            image_date_time += sync_time

                            rgb_date_times[(_root, file)] = image_date_time
                        except:
                            pass

    matched_files = {}
    counter = 0

    for root, subs, files in os.walk(thermal_image_path):
        for file in files:
            try:
                thermal_images_time = datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
            except:
                print("Invalid Name!")
                continue

            closest_image = sorted(
                list(rgb_date_times.keys())[:],
                key=lambda x: abs(thermal_images_time - rgb_date_times[x]))[0]

            time_span = abs(thermal_images_time - rgb_date_times[closest_image])
            print("_____________________________")
            if time_span < timedelta(seconds=1):
                print(file, "\t", closest_image[1], '\t', time_span)
                counter += 1
                matched_files[closest_image] = ((root, file), time_span)
            else:
                print("    No Image Found!")

    """
    for root, subs, files in os.walk(tif_image_path):
        for sub in subs:
            for _root, _subs, _files in os.walk(os.path.join(root, sub)):
                if '.' in _root:
                    continue
                for file in _files:
                    if "JPG" in file:
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
    """
    print("{} out of {} thermal images matched with RGB images.".format(len(matched_files),
                                                                        len(rgb_date_times.items())))
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


def main(images_path, thermal_images_path, saving_path,
         save_as_mask=False, save_as_crop=True, db=None):

    matched_files = match_by_time(thermal_images_path, images_path)

    if db:
        print("Initializing database.")
        conn = sqlite3.connect(db)
        c = conn.cursor()

        try:
            c.execute("ALTER TABLE images ADD COLUMN 'crop_x_min' INTEGER")
        except:
            pass
        try:
            c.execute("ALTER TABLE images ADD COLUMN 'crop_x_max' INTEGER")
        except:
            pass
        try:
            c.execute("ALTER TABLE images ADD COLUMN 'crop_y_min' INTEGER")
        except:
            pass
        try:
            c.execute("ALTER TABLE images ADD COLUMN 'crop_y_max' INTEGER")
        except:
            pass
        try:
            c.execute("ALTER TABLE images ADD COLUMN 'thermal_image' TEXT")
        except:
            pass

    for channel, thermal in matched_files.items():
        print(thermal[0][1])
        print(channel[1])
        crop = match_images(
            os.path.join(channel[0], channel[1]),
            os.path.join(thermal[0][0], thermal[0][1])
        )
        for root, subs, files in os.walk(channel[0]):
            for file in files:
                if file.endswith(".JPG") and file == channel[1]:
                    img = cv2.imread(os.path.join(root, file), 0)

                    y_min = crop[0][1]
                    y_max = crop[1][1]
                    x_min = crop[0][0]
                    x_max = crop[1][0]

                    if save_as_crop:
                        img = cv2.imread(os.path.join(root, file), -1)
                        cropped = img[y_min:y_max, x_min:x_max]
                        file_name = saving_path + file[:-4] + "_Cropped.TIF"
                        print("\t" + file_name)
                        cv2.imwrite(file_name, cropped)
                        copy_xmp(os.path.join(root, file), file_name)

                    if save_as_mask:
                        mask = np.zeros(img.shape)
                        mask[y_min: y_max, x_min: x_max] = 255
                        file_name = saving_path + 'Masks/' \
                                    + file[:-4] + "_Mask.png"
                        print("\t" + file_name)
                        cv2.imwrite(file_name, mask)

                    if db:
                        img[y_min: y_max, x_min: x_max] = crop[2]
                        cv2.imwrite(os.path.split(root)[0] + '/_thermals/' + \
                                    thermal[0][1][:-5] + '.PNG', img)
                        # shutil.copyfile(
                        #     os.path.join(thermal[0][0], thermal[0][1]),
                        #     os.path.split(root)[0] + '/thermals/' + thermal[0][1])
                        c.execute(
                            '''UPDATE images 
                            SET (crop_y_min, crop_y_max, 
                                 crop_x_min, crop_x_max) = ({0}, {1}, {2}, {3}) 
                            WHERE name = ("{4}")'''
                                .format(y_min, y_max, x_min, x_max, channel[1]))
                        c.execute('UPDATE images SET thermal_image = "{0}" WHERE name = ("{1}")'
                                  .format(thermal[0][1][:-5] + '.PNG', channel[1]))

                        conn.commit()
                        print("\t\tSAVED TO DATABASE.\n")

    if conn:
        conn.commit()
        conn.close()


# if __name__ == "__main__":
#     thermal_path = "/Volumes/PABLITO/THERMAL"
#     tif_path = "/Volumes/NO NAME/PT_5/DCIM/"
#     rgb = "/Users/Ardoo/Desktop/COLMAP_Test/Images/IMG_180621_095004_0000_RGB.JPG"
#     thermal = "/Users/Ardoo/Desktop/COLMAP_Test/thermals/20180621_114931.PNG"
#     match_images(rgb, thermal)

if __name__ == "__main__":
    save_path = "/Users/Ardoo/Desktop/PT_5_Crop_Test3/"
    thermal_path = "/Volumes/PABLITO/THERMAL/"
    tif_path = "/Users/Ardoo/Desktop/COLMAP_Test"

    main(tif_path, thermal_path, save_path,
         save_as_crop=False,
         save_as_mask=False,
         db='/Users/Ardoo/Desktop/COLMAP_Test/database.db')
