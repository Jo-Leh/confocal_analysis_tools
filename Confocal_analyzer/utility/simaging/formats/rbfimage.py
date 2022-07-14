# -*- coding: utf-8 -*-
import os
import logging

import numpy as np

from Confocal_analyzer.utility.simaging.image import Image
from Confocal_analyzer.utility.simaging.exceptions import FileError

logger = logging.Logger(__name__)

class RBFImage(Image):
    """Class capsuling Hamamatsu Hokawo Raw Binary File (*.rbf) images"""
    
    def __init__(self, file):
        super(RBFImage, self).__init__()
        self.file = os.path.abspath(file)
        logger.info("Read RBF file %s", self.file)
        with open(file, "rb") as fhnd:
            # check for correct header
            if fhnd.read(2) != b"ZZ":
                logger.error("Invalid header in file %s", self.file)
                raise FileError("Invalid header in file " + self.file)
            # read byteorder
            tmp = fhnd.read(2)
            if tmp == b"II":
                self.npbyteorder = "<"  # little endian
                self.endian = "little"
            elif tmp == b"MM":
                self.npbyteorder = ">"  # big endian
                self.endian = "big"
            else:
                logger.error("Invalid endian type in file %s", self.file)
                raise FileError("Invalid endian type in file " + self.file)
            logging.debug("Endian: %s", self.endian)
            # read header
            self.version = fhnd.read(1) + b"." + fhnd.read(1)
            logging.debug("Version: %s", self.version)
            self.width = int.from_bytes(fhnd.read(2), byteorder=self.endian)
            self.height = int.from_bytes(fhnd.read(2), byteorder=self.endian)
            logging.debug("Size: %s x %s", self.width, self.height)
            self.bpp = int.from_bytes(fhnd.read(2), byteorder=self.endian)
            logging.debug("Bits per pixel: %s", self.bpp)
            self.colortype = int.from_bytes(fhnd.read(2), 
                                            byteorder=self.endian)
            logging.debug("Colortype: %s", self.colortype)
            self.paletteentries = int.from_bytes(fhnd.read(2), 
                                                 byteorder=self.endian)
            logging.debug("Number of palette entries: %s", self.paletteentries)
            self.time = int.from_bytes(fhnd.read(4), byteorder=self.endian)
            logging.debug("Time of recording: %s", self.time)
            self.timestamp = int.from_bytes(fhnd.read(4), 
                                            byteorder=self.endian)
            logging.debug("Timestamp: %s", self.timestamp)
            # read image
            fhnd.seek(64)
            dt = np.dtype(self.npbyteorder + "u" + str(int(self.bpp/8)))
            self.image = np.reshape(
                np.fromfile(fhnd, dtype=dt, count=self.width*self.height), 
                (self.width, self.height)
            )
            # read image metadata
            self.meta = self.__createMetaDict(fhnd.read())
            logging.debug("Metadata: %s", self.meta)
            
    def __createMetaDict(self, meta):
        result = dict()
        for entry in (x.split(b"=") for x in meta.split(b";")):
            if len(entry) == 2:
                result[entry[0]] = entry[1]
        return result