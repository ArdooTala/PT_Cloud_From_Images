from ROI_Matching import *
from Match_by_Time import *
from libxmp import XMPFiles, consts

save_path = "/Users/Ardoo/Desktop/PT_5_Crop/"
thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
tif_path = "/Volumes/NO NAME/PT_5/DCIM/"

matched_files = match_by_time(thermal_path, tif_path)

for channel, thermal in matched_files.items():
    print(thermal[0][1])
    print(channel[1])
    crop = match_images(os.path.join(channel[0], channel[1]), os.path.join(thermal[0][0], thermal[0][1]))
    for root, subs, files in os.walk(channel[0]):
        for file in files:
            if file.endswith(".TIF") and "REG" not in file:

                offset_correction_x = 0
                offset_correction_y = 0

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

                cropped = img[y_min:y_max, x_min:x_max]

                cv2.imwrite(file_name, cropped)

                xmp_file_original = XMPFiles(file_path=os.path.join(root, file), open_forupdate=True)
                xmp_original = xmp_file_original.get_xmp()

                xmp_crop_file = XMPFiles(file_path=file_name, open_forupdate=True)
                xmp_crop = xmp_crop_file.get_xmp()
                assert xmp_crop_file.can_put_xmp(xmp_original), "Houston, we have a problem!"

                xmp_crop_file.put_xmp(xmp_original)
                xmp_crop_file.close_file()
                print("\tXMP Updated!")