# -*- coding: utf-8 -*-
import collections

import pyqtgraph as pg

class ROICollection(object):

    __availableROIs = {
        "Rectangle": pg.RectROI,
        "Ellipse": pg.EllipseROI,
        "Circle": pg.CircleROI
        #"LineSegment": pg.LineSegmentROI,
        #"PolyLine": pg.PolyLineROI,
        #"Line": pg.LineROI,
        #"MultiRectangle": pg.MultiRectROI
    }
    
    def __init__(self):
        self.__ROIs = collections.OrderedDict()
        
    def __len__(self):
        return len(self.__ROIs)
        
    def __getitem__(self, key):
        return self.__ROIs[key]
    
    def __contains__(self, key):
        return key in self.__ROIs
        
    def __iter__(self):
        for roi in self.__ROIs.items():
            yield roi
    
    def getAvailableROIs(self):
        return list(self.__availableROIs.keys())
        
    def getROINames(self):
        return list(self.__ROIs.keys())
        
    def newROI(self, ROItype, ROIname, ROIchangedSlot, *args, **kwargs):
        if ROIname in self:
            raise KeyError("Name already exists!")
        self.__ROIs[ROIname] = self.__availableROIs[ROItype](*args, **kwargs)
        if ROIchangedSlot:
            self.__ROIs[ROIname].sigRegionChangeFinished.connect(ROIchangedSlot)
        
    def addROIsToPlot(self, plot):
        [plot.addItem(roi) for roi in self.__ROIs.values()]
        
    def deleteROI(self, ROIname, plot=None):
        if plot:
            plot.removeItem(self.__ROIs[ROIname])
        del self.__ROIs[ROIname]