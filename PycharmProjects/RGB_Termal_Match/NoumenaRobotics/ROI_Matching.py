import os
from datetime import datetime
from datetime import timedelta
# from libxmp import XMPFiles
import imutils as imutils
import numpy as np
import cv2


class ImageUtils:
    thermalDateTimes = {}
    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(15, 15))

    def __init__(self, path):
        print(">>> INITIATING CLASS: %s" % path[1])
        print("============================================")
        self.root = path[0]
        self.file = path[1]
        self.dateTime = self.extractDateTime(self.file)
        print("\t\tDate/Time extracted . . .")
        self.closestImage = self.matchThermal()
        if self.closestImage:
            (self.minY, self.minX), (self.maxY, self.maxX), self.collage = \
                self.matchImages()
            print("\t\tThermal Matched.")
        else:
            # self.collage = None
            print("\t\tThermal NOT Matched.")

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

    # def copyXMP(self, target_file):
    #     xmp_file_original = XMPFiles(file_path=self.file, open_forupdate=True)
    #     xmp_original = xmp_file_original.get_xmp()
    #
    #     xmp_crop_file = XMPFiles(file_path=target_file, open_forupdate=True)
    #     assert xmp_crop_file.can_put_xmp(xmp_original), "Houston, we have a problem!"
    #
    #     xmp_crop_file.put_xmp(xmp_original)
    #     xmp_crop_file.close_file()
    #     print("\tXMP Updated!")

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
        #### RGB pre-processing
        rgb_image = cv2.imread(os.path.join(self.root, self.file), 0)
        rgb_image_main = imutils.rotate_bound(rgb_image, 180)
        offset_0 = int(rgb_image_main.shape[0] / 5)
        offset_1 = int(rgb_image_main.shape[1] / 5)
        rgb_image = rgb_image_main[offset_0:rgb_image_main.shape[0] - offset_0,
                    offset_1:rgb_image_main.shape[1] - offset_1,
                    :]
        # rgb_image = self.__class__.clahe.apply(rgb_image)
        blur_rgb = cv2.GaussianBlur(rgb_image, (11, 11), 10)
        # rgb_edges = cv2.Canny(blur_rgb, 90, 100)
        bins = np.linspace(0, 255, num=3)
        inds = np.digitize(blur_rgb, bins).astype(np.float64) / 3
        inds1 = cv2.Canny(
            (inds[:, :, 0] * 255).astype(np.uint8),
            190, 210)
        inds2 = cv2.Canny(
            (inds[:, :, 1] * 255).astype(np.uint8),
            190, 210)
        inds3 = cv2.Canny(
            (inds[:, :, 2] * 255).astype(np.uint8),
            190, 210)
        rgb_edges = cv2.bitwise_or(inds1, inds2, inds3)

        # rgb_edges = cv2.dilate(rgb_edges, np.ones((3, 3)), iterations=3)
        # rgb_edges = cv2.erode(rgb_edges, np.ones((3, 3)), iterations=3)

        # rgb_edges = cv2.resize(rgb_edges, None, fx=.2, fy=.2)
        rgb_edges = cv2.blur(rgb_edges, (5, 5))

        #### Template pre-processing
        template = cv2.imread(os.path.join(self.closestImage[0][0],
                                           self.closestImage[0][1]),
                              -1).astype('uint8')
        template = imutils.rotate_bound(template, 180)
        template = cv2.resize(template, (1728, 1217), interpolation=cv2.INTER_CUBIC)
        # equ_template = cv2.equalizeHist(template)
        blur_template = cv2.GaussianBlur(template, (7, 7), 7)
        equ_template = self.__class__.clahe.apply(blur_template)
        # cv2.imwrite("/Users/ardoo/Desktop/Thermals_Normalized/" + self.closestImage[0][1], equ_template)
        template_edges = cv2.Canny(equ_template, 30, 50)

        # template_edges = cv2.dilate(template_edges, np.ones((3, 3)), iterations=3)
        # template_edges = cv2.erode(template_edges, np.ones((3, 3)), iterations=3)

        # template_edges = cv2.resize(template_edges, None, fx=.2, fy=.2)
        template_edges = cv2.blur(template_edges, (5, 5))

        # self.show(rgb_image)
        # self.show(template)
        #
        # self.show(cv2.resize(rgb_edges, (1024, 768)))
        # self.show(cv2.resize(template_edges, (768, 480)))

        h, w = template.shape

        methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
                   'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
        method = eval(methods[0])
        res = cv2.matchTemplate(rgb_edges, template_edges, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc  # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum

        top_left = (top_left[0] + offset_1, top_left[1] + offset_0)

        # top_left = [i*5 for i in top_left]
        bottom_right = (top_left[0] + w, top_left[1] + h)

        print("Thermal {1} placed @ {0}: {2}"
              .format(self.file, self.closestImage[0][1], top_left))

        # overlap = np.zeros((rgb_edges.shape[0], rgb_edges.shape[1], 3))
        # overlap[:, :, 0] = rgb_edges
        # overlap[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0], 2] = template_edges
        # show(overlap)

        # collage = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2GRAY)
        collage = cv2.cvtColor(rgb_image_main, cv2.COLOR_BGR2GRAY)
        collage[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]] = template
        # self.collage = collage

        ## Temp . . .
        # cv2.rectangle(collage, top_left, bottom_right, 0, thickness=10)
        # (self.minY, self.minX), (self.maxY, self.maxX) = \
        #     top_left, bottom_right
        return top_left, bottom_right, collage


if __name__ == '__main__':
    rgb_path = "PycharmProjects/RGB_Termal_Match/Images/PT_05/JPG"
    thermal_path = "PycharmProjects/RGB_Termal_Match/Images/PT_05/THERMAL"
