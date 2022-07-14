# -*- coding: utf-8 -*-
from PyQt4 import QtGui

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)
    

class HistplotQt(QtGui.QWidget):
    """ Widget for image histograms """
    
    def __init__(self, hostlayout, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.__hostlayout = hostlayout
        self.__figure = Figure()
        self.__canvas = FigureCanvas(self.__figure)
        self.__ax = self.__figure.add_subplot(111)
        self.__hostlayout.addWidget(self.__canvas)
        self.__curimg = None
        self.__curplot = None
        self.__span = None
        
    def __redraw(self):
        self.__ax.draw_artist(self.__ax.patch)
        self.__ax.draw_artist(self.__span)
        for bar in self.__bars:
            self.__ax.draw_artist(bar)
        self.__canvas.update()
        
    def showhist(self, image):
        self.__curimg = image
        self.__data, self.__bins = np.histogram(image.image.ravel(), bins=512)
        self.__bins = self.__bins[:-1]  # omit right edge of last bin
        self.__ymax = np.max(self.__data)
        self.__ax.xaxis.set_visible(False)
        self.__ax.yaxis.set_visible(False)
        self.__span = self.__ax.axvspan(0, 1, color="lightblue")
        self.__bars = self.__ax.bar(
            self.__bins, self.__data, width=self.__bins[-1]-self.__bins[-2],
            color="k", linewidth=0
        )   
        self.__ax.set_ylim(0, self.__ymax)
        #self.__figure.tight_layout()
        self.__canvas.draw()
    
    def setContrast(self, maxval, span, offset):
        self.__ax.set_xlim(0, maxval)
        self.__ax.set_ylim(0, self.__ymax)
        self.__span.set_xy([[offset, 0], [offset, 1], 
                            [offset+span, 1], [offset+span, 0], [offset, 0]])
        self.__redraw()