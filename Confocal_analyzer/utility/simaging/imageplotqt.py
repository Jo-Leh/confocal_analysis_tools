# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavBar)
    

class ImageplotQt(QtGui.QWidget):
    """ Widget for plotting images """
    
    def __init__(self, hostlayout, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.__hostlayout = hostlayout
        self.__figure = Figure()
        self.__canvas = FigureCanvas(self.__figure)
        #self.__gridspec = GridSpec(3,3)
        self.__ax = self.__figure.add_subplot(111)
        self.__toolbar = NavBar(self.__canvas, parent)
        self.__hostlayout.addWidget(self.__canvas)
        self.__hostlayout.addWidget(self.__toolbar)
        self.__curimg = None
        self.__curplot = None
        self.__contrast = ()
        
    def showimg(self, image):
        self.__curimg = image
        self.__ax.xaxis.set_visible(False)
        self.__ax.yaxis.set_visible(False)
        if self.__curplot:
            self.__curplot.set_data(self.__curimg.image)
            self.__ax.draw_artist(self.__curplot)
            self.__canvas.update()
        else:
            self.__curplot = self.__ax.matshow(self.__curimg.image, cmap="gray")
            if self.__contrast:
                self.__curplot.set_clim(
                    (self.__contrast[2], self.__contrast[1]+self.__contrast[2])
                )
            self.__canvas.draw()
    
    def setContrast(self, maxval, span, offset):
        self.__contrast = (maxval, span, offset)
        self.__curplot.set_clim((offset, offset+span))
        self.__ax.draw_artist(self.__curplot)
        self.__canvas.update()