from core.ROI_Matching import *


def crop_and_save(tif_path, thermal_path, save_path, save_as_mask=False, save_as_crop=True):
    matched_files = match_by_time(thermal_path, tif_path)

    for channel, thermal in matched_files.items():
        print(thermal[0][1])
        print(channel[1])
        crop = match_images(os.path.join(channel[0], channel[1]), os.path.join(thermal[0][0], thermal[0][1]))
        for root, subs, files in os.walk(channel[0]):
            for file in files:
                if file.endswith(".TIF") and "REG" not in file:
                    img = cv2.imread(os.path.join(root, file), -1)

                    y_min = crop[0][1]
                    y_max = crop[1][1]
                    x_min = crop[0][0]
                    x_max = crop[1][0]

                    if save_as_crop:
                        cropped = img[y_min:y_max, x_min:x_max]
                        file_name = save_path + file[:-4] + "_Cropped.TIF"
                        print("\t" + file_name)
                        cv2.imwrite(file_name, cropped)
                        copy_xmp(os.path.join(root, file), file_name)

                    if save_as_mask:
                        mask = np.zeros(img.shape)
                        mask[y_min: y_max, x_min: x_max] = 255
                        file_name = save_path + 'Masks/' + file[:-4] + "_Mask.png"
                        print("\t" + file_name)
                        cv2.imwrite(file_name, mask)


if __name__ == "__main__":
    save_path = "/Users/Ardoo/Desktop/PT_5_Crop_Test2/"
    thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
    tif_path = "/Volumes/NO NAME/PT_5/DCIM/"

    crop_and_save(tif_path, thermal_path, save_path, save_as_crop=False, save_as_mask=True)
