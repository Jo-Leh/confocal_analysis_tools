# -*- coding: utf-8 -*-
import os
import logging

import numpy as np

from Confocal_analyzer.utility.simaging.spectrum import Spectrum
#from simaging.exceptions import FileError

logger = logging.Logger(__name__)

class LAPMSpectrum(Spectrum):
    """Class capsuling Hamamatsu Hokawo Raw Binary File (*.rbf) images"""
    
    def __init__(self, file):
        super(LAPMSpectrum, self).__init__()
        logger.info("Read LAPM spectrum %s", self.file)
        headerlines = self.__getHeaderLines(file)
        self.spectrum = np.loadtxt(file, skiprows=headerlines)
        self.datapoints = self.spectrum.shape[0]
        
    def __getHeaderLines(self, file):#
        i = 0
        with open(file, "r") as fhnd:
            for line in fhnd:
                line = line.strip()
                if line[0] != "<" and line[0] != "#":
                    break
                i += 1
        return i