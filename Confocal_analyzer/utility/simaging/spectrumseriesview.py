# -*- coding: utf-8 -*-
import os.path

import numpy as np
from PyQt5 import QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.imageview import ImageView
from pyqtgraph import ptime

class SpectrumSeriesView(ImageView):
    """ 
    Modified version of pyqtgraph.imageview.ImageView to view SpectrumSeries.
    In contrast to ImageView, it is possible to select a wavelength range
    and the image update is done just in time.
    """
    
    def __init__(self, parent=None, name="ImageSeriesView", view=None, imageItem=None, *args):
        super().__init__(parent, name, view, imageItem, *args)
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.__roi = None
        self.wledger = pg.InfiniteLine(0, movable=False)
        self.wledger.setPen(QtGui.QPen(QtGui.QColor(255, 200, 0, 200)))
        self.wledger.setZValue(1)
        self.ui.roiPlot.addItem(self.wledger)
        self.wledgel = pg.InfiniteLine(0, movable=False)
        self.wledgel.setPen(QtGui.QPen(QtGui.QColor(255, 200, 0, 200)))
        self.wledgel.setZValue(1)
        self.ui.roiPlot.addItem(self.wledgel)
        self.binsize = 10
        
    def setSeries(self, series, **kwargs):
        self.spectrumseries = series
        self.__maps = series.getSpectralMaps(self.binsize)
        self.setImage(self.__maps["maps"][0], **kwargs)
        
        self.__series = series
        if not self.__roi:
            pen = pg.mkPen(color=(180,180,0), width=3)
            pen.setWidth(2)
            self.__roi = pg.RectROI(
                (0, 0), 1, 1, translateSnap=True, 
                maxBounds=QtCore.QRect(0, 0, len(self.__maps["posbinsX"]) + 1, 
                                       len(self.__maps["posbinsY"]) + 1),
                pen=pen
            )
            self.__roi.sigRegionChanged.connect(self.roi_moved)
            self.addItem(self.__roi)
            self.__roi.removeHandle(self.__roi.getHandles()[0])
            self.__roi.show()
        #self.updateImage()
        self.wledger.show()
        self.wledgel.show()
        
        #add time axis
        sprange = series.getSpectralRange()
        self.tVals = np.arange(start=sprange[0], stop=sprange[1], step=1)
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
        self.ui.roiPlot.show()
        self.setCurrentIndex(0)
        self.updateROIPlot()
        
    # Override to support series
    def setCurrentIndex(self, ind):
        self.currentIndex = np.clip(ind, 0, len(self.tVals)-1)
        self.image = self.spectrumseries.getSpectralMap(self.tVals[self.currentIndex], self.binsize)["map"]
        self.wledgel.setValue(self.tVals[self.currentIndex] - self.binsize/2)
        self.wledger.setValue(self.tVals[self.currentIndex] + self.binsize/2)
        self.ignoreTimeLine = True
        self.timeLine.setValue(self.tVals[self.currentIndex])
        self.ignoreTimeLine = False
        self.imageDisp = None
        self.updateImage()
        
        
    def updateImage(self, autoHistogramRange=True):
        if self.image is None:
            return
        image = self.getProcessedImage()
        self.imageItem.updateImage(image)
        self.autoLevels()
        if autoHistogramRange:
            self.ui.histogram.setHistogramRange(self.levelMin, self.levelMax)
        
    def getProcessedImage(self):
        if self.imageDisp is None:
            #image = self.normalize(self.image)
            image = self.image
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
            if self.currentIndex+n > len(self.tVals):
                self.play(0)
            self.jumpFrames(n)
            
    def export(self, fileName):
        if self.hasTimeAxis():
            base, ext = os.path.splitext(fileName)
            fmt = "%%s%%0%dd%%s" % int(np.log10(len(self.tVals)+1))
            for i in range(len(self.tVals)):
                self.imageItem.setImage(self.spectrumseries.getSpectralMap(self.tVals[i], self.binsize)["map"], autoLevels=False)
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
        
    @QtCore.pyqtSlot(object)
    def roi_moved(self):
        self.updateROIPlot()
        return

    def updateROIPlot(self):
        self.roiCurve.setData(
            self.spectrumseries[self.__maps["indices"][int(self.__roi.pos()[0]), int(self.__roi.pos()[1])]].spectrum
        )
        self.roiCurve.show()
        self.ui.roiPlot.showAxis("left")
        
    def update(self):
        self.setCurrentIndex(self.currentIndex)
        
    def setBinsize(self, binsize):
        self.binsize = binsize
        self.update()