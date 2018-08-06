from colmapScripts.read_model import *
from NoumenaRobotics.ROI_Matching import ImageUtils
from multiprocessing import Pool, cpu_count
import cv2


def mi(path):
    return ImageUtils(path)


def main(rgbs_path, thermals_path):
    cameras, images, points3D = \
        read_model(path='/Users/Ardoo/Desktop/COLMAP_Test/Exports/TXT0/',
                   ext=".txt")

    print("num_cameras:", len(cameras))
    print("num_images:", len(images))
    print("num_points3D:", len(points3D))
    print("\n\________(o_O)________/\n")

    ImageUtils.importThermalImages(thermals_path)

    for root, subs, files in os.walk(rgbs_path):
        paths = [(root, file) for file in files if file.endswith('.JPG')]
        print("CPU cores available: %d" % cpu_count())

        with Pool(cpu_count()) as pool:
            print("~~~~ Into the pool ~~~~~~~~~~~~~~~~~~~~~~~~")
            imgLst = pool.map(mi, paths)
            print("And OUT!")

        imgs = {imgUtl.file: imgUtl for imgUtl in imgLst}

    point_cloud = {}
    for item in images.items():
        print('\n----{', item[0], '}-------------------------------------------------------------------------')
        print('File: {}'.format(item[1].name))

        imgData = imgs[item[1].name]
        img = imgData.collage
        print("Loaded and ready.\n\tResolution: {}\tData: {}"
              .format(img.shape, imgData.file))

        for i in range(len(item[1].point3D_ids)):
            pt3D = item[1].point3D_ids[i]
            if pt3D == -1:
                continue

            sparse_pt_pos = item[1].xys[i].astype(int)

            if imgData.maxX > sparse_pt_pos[0] > imgData.minX and \
                    imgData.maxY > sparse_pt_pos[1] > imgData.minY:
                sparse_pt_col = imgData.collage[sparse_pt_pos[0], sparse_pt_pos[1]]

                img = cv2.circle(img, (sparse_pt_pos[1], sparse_pt_pos[0]), 5, 0, 2)

                if pt3D not in list(point_cloud.keys()):
                    point_cloud[pt3D] = [sparse_pt_col, ]
                else:
                    point_cloud[pt3D].append(sparse_pt_col)

        # ImageUtils.show(img)

    with open("points3D.txt", 'w') as f:

        print("\nDrawing Thermal Points . . .")
        for item in point_cloud.items():
            loc = points3D[item[0]].xyz
            color = int(sum(item[1]) / len(item[1]))
            f.write("x{} y{} z{} col{}\n"
                    .format(loc[0], loc[1], loc[2], color))

        print("Drawing Undetected Points . . .\n")
        for p3Did in list(points3D.keys()):
            if p3Did not in list(point_cloud.keys()):
                loc = points3D[p3Did].xyz
                f.write("x{} y{} z{} col_\n"
                        .format(loc[0], loc[1], loc[2]))
                # ax.scatter(loc[0], loc[1], loc[2], s=1, c='g')
    print("Drawing Done.\n")

    # for item in point_cloud.items():
    #     print("\nPoint3D: {}\t\tValues: {} < {}\t[{}]"
    #           .format(item[0], min(item[1]), max(item[1]), item[1]))


if __name__ == '__main__':
    trm_path = "/Users/Ardoo/Desktop/COLMAP_Test/Images/Thermals/"
    rgb_path = "/Users/Ardoo/Desktop/COLMAP_Test/Images/RGB/"

    main(rgb_path, trm_path)
