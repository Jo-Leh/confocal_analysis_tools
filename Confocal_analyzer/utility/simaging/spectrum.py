# -*- coding: utf-8 -*-
import logging

import numpy as np

logger = logging.Logger(__name__)

class Spectrum(object):
    """ Abstract base class for spectrum objects. """
    
    def __init__(self):
        self.file = ""
        self.datapoints = 0
        self.spectrum = np.empty([0, 0])