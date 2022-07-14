# -*- coding: utf-8 -*-
from pathlib import PurePath
import logging

from Confocal_analyzer.utility.simaging.exceptions import FiletypeError
from Confocal_analyzer.utility.simaging.formats.rbfimage import RBFImage
from Confocal_analyzer.utility.simaging.formats.LAPMspectrum import LAPMSpectrum

logger = logging.Logger(__name__)

def readimage(file):
    """ Reads image file with automatic filetype detection """
    ftype = str.upper(PurePath(file).suffix)
    if ftype == ".RBF":
        img = RBFImage(file)
        return img
    else:
        logger.error("Invalid filetype %s: %s", ftype, file)
        raise FiletypeError(file)
    return None
    
def readspectrum(file):
    """ Reads spectrum file with automatic filetype detection """
    ftype = str.upper(PurePath(file).suffix)
    if ftype == ".TXT":
        img = LAPMSpectrum(file)
        return img
    else:
        logger.error("Invalid filetype %s: %s", ftype, file)
        raise FiletypeError(file)
    return None