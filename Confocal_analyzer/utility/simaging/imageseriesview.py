# -*- coding: utf-8 -*-
import os.path

import numpy as np
from PyQt4 import QtCore, QtGui
from pyqtgraph.imageview import ImageView
from pyqtgraph import ptime

class ImageSeriesView(ImageView):
    """ 
    Modified version of pyqtgraph.imageview.ImageView to view ImageSeries.
    In contrast to ImageView this does not load the complete series into RAM.
    """    
    
    def __init__(self, parent=None, name="ImageSeriesView", view=None, imageItem=None, *args):
        super().__init__(parent, name, view, imageItem, *args)
        
    def setSeries(self, series, **kwargs):
        self.imageseries = series
        self.setImage(series[0].image, **kwargs)
        
        #add time axis
        self.tVals = np.arange(len(series))
        self.axes['t'] = 2
        self.ui.roiPlot.setXRange(self.tVals.min(), self.tVals.max())
        if len(self.tVals) > 1:
            start = self.tVals.min()
            stop = self.tVals.max() + abs(self.tVals[-1] - self.tVals[0]) * 0.02
        elif len(self.tVals) == 1:
            start = self.tVals[0] - 0.5
            stop = self.tVals[0] + 0.5
        else:
            start = 0
            stop = 1
        for s in [self.timeLine, self.normRgn]:
            s.setBounds([start, stop])
        self.roiClicked()
        self.setCurrentIndex(0)
        
    # Override to support series
    def setCurrentIndex(self, ind):
        self.currentIndex = np.clip(ind, 0, len(self.imageseries)-1)
        self.image = self.imageseries[self.currentIndex].image
        self.imageDisp = None
        self.updateImage()
        self.ignoreTimeLine = True
        self.timeLine.setValue(self.tVals[self.currentIndex])
        self.ignoreTimeLine = False
        
    def updateImage(self, autoHistogramRange=True):
        if self.image is None:
            return
        image = self.getProcessedImage()
        if autoHistogramRange:
            self.ui.histogram.setHistogramRange(self.levelMin, self.levelMax)
        self.ui.roiPlot.show()
        self.imageItem.updateImage(image)
        
    def getProcessedImage(self):
        if self.imageDisp is None:
            image = self.normalize(self.image)
            self.imageDisp = image
            self.levelMin, self.levelMax = list(map(float, self.quickMinMax(self.imageDisp)))
        return self.imageDisp
        
    def keyPressEvent(self, ev):
        #print ev.key()
        if ev.key() == QtCore.Qt.Key_Space:
            if self.playRate == 0:
                fps = (len(self.imageseries)-1) / (self.tVals[-1] - self.tVals[0])
                self.play(fps)
                #print fps
            else:
                self.play(0)
            ev.accept()
        elif ev.key() == QtCore.Qt.Key_Home:
            self.setCurrentIndex(0)
            self.play(0)
            ev.accept()
        elif ev.key() == QtCore.Qt.Key_End:
            self.setCurrentIndex(len(self.imageseries)-1)
            self.play(0)
            ev.accept()
        elif ev.key() in self.noRepeatKeys:
            ev.accept()
            if ev.isAutoRepeat():
                return
            self.keysPressed[ev.key()] = 1
            self.evalKeyState()
        else:
            QtGui.QWidget.keyPressEvent(self, ev)
            
    def timeout(self):
        now = ptime.time()
        dt = now - self.lastPlayTime
        if dt < 0:
            return
        n = int(self.playRate * dt)
        if n != 0:
            self.lastPlayTime += (float(n)/self.playRate)
            if self.currentIndex+n > len(self.imageseries):
                self.play(0)
            self.jumpFrames(n)
            
    def export(self, fileName):
        img = self.getProcessedImage()
        if self.hasTimeAxis():
            base, ext = os.path.splitext(fileName)
            fmt = "%%s%%0%dd%%s" % int(np.log10(len(self.imageseries)+1))
            for i in range(len(self.imageseries)):
                self.imageItem.setImage(img[i], autoLevels=False)
                self.imageItem.save(fmt % (base, i, ext))
            self.updateImage()
        else:
            self.imageItem.save(fileName)
            
    def timeLineChanged(self):
        if self.ignoreTimeLine:
            return
        self.play(0)
        (ind, time) = self.timeIndex(self.timeLine)
        if ind != self.currentIndex:
            self.setCurrentIndex(ind)
        self.sigTimeChanged.emit(ind, time)