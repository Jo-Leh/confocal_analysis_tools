# -*- coding: utf-8 -*-
#import threading
import logging
import os
import re
from pathlib import PurePath, Path

import numpy as np

import simaging.api as sapi

logger = logging.Logger(__name__)


class ImageSeries(object):
    """ Represents a series consisting of multiple images. """
    
    def __init__(self, file):
        if type(file) in (list, tuple):
            if len(file) > 1:
                self.__files = sorted([os.path.abspath(x) for x in file])
                print(self.__files)
            else:
                self.__findFiles(PurePath(os.path.abspath(file[0])))
        else:
            self.__findFiles(PurePath(os.path.abspath(file)))
        logger.info("Found $s files", len(self.__files))
    
    def __iter__(self):
        for img in self.__files:
            yield sapi.readimage(img)
        
    def __len__(self):
        return len(self.__files)
    
    def __getitem__(self, index):
        return sapi.readimage(self.__files[index])
        
    def __findFiles(self, file):
        logger.info("Searching for files: %s", file)
        filename = file.stem
        fileext = file.suffix
        basename = re.search(r"^(.+?)\d+$", filename).group(1)
        pattern = basename + "[0-9]*" + fileext
        self.__files = [str(x) for x in sorted(Path(file.parent).glob(pattern))]
        
    def getAll(self, progressHook=None):
        images = []
        for i, img in enumerate(self.__files):
            images.append(sapi.readimage(img).image)
            if progressHook:
                progressHook(i)
        return np.stack(images)