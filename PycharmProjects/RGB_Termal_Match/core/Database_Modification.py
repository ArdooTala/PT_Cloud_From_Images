import sqlite3
import numpy as np
import core.ROI_Matching as ROI
import cv2


save_path = "/Users/Ardoo/Desktop/PT_5_Crop_Test3/"
thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
tif_path = "/Users/Ardoo/Desktop/COLMAP_Test/"

matched_files = ROI.match_by_time(thermal_path, tif_path)

db = '/Users/Ardoo/Desktop/COLMAP_Test/database.db'

# Connect to database.
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT * FROM {tb}".format(tb='keypoints',))

rows = c.fetchall()
for row in rows:
    image_row = c.execute("SELECT * FROM {tb} WHERE {col}={id}"
        .format(tb='images', col='image_id', id=row[0])).fetchone()

    key_pts = np.fromstring(row[3], dtype=np.float32).reshape((row[1], row[2]))

    # img = cv2.imread(tif_path + 'images/' + image_row[1])
    # cv2.rectangle(img, (image_row[10], image_row[12]), (image_row[11], image_row[13]), (0, 255, 0), 3)

    vc = 0
    ic = 0
    for key_pt in key_pts:
        key_pt_cord = np.floor(key_pt[0:2])
        if key_pt_cord[0] in range(image_row[10], image_row[11]) and \
                key_pt_cord[1] in range(image_row[12], image_row[13]):
            # print("BINGO!\t\t>>> ", key_pt_cord)
            vc += 1

            # cv2.circle(img, (key_pt_cord[0], key_pt_cord[1]), 5, (0, 0, 255), -1)

        else:
            ic += 1

            # cv2.circle(img, (key_pt_cord[0], key_pt_cord[1]), 5, (255, 0, 0), -1)

    print('Image: {},\t\tThermal: {},\t\tValidKeyPoints: {:4.1f} %'.format(image_row[1], image_row[-1], 100 * vc / (vc + ic)))
    # cv2.imshow("img", img)
    # cv2.waitKey()