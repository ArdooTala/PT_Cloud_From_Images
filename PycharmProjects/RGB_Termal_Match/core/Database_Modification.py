import sqlite3
import numpy as np
import core.ROI_Matching as ROI


save_path = "/Users/Ardoo/Desktop/PT_5_Crop_Test2/"
thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
tif_path = "/Volumes/NO NAME/PT_5/DCIM/"

matched_files = ROI.match_by_time(thermal_path, tif_path)


db = '/Users/Ardoo/Desktop/COLMAP_Test/database.db'

# Connect to database.
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT * FROM {tb}".format(tb='keypoints',))

rows = c.fetchall()
for row in rows:
    image_row = c.execute("SELECT * FROM {tb} WHERE {col}={id}"
        .format(tb='images', col='image_id', id=row[0]))

    key_pts = np.fromstring(row[3], dtype=np.float32).reshape((row[1], row[2]))

    for key_pt in key_pts[:10]:
        key_pt_cord = np.floor(key_pt[0:2])
        if key_pt_cord[0] in range(100, 500) and key_pt_cord[1] in range(20, 1000):
            print(key_pt_cord)

    print("ID: {}\t\tImageName: {}\t\tKeyPoint#: {}\t\tThermalKeyPoints:{}"
          .format(row[0], image_row.fetchone()[1], len(key_pts), 12))