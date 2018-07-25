import sqlite3
import numpy as np
import core.database as Database


class DatabaseGeneration(Database.COLMAPDatabase):
    def __init__(self, original_database, new_database, *args, **kwargs):
        super().__init__(new_database, *args, **kwargs)
        self.conn_org = sqlite3.connect(original_database)
        self.c_org = self.conn_org.cursor()
        self.conn_new = super()

    def check_key_points(self, image_id):
        kp_row = self.c_org.execute("SELECT * FROM {tb} WHERE image_id = {img}"
                                    .format(tb='keypoints', img=image_id)).fetchone()
        dc_row = self.c_org.execute("SELECT * FROM {tb} WHERE image_id = {img}"
                                    .format(tb='descriptors', img=image_id)).fetchone()

        im_row = self.c_org.execute("SELECT * FROM {tb} WHERE image_id={id}"
                                    .format(tb='images', id=image_id)).fetchone()

        key_pts = np.fromstring(kp_row[3], dtype=np.float32).reshape((kp_row[1], kp_row[2]))
        dscrptrs = np.fromstring(dc_row[3], dtype=np.uint8).reshape((dc_row[1], dc_row[2]))

        # img = cv2.imread(tif_path + 'images/' + im_row[1])
        # cv2.rectangle(img, (im_row[10], im_row[12]), (im_row[11], im_row[13]), (0, 255, 0), 3)

        vc = 0
        ic = 0
        new_key_pts = np.zeros((0, 6), dtype=np.float32)
        new_dscrptrs = np.zeros((0, 128), dtype=np.float32)

        for i in range(len(key_pts)):
            key_pt = key_pts[i]

            key_pt_cord = np.floor(key_pt[0:2])
            if key_pt_cord[0] in range(im_row[10], im_row[11]) and \
                    key_pt_cord[1] in range(im_row[12], im_row[13]):
                vc += 1

                new_dscrptrs = np.append(new_dscrptrs, dscrptrs[i].reshape(1, 128), 0)
                new_key_pts = np.append(new_key_pts, key_pt.reshape(1, 6), 0)
                # cv2.circle(img, (key_pt_cord[0], key_pt_cord[1]), 7, (0, 0, 255), 3)

            else:
                ic += 1
                # cv2.circle(img, (key_pt_cord[0], key_pt_cord[1]), 5, (255, 0, 0), 3)

        print('Image: {},\t\tThermal: {},\t\tValidKeyPoints: {} ({:4.1f} %)'
              .format(im_row[1], im_row[-1], vc, 100 * vc / (vc + ic)))

        self.add_keypoints(image_id, new_key_pts)
        self.add_descriptors(image_id, new_dscrptrs)

        # cv2.imshow("img", img)
        # cv2.waitKey()

        self.conn_new.commit()
        # super().commit()

    def check_matches(self, pair_id):
        pair_data = self.c_org.execute("SELECT * FROM {tb} WHERE {col}={id}"
                                       .format(tb='matches', col='pair_id', id=pair_id)).fetchone()

        image_id1, image_id2 = Database.pair_id_to_image_ids(pair_id)

        image_data1 = self.c_org.execute("SELECT * FROM {tb} WHERE {col}={id}"
                                         .format(tb='images', col='image_id', id=image_id1)).fetchone()
        key_pt_data1 = self.c_org.execute('SELECT * FROM {tb} WHERE image_id = {id}'
                                          .format(tb='keypoints', id=image_id1)).fetchone()
        key_pts1 = Database.blob_to_array(key_pt_data1[3], np.float32, (key_pt_data1[1], key_pt_data1[2]))

        image_data2 = self.c_org.execute("SELECT * FROM {tb} WHERE {col}={id}"
                                         .format(tb='images', col='image_id', id=image_id2)).fetchone()
        key_pt_data2 = self.c_org.execute('SELECT * FROM {tb} WHERE image_id = {id}'
                                          .format(tb='keypoints', id=image_id2)).fetchone()
        key_pts2 = Database.blob_to_array(key_pt_data2[3], np.float32, (key_pt_data2[1], key_pt_data2[2]))

        matched_points_array = Database.blob_to_array(pair_data[3], np.uint32, (pair_data[1], pair_data[2]))

        for key_pt_pair in matched_points_array:
            pt1 = np.floor(key_pts1[key_pt_pair[0]][:2])
            pt2 = np.floor(key_pts2[key_pt_pair[1]][:2])

            if pt1[0] in range(image_data1[10], image_data1[11]) and \
                    pt1[1] in range(image_data1[12], image_data1[13]) and \
                    pt2[0] in range(image_data2[10], image_data2[11]) and \
                    pt2[1] in range(image_data2[12], image_data2[13]):
                print("Found a match!")

        # conn.close()


def main(db_org, db_new):
    import os

    if os.path.exists(db_new):
        print("ERROR: database path already exists -- will not modify it.")
        return

    handler = DatabaseGeneration(db_org, db_new)
    handler.create_tables()
    handler.check_key_points(4)


if __name__ == "__main__":
    save_path = "/Users/Ardoo/Desktop/PT_5_Crop_Test3/"
    thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
    tif_path = "/Users/Ardoo/Desktop/COLMAP_Test/"
    db = '/Users/Ardoo/Desktop/COLMAP_Test/database2.db'
    db_n = '/Users/Ardoo/Desktop/COLMAP_Test/database_artificial.db'

    main(db, db_n)

    # check_matches(2147483649, db)
