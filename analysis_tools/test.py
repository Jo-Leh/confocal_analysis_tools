import os
from shutil import copy, move
import tqdm
import re

# startFolder = r'//confocal1/LAP Measurements Data/Johannes/dlts/p2-5/2021-05-11/partTest_675nm_OD1_noPinhole_750LP_1e-5interval'

# def iterator(folder):
#     for item in tqdm.tqdm(os.listdir(folder), leave=True, position=1):
#         if os.path.isdir(folder + '/' + item):
#             iterator(folder + '/' + item)
#         else:
#             if '_001_' in item:
#                 target = r'E:/Data/confocal_LAP_measurements/DLTS/p2-5/2021-05-11/10ms'
#             else:
#                 target = r'E:/Data/confocal_LAP_measurements/DLTS/p2-5/2021-05-11/100ms'
#             copy(folder + '/' + item, target + '/' + item)




if __name__ == '__main__':
    base = r'E:\Data\confocal2\SNJ\CK-SNJ-S-03\2021-07-14\fromWaferTop_atThorn_highPressure'
    roughLike = r'^.*?_rough([-+eE\d.]+).*\.+'
    for i, f in enumerate(os.listdir(base)):
        m = re.match(roughLike, f)
        if m is not None:
            subdir = base + '/rough' + m[1]
            if not os.path.isdir(subdir):
                os.mkdir(subdir)
            move(base + '/' + f, subdir + '/' + f)

    # iterator(startFolder)
