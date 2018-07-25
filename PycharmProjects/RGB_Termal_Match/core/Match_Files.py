from core.ROI_Matching import *
import sqlite3
import shutil


def crop_and_save(images_path, thermal_images_path, saving_path, save_as_mask=False, save_as_crop=True, db=None):
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
        crop = match_images(os.path.join(channel[0], channel[1]), os.path.join(thermal[0][0], thermal[0][1]))
        for root, subs, files in os.walk(channel[0]):
            for file in files:
                if file.endswith(".JPG") and file == channel[1]:
                    img = cv2.imread(os.path.join(root, file), -1)

                    y_min = crop[0][1]
                    y_max = crop[1][1]
                    x_min = crop[0][0]
                    x_max = crop[1][0]

                    if save_as_crop:
                        cropped = img[y_min:y_max, x_min:x_max]
                        file_name = saving_path + file[:-4] + "_Cropped.TIF"
                        print("\t" + file_name)
                        cv2.imwrite(file_name, cropped)
                        copy_xmp(os.path.join(root, file), file_name)

                    if save_as_mask:
                        mask = np.zeros(img.shape)
                        mask[y_min: y_max, x_min: x_max] = 255
                        file_name = saving_path + 'Masks/' + file[:-4] + "_Mask.png"
                        print("\t" + file_name)
                        cv2.imwrite(file_name, mask)

                    if db:
                        print("\t\tWriting to database.")
                        shutil.copyfile(
                            os.path.join(thermal[0][0], thermal[0][1]),
                            root + '/thermals/' + thermal[0][1])
                        c.execute(
                            '''UPDATE images 
                            SET (crop_y_min, crop_y_max, crop_x_min, crop_x_max) = ({0}, {1}, {2}, {3}) 
                            WHERE name = ("{4}")'''
                            .format(y_min, y_max, x_min, x_max, channel[1]))
                        c.execute('UPDATE images SET thermal_image = "{0}" WHERE name = ("{1}")'
                                  .format(thermal[0][1], channel[1]))

                        print("\t\t\t\tSAVED TO DATABASE.\n")

    if conn:
        conn.commit()
        conn.close()


if __name__ == "__main__":
    save_path = "/Users/Ardoo/Desktop/PT_5_Crop_Test3/"
    thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
    tif_path = "/Users/Ardoo/Desktop/COLMAP_Test"

    crop_and_save(tif_path, thermal_path, save_path,
                  save_as_crop=False,
                  save_as_mask=False,
                  db='/Users/Ardoo/Desktop/COLMAP_Test/database.db')
