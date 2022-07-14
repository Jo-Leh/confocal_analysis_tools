# -*- coding: utf-8 -*-
import logging

import numpy as np

logger = logging.Logger(__name__)

class Image(object):
    """ Abstract base class for image objects. """
    
    def __init__(self):
        self.file = ""
        self.width = 0
        self.height = 0
        self.image = np.empty([0, 0])