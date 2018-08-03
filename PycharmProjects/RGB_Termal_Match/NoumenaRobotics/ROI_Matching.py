import os
from datetime import datetime
from datetime import timedelta
from libxmp import XMPFiles
import numpy as np
import cv2


class ImageUtils:
    thermalDateTimes = {}

    def __init__(self, path):
        self.root = path[0]
        self.file = path[1]
        self.dateTime = self.extractDateTime(self.file)
        self.closestImage = self.matchThermal()
        (self.minY, self.minX), (self.maxY, self.maxX), self.collage = \
            self.matchImages()

    @classmethod
    def importThermalImages(cls, tif_image_path):
        print("Importing thermal Images . . .")
        for root, subs, files in os.walk(tif_image_path):
            for file in files:
                if not file.endswith('.tiff'):
                    print("{} is not a valid name.".format(file))
                    continue
                cls.thermalDateTimes[(root, file)] = \
                    cls.extractDateTime(file)

    @staticmethod
    def show(*args, terminate=False):
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        chnls = np.concatenate([arg for arg in args], axis=1)
        cv2.imshow('image', chnls)
        cv2.waitKey()
        if terminate:
            cv2.destroyAllWindows()

    def matchThermal(self):
        closest_image = sorted(
            list(self.thermalDateTimes.keys())[:],
            key=lambda x: abs(self.dateTime
                              - self.thermalDateTimes[x])
        )[0]

        time_span = abs(self.dateTime - self.thermalDateTimes[closest_image])

        if time_span < timedelta(seconds=2):
            print("\nRGB image: {}\nThermal image: {}\n\tTime span: {}"
                  .format(self.file, closest_image[1], time_span))
            return closest_image, time_span
        else:
            print("\tNo Match Found!")

    @staticmethod
    def extractDateTime(file):
        sync_time = timedelta(hours=1, minutes=59, seconds=26)
        try:
            image_date_time = datetime.strptime(
                file.split('.')[0][:-8], 'IMG_%y%m%d_%H%M%S_'
            )
            return image_date_time + sync_time

        except ValueError:
            return datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')

        except ValueError:
            print("{}[thermal] is not a date/time format, is it?".format(file))
            return

    def copyXMP(self, target_file):
        xmp_file_original = XMPFiles(file_path=self.file, open_forupdate=True)
        xmp_original = xmp_file_original.get_xmp()

        xmp_crop_file = XMPFiles(file_path=target_file, open_forupdate=True)
        assert xmp_crop_file.can_put_xmp(xmp_original), "Houston, we have a problem!"

        xmp_crop_file.put_xmp(xmp_original)
        xmp_crop_file.close_file()
        print("\tXMP Updated!")

    @staticmethod
    def mixChannels(tif_image_path):
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

    def matchImages(self):
        rgb_img = cv2.imread(os.path.join(self.root, self.file), 1)

        r_image = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2GRAY)
        # r_image = cv2.equalizeHist(r_image)
        blur_rgb = cv2.GaussianBlur(r_image, (7, 7), 5)
        rgb_edges = cv2.Canny(blur_rgb, 60, 80)
        rgb_edges = cv2.dilate(rgb_edges, np.ones((5, 5)), iterations=1)
        rgb_edges = cv2.erode(rgb_edges, np.ones((3, 3)), iterations=1)
        rgb_edges = cv2.dilate(rgb_edges, np.ones((5, 5)), iterations=1)

        template = cv2.imread(os.path.join(self.closestImage[0][0],
                                           self.closestImage[0][1]),
                              -1).astype('uint8')

        template = cv2.resize(template, (1728, 1217), interpolation=cv2.INTER_CUBIC)
        equ_template = cv2.equalizeHist(template)
        blur_template = cv2.GaussianBlur(equ_template, (7, 7), 5)
        template_edges = cv2.Canny(blur_template, 50, 70)
        template_edges = cv2.dilate(template_edges, np.ones((5, 5)), iterations=1)
        template_edges = cv2.erode(template_edges, np.ones((3, 3)), iterations=1)
        template_edges = cv2.dilate(template_edges, np.ones((5, 5)), iterations=1)

        # show(template_edges)
        # show(rgb_edges)
        # cv2.imshow("1", rgb_edges)
        # cv2.imshow("2", template_edges)
        # cv2.waitKey()

        h, w = template_edges.shape

        methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
                   'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
        method = eval(methods[0])
        res = cv2.matchTemplate(rgb_edges, template_edges, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc  # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
        bottom_right = (top_left[0] + w, top_left[1] + h)

        print("Thermal {1} placed @ {0}: {2}"
              .format(self.file, self.closestImage[0][1], top_left))

        # overlap = np.zeros((rgb_edges.shape[0], rgb_edges.shape[1], 3))
        # overlap[:, :, 0] = rgb_edges
        # overlap[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0], 2] = template_edges
        # show(overlap)

        collage = r_image
        collage[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]] = template

        ## Temp . . .
        # cv2.rectangle(collage, top_left, bottom_right, 0, thickness=10)

        return top_left, bottom_right, collage
