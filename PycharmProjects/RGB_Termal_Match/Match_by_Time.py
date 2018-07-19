import os
from datetime import datetime
from datetime import timedelta


def match_by_time(thermal_path, tif_path):
    thermal_Images_Times = {}
    for root, subs, files in os.walk(thermal_path):
        for file in files:
            try:
                thermal_Images_Times[(root, file)] = datetime.strptime(file.split('.')[0], '%Y%m%d_%H%M%S')
            except:
                pass

    # print(thermal_Images_Times)
    sync_time = timedelta(hours=1, minutes=59, seconds=26)

    matched_files = {}
    for root, subs, files in os.walk(tif_path):
        for sub in subs:
            for _root, _subs, _files in os.walk(os.path.join(root, sub)):
                for file in _files:
                    if "GRE" in file:
                        if '.' in _root: continue
                        image_date_time = datetime.strptime(file.split('.')[0][:-8], 'IMG_%y%m%d_%H%M%S_')
                        image_date_time += sync_time
                        print(image_date_time, file)

                        closest_image = sorted(
                            list(thermal_Images_Times.keys())[:],
                            key=lambda x: abs(image_date_time - thermal_Images_Times[x])
                        )[0]

                        time_span = abs(image_date_time - thermal_Images_Times[closest_image])
                        if time_span < timedelta(seconds=5):
                            print(thermal_Images_Times[closest_image], closest_image[1], '\n', time_span)
                            matched_files[(_root, file)] = (closest_image, time_span)
                        else:
                            print("    No Image Found!")

    print("{} out of {} thermal images matched with RGB images.".format(len(matched_files),
                                                                        len(thermal_Images_Times.items())))

    return matched_files

    if __name__ == "__main__":

        thermal_path = "/Volumes/NO NAME/PT_5/THERMAL/"
        tif_path = "/Volumes/NO NAME/PT_5/DCIM/"
        print(match_by_time(thermal_path, tif_path))