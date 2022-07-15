from mainWindow import Analyzer, pg
from utility.dltsTools import dltsMeasClass
from PyQt5 import QtCore, QtWidgets, QtGui
from scipy import optimize

import numpy as np
import pandas as pd
import os
import pickle

from scipy.signal import savgol_filter

def getColor(text):
    if text.startswith('('):
        return eval(text)
    else:
        return text

def tableAddRow(table: QtWidgets.QTableWidget, entries, fixedOnes=()):
    row = table.rowCount()
    table.insertRow(row)
    for i, entry in enumerate(entries):
        if type(entry) is bool:
            item = QtWidgets.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(entry)
            table.setItem(row, i, item)
        elif issubclass(type(entry), QtWidgets.QWidget) or type(entry) is QtWidgets.QWidget:
            table.setCellWidget(row, i, entry)
        else:
            item = QtWidgets.QTableWidgetItem(str(entry))
            if i in fixedOnes:
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            table.setItem(row, i, item)
    table.resizeColumnsToContents()

def addDataToPlot(gui:Analyzer, data:dltsMeasClass.OD_DLTS_Transient):
    row = gui.dltsFileTable.rowCount() - 1
    x = data.time
    y = data.signal
    # if row == 0:
    #     gui.lineEditSimpleFrom.setText(str(min(x)))
    #     gui.lineEditSimpleTo.setText(str(max(x)))
    pen = pg.mkPen(width=1, color=gui.colors[row % len(gui.colors)], style=QtCore.Qt.DotLine)
    item = pg.PlotCurveItem(x, y, pen=pen)
    pulseEndLine = pg.InfiniteLine(pos=data.pulseEnd, pen=gui.colors[row % len(gui.colors)], movable=False)
    pen2 = pg.mkPen(width=1, color=gui.colors[row % len(gui.colors)])
    item2 = pg.PlotCurveItem(x, data.smoothed, pen=pen2)
    gui.dltsPlotData.append([item, pulseEndLine, item2])
    transLinePosChanged(gui)

def removeFile(gui:Analyzer):
    for index in activeData(gui, True)[::-1]:
        i = index.row()
        gui.dltsPlotData.pop(i)
        gui.dltsFileTable.removeRow(i)
        gui.dltsData.pop(i)
        gui.calcBoxInput.removeItem(i)
        gui.calcBoxData.removeItem(i)
    plot_all(gui)

def activeData(gui:Analyzer, multi=False):
    """returns the index of the currently active spectrum"""
    indices = gui.dltsFileTable.selectedIndexes()
    if multi:
        return indices
    if len(indices) == 0:
        return -1
    return indices[0].row()

def dltsPackTableClicked(gui:Analyzer, index):
    r = index.row()
    if gui.dltsPackTableLastRow == r:
        return
    gui.dltsPackTableLastRow = r
    gui.dltsUpdateStop = True
    while gui.dltsFileTable.rowCount() > 0:
        gui.dltsFileTable.removeRow(0)
    gui.dltsData = gui.dltsDataPacks[r]
    # f = gui.dltsPackTable.item(r,2).text()
    gui.dltsPlotData = []
    for i, d in enumerate(gui.dltsData):
        file = d.fileName
        color = gui.colors[gui.dltsFileTable.rowCount() % len(gui.colors)]
        tableAddRow(gui.dltsFileTable, [d.name, d.windowSize, d.polyorder, True, True, str(color), file], [3])
        addDataToPlot(gui, d)
    gui.dltsUpdateStop = False
    plot_all(gui)

def dltsSaveSmoothedData(gui:Analyzer):
    foldername = QtWidgets.QFileDialog.getExistingDirectory(gui, 'Save smoothed data', gui.saveFolder)
    gui.saveFolder = foldername
    for i, pack in enumerate(gui.dltsDataPacks):
        for j, d in enumerate(pack):
            name = d.name
            if not name.endswith('.txt'):
                name += '.txt'
            dat = np.array([d.time, d.smoothed]).transpose()
            np.savetxt(foldername + '/' + name, dat, header='Time (s)\tsignal', comments='', delimiter='\t')

def dltsSaveCorrelationData(gui:Analyzer):
    data = sum(gui.dltsDataPacks, [])
    df = pd.DataFrame([d.corrAfter for d in data])
    filename = QtWidgets.QFileDialog.getSaveFileName(gui, 'Save smoothed data', gui.saveFolder, '*.txt')[0]
    gui.saveFolder = '/'.join(filename.split('/')[:-1])
    df.sort_values('temperature', inplace=True)
    df.to_csv(filename, sep='\t', index=False)



def updateLegend(gui:Analyzer, r):
    gui.dltsData[r].name = gui.dltsFileTable.item(r,0).text()

def plotAllRaw(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsFileTable.rowCount()):
        gui.dltsFileTable.item(row, 3).setCheckState(True)
    gui.dltsUpdateStop = False
    plot_all(gui)

def plotNoneRaw(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsFileTable.rowCount()):
        gui.dltsFileTable.item(row, 3).setCheckState(False)
    gui.dltsUpdateStop = False
    plot_all(gui)

def plotAllSmooth(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsFileTable.rowCount()):
        gui.dltsFileTable.item(row, 4).setCheckState(True)
    gui.dltsUpdateStop = False
    plot_all(gui)

def plotNoneSmooth(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsFileTable.rowCount()):
        gui.dltsFileTable.item(row, 4).setCheckState(False)
    gui.dltsUpdateStop = False
    plot_all(gui)

def plotAllCorr(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsCorrTable.rowCount() - 1):
        gui.dltsCorrTable.item(row, 3).setCheckState(True)
    gui.dltsUpdateStop = False
    gui.dltsCorrTable.item(gui.dltsCorrTable.rowCount()-1, 3).setCheckState(True)

def plotNoneCorr(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsCorrTable.rowCount() - 1):
        gui.dltsCorrTable.item(row, 3).setCheckState(False)
    gui.dltsUpdateStop = False
    gui.dltsCorrTable.item(gui.dltsCorrTable.rowCount()-1, 3).setCheckState(False)

def plotAllCorrSmooth(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsCorrTable.rowCount() - 1):
        gui.dltsCorrTable.item(row, 4).setCheckState(True)
    gui.dltsUpdateStop = False
    gui.dltsCorrTable.item(gui.dltsCorrTable.rowCount()-1, 4).setCheckState(True)

def plotNoneCorrSmooth(gui:Analyzer):
    gui.dltsUpdateStop = True
    for row in range(gui.dltsCorrTable.rowCount() - 1):
        gui.dltsCorrTable.item(row, 4).setCheckState(False)
    gui.dltsUpdateStop = False
    gui.dltsCorrTable.item(gui.dltsCorrTable.rowCount()-1, 4).setCheckState(False)

def applyBinning(gui:Analyzer):
    gui.dltsUpdateStop = True
    binning = int(gui.binAvgLine.text())
    for row in range(gui.dltsFileTable.rowCount()):
        data = gui.dltsData[row]
        data.changeBinning(binning)
        col = getColor(gui.dltsFileTable.item(row, 5).text())
        pen = pg.mkPen(width=1, color=col, style=QtCore.Qt.DotLine)
        item = pg.PlotCurveItem(data.time, data.signal, pen=pen)
        gui.dltsPlotData[row][0] = item
        pen2 = pg.mkPen(width=1, color=col)
        item2 = pg.PlotCurveItem(data.time, data.smoothed, pen=pen2)
        gui.dltsPlotData[row][2] = item2
    gui.dltsUpdateStop = False
    plot_all(gui)

def applySmoothing(gui:Analyzer):
    gui.dltsUpdateStop = True
    window = int(gui.smoothWindowLine.text())
    polyorder = int(gui.polyorderLine.text())
    savgol = gui.smoothSavgolCheckBox.checkState()
    for row in range(gui.dltsFileTable.rowCount()):
        gui.dltsFileTable.item(row, 1).setText(str(window))
        gui.dltsFileTable.item(row, 2).setText(str(polyorder))
        data = gui.dltsData[row]
        data.resmooth(window, polyorder, savgol)
        col = getColor(gui.dltsFileTable.item(row, 5).text())
        pen2 = pg.mkPen(width=1, color=col)
        item2 = pg.PlotCurveItem(data.time, data.smoothed, pen=pen2)
        gui.dltsPlotData[row][2] = item2
    gui.dltsUpdateStop = False
    plot_all(gui)


def resmooth(gui:Analyzer):
    savgol = gui.smoothSavgolCheckBox.checkState()
    for i, data in enumerate(gui.dltsData):
        window = int(gui.dltsFileTable.item(i, 1).text())
        poly = int(gui.dltsFileTable.item(i,2).text())
        data.resmooth(window, poly, savgol)
        pen2 = pg.mkPen(width=1, color=getColor(gui.dltsFileTable.item(i, 5).text()))
        item2 = pg.PlotCurveItem(data.time, data.smoothed, pen=pen2)
        gui.dltsPlotData[i][2] = item2
    plot_all(gui)

def transientPointsChanged(gui:Analyzer):
    startStart = float(gui.startTrans_start.text())
    stopStart = float(gui.stopTrans_start.text())
    time = gui.dltsData[0].time
    startStartArg = np.abs(startStart - time).argmin()
    stopStartArg = np.abs(stopStart - time).argmin()
    pointsStart = int(gui.startTransPointsLabel.text())
    pointsStop = int(gui.stopTransPointsLabel.text())
    startStop = time[startStartArg + pointsStart]
    stopStop = time[stopStartArg + pointsStop]
    gui.startTrans_stop.setText('{:.4e}'.format(startStop))
    gui.stopTrans_stop.setText('{:.4e}'.format(stopStop))
    changeTransLinePos(gui)

def calculateCorrelation(gui:Analyzer):
    gui.thread = CalcWorker(gui)
    gui.thread.sig_step.connect(gui.dltsProgressBar.signal_accept)
    gui.dltsProgressBar.cancelSig.connect(gui.thread._cancel)
    gui.thread.start()
    # afterStart = float(gui.stopTrans_start.text())
    # pointsStop = int(gui.stopTransPointsLabel.text())
    # startDiff = np.abs(afterStart - gui.dltsData[0].time).argmin() - gui.dltsData[0].pulseEndArg
    # # corrFunction = gui.correlationFunctionComboBox.currentText()
    # gui.dltsCorrelationData = []
    # norming = gui.dltsNormCorr.checkState()
    # for datas in gui.dltsDataPacks:
    #     for i, d in enumerate(datas):
    #         if i == 0:
    #             d.calcCorrelationsAfter(startpos=d.pulseEndArg+startDiff, endpos=d.pulseEndArg+startDiff+pointsStop, norm=True)
    #             normaliser = d.currentNorm
    #             print(normaliser)
    #         else:
    #             d.calcCorrelationsAfter(startpos=d.pulseEndArg+startDiff, endpos=d.pulseEndArg+startDiff+pointsStop, norm=normaliser)
    #         if norming:
    #             gui.dltsCorrelationData.append(d.corrAfterNormed)
    #         else:
    #             gui.dltsCorrelationData.append(d.corrAfter)

def smoothCorrelation(gui:Analyzer):
    gui.dltsCorrelationSmoothed = pd.DataFrame()
    for k in gui.dltsCorrelationData:
        if k in ['temperature', 'Vr', 'Vp']:
            gui.dltsCorrelationSmoothed[k] = gui.dltsCorrelationData[k]
            continue
        if '_' in k:
            i = dltsMeasClass.correlationListBefore.index(k) + len(dltsMeasClass.correlationList)
        else:
            i = dltsMeasClass.correlationList.index(k)
        window = int(gui.dltsCorrTable.item(i, 1).text())
        polyorder = int(gui.dltsCorrTable.item(i, 2).text())
        gui.dltsCorrelationSmoothed[k] = savgol_filter(gui.dltsCorrelationData[k], window_length=window, polyorder=polyorder)
    plotCorr(gui)

def changeNormState(gui:Analyzer):
    gui.dltsCorrelationData = []
    norming = gui.dltsNormCorr.checkState()
    for i, d in enumerate(gui.dltsData):
        if norming:
            gui.dltsCorrelationData.append(d.corrAfterNormed)
        else:
            gui.dltsCorrelationData.append(d.corrAfter)
    gui.dltsCorrelationDataFull = pd.DataFrame(gui.dltsCorrelationData).sort_values(by=['Vr', 'Vp', 'temperature'])

    Vr = float(gui.dltsVRbox.currentText()[5:14])
    Vp = float(gui.dltsVRbox.currentText()[22:-2])
    df = gui.dltsCorrelationDataFull
    gui.dltsCorrelationData = df[(df['Vr'] == Vr) & (df['Vp'] == Vp)]
    plotCorr(gui)

def plotCorr(gui:Analyzer):
    gui.dltsDataPlot.clear()
    x = np.asarray(gui.dltsCorrelationData['temperature'])
    for row in range(gui.dltsCorrTable.rowCount()):
        name = gui.dltsCorrTable.item(row, 0).text()
        rawMax = np.argmax(np.asarray(gui.dltsCorrelationData[name]))
        smoothMax = np.argmax(np.asarray(gui.dltsCorrelationSmoothed[name]))
        gui.dltsCorrTable.item(row, 7).setText(str(x[rawMax]))
        gui.dltsCorrTable.item(row, 8).setText(str(x[smoothMax]))
        if gui.dltsCorrTable.item(row, 3).checkState():
            pen = pg.mkPen(width=1, color=getColor(gui.dltsCorrTable.item(row, 5).text()), style=QtCore.Qt.DotLine)
            y = np.asarray(gui.dltsCorrelationData[name])
            item = pg.PlotCurveItem(x, y, pen=pen)
            gui.dltsDataPlot.addItem(item)
        if gui.dltsCorrTable.item(row, 4).checkState():
            pen = pg.mkPen(width=1, color=getColor(gui.dltsCorrTable.item(row, 5).text()))
            y = np.asarray(gui.dltsCorrelationSmoothed[name])
            item = pg.PlotCurveItem(x, y, pen=pen)
            gui.dltsDataPlot.addItem(item)



def changeTransLinePos(gui:Analyzer):
    startStart = float(gui.startTrans_start.text())
    startStop = float(gui.startTrans_stop.text())
    stopStart = float(gui.stopTrans_start.text())
    stopStop = float(gui.stopTrans_stop.text())
    gui.startStartLine.setValue(startStart)
    gui.startStopLine.setValue(startStop)
    gui.stopStartLine.setValue(stopStart)
    gui.stopStopLine.setValue(stopStop)
    time = gui.dltsData[0].time
    startStartArg = np.abs(startStart - time).argmin()
    startStopArg = np.abs(startStop - time).argmin()
    stopStartArg = np.abs(stopStart - time).argmin()
    stopStopArg = np.abs(stopStop - time).argmin()
    gui.startTransPointsLabel.setText('{}'.format(startStopArg - startStartArg))
    gui.stopTransPointsLabel.setText('{}'.format(stopStopArg - stopStartArg))

def transLinePosChanged(gui:Analyzer):
    startStart = gui.startStartLine.value()
    startStop = gui.startStopLine.value()
    stopStart = gui.stopStartLine.value()
    stopStop = gui.stopStopLine.value()
    minValStart, maxValStart, minValStop, maxValStop = getTransMinMax(gui)
    if minValStart <= startStart <= startStop <= maxValStart:
        gui.startTrans_start.setText('{:.4e}'.format(startStart))
        gui.startTrans_stop.setText('{:.4e}'.format(startStop))
    else:
        gui.startTrans_start.setText('{:.4e}'.format(minValStart))
        gui.startTrans_stop.setText('{:.4e}'.format(maxValStart))
        gui.startStartLine.setValue(minValStart)
        gui.startStopLine.setValue(maxValStart)
        startStart = minValStart
        startStop = maxValStart
    if minValStop <= stopStart <= stopStop <= maxValStop:
        gui.stopTrans_start.setText('{:.4e}'.format(stopStart))
        gui.stopTrans_stop.setText('{:.4e}'.format(stopStop))
    else:
        gui.stopTrans_start.setText('{:.4e}'.format(minValStop))
        gui.stopTrans_stop.setText('{:.4e}'.format(maxValStop))
        gui.stopStartLine.setValue(minValStop)
        gui.stopStopLine.setValue(maxValStop)
        stopStart = minValStop
        stopStop = maxValStop
    time = gui.dltsData[0].time
    startStartArg = np.abs(startStart - time).argmin()
    startStopArg = np.abs(startStop - time).argmin()
    stopStartArg = np.abs(stopStart - time).argmin()
    stopStopArg = np.abs(stopStop - time).argmin()
    gui.startTransPointsLabel.setText('{}'.format(startStopArg - startStartArg))
    gui.stopTransPointsLabel.setText('{}'.format(stopStopArg - stopStartArg))

def getTransMinMax(gui:Analyzer):
    i = activeData(gui)
    dat = gui.dltsData[i]
    pulsepos = dat.pulseEndArg
    time = dat.time
    return time[0], time[pulsepos], time[pulsepos-100], time[-1]


def plot_all(gui:Analyzer):
    gui.dltsPlot.clear()
    # removeSimpleLegend()
    gui.dltsPlot.addItem(gui.startStartLine)
    gui.dltsPlot.addItem(gui.startStopLine)
    gui.dltsPlot.addItem(gui.stopStartLine)
    gui.dltsPlot.addItem(gui.stopStopLine)
    # if gui.checkBoxSimpleLimitLines.checkState():
    #     pulseEndLine = pg.InfiniteLine(pos=None, pen='r', movable=True)
    #     gui.dltsPlot.addItem(gui.limLineLo)
    #     gui.dltsPlot.addItem(gui.limLineHi)

    for i, line in enumerate(gui.dltsPlotData):
        pl = False
        if gui.dltsFileTable.item(i, 3).checkState():
            # gui.legend
            gui.dltsPlot.addItem(line[0])
            pl = True
        if gui.dltsFileTable.item(i,4).checkState():
            gui.dltsPlot.addItem(line[2])
            pl = True
        if pl:
            gui.dltsPlot.addItem(line[1])

    # for i, line in enumerate(gui.dltsPlotFit):
    #     if gui.simpleFitTable.item(i+1, 1).checkState():
    #         gui.dltsPlotFitNumbers.append(i)
    #         if gui.simpleFitTable.cellWidget(i+1, 3).currentIndex() == 1:
    #             gui.dltsPlotTwin.addItem(line)
    #         else:
    #             gui.dltsPlot.addItem(line)
    # updateViews(gui)

def updateTau(gui:Analyzer, start, stop, startBefore=0, stopBefore=0, pulseWidth=0):
    Tw = stop - start
    TwBefore = stopBefore - startBefore
    # maxB1 = optimize.fmin(lambda tau: -dltsMeasClass.b1func(tau, start, Tw), 0)
    for i, fun in enumerate(dltsMeasClass.corrFuncList):
        res = optimize.fmin(lambda tau: -fun(tau, start, Tw), 0.5)
        res2 = optimize.fmin(lambda tau: -fun(tau, start, Tw, True), 0.5)
        gui.dltsCorrTable.item(i, 6).setText('{:.2e}\n{:.2e}'.format(res[0], res2[0]))
        if startBefore != stopBefore:
            res = optimize.fmin(lambda tau: -fun(tau, startBefore+pulseWidth, TwBefore), 0.5)
            res2 = optimize.fmin(lambda tau: -fun(tau, startBefore+pulseWidth, TwBefore, True), 0.5)
            gui.dltsCorrTable.item(i + len(dltsMeasClass.corrFuncList), 6).setText('{:.2e}\n{:.2e}'.format(res[0], res2[0]))
    # print(maxB1)

def changeVoltages(gui:Analyzer):
    Vr = float(gui.dltsVRbox.currentText()[5:14])
    Vp = float(gui.dltsVRbox.currentText()[22:-2])
    try:
        df = gui.dltsCorrelationDataFull
        gui.dltsCorrelationData = df[(df['Vr'] == Vr) & (df['Vp'] == Vp)]
        smoothCorrelation(gui)
    except Exception as e:
        print('tried changing voltages')
        print(e)


def saveData(gui:Analyzer):
    filename = QtWidgets.QFileDialog.getSaveFileName(gui, 'Save Fit Data', gui.loadFolder, '*.fdlts')[0]
    data = []
    for datPack in gui.dltsDataPacks:
        data += datPack
    with open(filename, 'wb') as file:
        pickle.dump(data, file)

def loadFile(gui:Analyzer, file):
    VrVpCombis = []
    with open(file, 'rb') as f:
        dataPack = pickle.load(f)
    gui.dltsDataPacks.append(dataPack)
    tableAddRow(gui.dltsPackTable, [file.split('/')[-1], True, file])
    gui.dltsData = dataPack
    for i, d in enumerate(dataPack):
        name = f'{d.T}K_{d.Vr}Vr_{d.Vp}Vp'
        color = gui.colors[gui.dltsFileTable.rowCount() % len(gui.colors)]
        gui.dltsUpdateStop = True
        tableAddRow(gui.dltsFileTable, [name.split('/')[-1], 51, 2, False, False, str(color), name], [3])
        gui.dltsUpdateStop = False
        addDataToPlot(gui, d)
        if d.Vr is not None and d.Vp is not None and 'Vr = {:.2e} V; Vp = {:.2e} V'.format(d.Vr, d.Vp) not in VrVpCombis:
            VrVpCombis.append('Vr = {:.2e} V; Vp = {:.2e} V'.format(d.Vr, d.Vp))
    plot_all(gui)
    gui.switchDLTS()
    gui.dltsUpdateStop = True
    for v in VrVpCombis:
        gui.dltsVRbox.addItem(v)
    gui.dltsVRbox.setCurrentIndex(0)
    gui.dltsUpdateStop = False
    gui.dltsPackTableLastRow = len(gui.dltsDataPacks) - 1
    if min(gui.dltsData[-1].time < -0.1):
        gui.startTrans_start.setText('-0.1')
        gui.dltsPulseWidthLine.setText('0.1')
    else:
        gui.startTrans_start.setText('-0.01')
        gui.dltsPulseWidthLine.setText('0.01')
    gui.startTransPointsLabel.setText('512')
    gui.stopTransPointsLabel.setText('512')




class ProgressBar(QtWidgets.QWidget):
    cancelSig = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)
        self.progress = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progress)
        self.cancel = QtWidgets.QPushButton('cancel')
        layout.addWidget(self.cancel)
        self.cancel.setEnabled(False)
        self.cancel.clicked.connect(self.cancelSend)

    def signal_accept(self, msg):
        self.progress.setValue(msg)

    def cancelSend(self):
        self.cancelSig.emit()
        self.cancel.setEnabled(False)

class CalcWorker(QtCore.QThread):
    sig_step = QtCore.pyqtSignal(int)

    def __init__(self, gui:Analyzer):
        super(CalcWorker, self).__init__()
        self.gui = gui
        self.cancel = False

    def run(self):
        self.sig_step.emit(0)
        afterStart = float(self.gui.stopTrans_start.text())
        afterStop = float(self.gui.stopTrans_stop.text())
        pointsAfter = int(self.gui.stopTransPointsLabel.text())
        beforeStart = float(self.gui.startTrans_start.text())
        beforeStop = float(self.gui.startTrans_stop.text())
        pointsBefore = int(self.gui.startTransPointsLabel.text())
        pulseWidth = float(self.gui.dltsPulseWidthLine.text())
        startDiffAfter = np.abs(afterStart - self.gui.dltsData[0].time).argmin() - self.gui.dltsData[0].pulseEndArg
        startDiffBefore = np.abs(beforeStart - self.gui.dltsData[0].time).argmin() - self.gui.dltsData[0].pulseEndArg
        self.gui.dltsCorrelationData = []
        norming = self.gui.dltsNormCorr.checkState()
        n = len(self.gui.dltsDataPacks)
        self.gui.dltsProgressBar.cancel.setEnabled(True)
        useSmooth = not self.gui.dltsUseRawForCorrBox.checkState()
        normaliser = None
        updateTau(self.gui, afterStart, afterStop, beforeStart, beforeStop, pulseWidth)
        for j, datas in enumerate(self.gui.dltsDataPacks):
            m = len(datas)
            if self.cancel:
                break
            for i, d in enumerate(datas):
                if self.cancel:
                    break
                if i == 0 and j == 0:
                    d.calcCorrelationsAfter(startpos=d.pulseEndArg+startDiffAfter, endpos=d.pulseEndArg+startDiffAfter+pointsAfter, norm=True, smooth=useSmooth)
                    normaliser = d.currentNorm
                    print(normaliser)
                    d.calcCorrelationsBefore(startpos=d.pulseEndArg+startDiffBefore, endpos=d.pulseEndArg+startDiffBefore+pointsBefore, norm=normaliser, smooth=useSmooth)
                else:
                    d.calcCorrelationsAfter(startpos=d.pulseEndArg+startDiffAfter, endpos=d.pulseEndArg+startDiffAfter+pointsAfter, norm=normaliser, smooth=useSmooth)
                    d.calcCorrelationsBefore(startpos=d.pulseEndArg+startDiffBefore, endpos=d.pulseEndArg+startDiffBefore+pointsBefore, norm=normaliser, smooth=useSmooth)
                dataSet = {}
                if norming:
                    dataSet.update(d.corrAfterNormed)
                    dataSet.update(d.corrBeforeNormed)
                    self.gui.dltsCorrelationData.append(d.corrAfterNormed)
                else:
                    dataSet.update(d.corrAfter)
                    dataSet.update(d.corrBefore)
                self.gui.dltsCorrelationData.append(dataSet)
                self.sig_step.emit(int((j+(i+1)/m)/n * 100))
        self.gui.dltsProgressBar.cancel.setEnabled(False)
        self.gui.dltsCorrelationDataFull = pd.DataFrame(self.gui.dltsCorrelationData).sort_values(by=['Vr', 'Vp', 'temperature'])
        try:
            Vr = float(self.gui.dltsVRbox.currentText()[5:14])
            Vp = float(self.gui.dltsVRbox.currentText()[22:-2])
            df = self.gui.dltsCorrelationDataFull
            self.gui.dltsCorrelationData = df[(df['Vr'] == Vr) & (df['Vp'] == Vp)]
        except:
            self.gui.dltsCorrelationData = self.gui.dltsCorrelationDataFull
        smoothCorrelation(self.gui)


    def _cancel(self):
        self.cancel = True


class LoadWorker(QtCore.QThread):
    sig_step = QtCore.pyqtSignal(int)

    def __init__(self, files, gui:Analyzer):
        super(LoadWorker, self).__init__()
        self.files = files
        self.gui = gui
        self.cancel = False

    def run(self):
        n = len(self.files)
        VRs = []
        VPs = []
        VrVpCombis = []
        self.gui.dltsProgressBar.cancel.setEnabled(True)
        if self.files[0].endswith('.txt'):
            if len(self.gui.dltsDataPacks) == 0:
                self.gui.dltsDataPacks.append(self.gui.dltsData)
                tableAddRow(self.gui.dltsPackTable, ['standard', True, 'none'])
            for i, file in enumerate(self.files):
                try:
                    if self.cancel:
                        break
                    data = dltsMeasClass.OD_DLTS_Transient(file)
                    if data.Vr is not None and data.Vp is not None and 'Vr = {:.2e} V; Vp = {:.2e} V'.format(data.Vr, data.Vp) not in VrVpCombis:
                        VrVpCombis.append('Vr = {:.2e} V; Vp = {:.2e} V'.format(data.Vr, data.Vp))
                    self.gui.dltsData.append(data)
                    color = self.gui.colors[self.gui.dltsFileTable.rowCount() % len(self.gui.colors)]
                    self.gui.dltsUpdateStop = True
                    tableAddRow(self.gui.dltsFileTable, [file.split('/')[-1], 51, 2, False, False, str(color), file], [3])
                    self.gui.dltsUpdateStop = False
                    addDataToPlot(self.gui, data)
                    self.sig_step.emit(int((i+1)/n * 100))
                except Exception as e:
                    print('Exception for:', file)
                    print(e)
        elif os.path.isdir(self.files[0]):
            for i, f in enumerate(self.files):
                dataPack = []
                self.gui.dltsDataPacks.append(dataPack)
                m = len(os.listdir(f))
                tableAddRow(self.gui.dltsPackTable, [f.split('/')[-1], True, f])
                for j, fil in enumerate(os.listdir(f)):
                    try:
                        file = f + '/' + fil
                        if self.cancel:
                            break
                        data = dltsMeasClass.OD_DLTS_Transient(file)
                        if data.Vr is not None and data.Vp is not None and 'Vr = {:.2e} V; Vp = {:.2e} V'.format(data.Vr, data.Vp) not in VrVpCombis:
                            VrVpCombis.append('Vr = {:.2e} V; Vp = {:.2e} V'.format(data.Vr, data.Vp))
                        dataPack.append(data)
                        self.sig_step.emit(int((i+(j+1)/m)/n * 100))
                    except Exception as e:
                        print('Exception for:', fil)
                        print(e)
                if i == n - 1:
                    self.gui.dltsData = self.gui.dltsDataPacks[-1]
                    for j, data in enumerate(self.gui.dltsData):
                        file = data.fileName
                        data = self.gui.dltsData[j]
                        color = self.gui.colors[self.gui.dltsFileTable.rowCount() % len(self.gui.colors)]
                        self.gui.dltsUpdateStop = True
                        tableAddRow(self.gui.dltsFileTable, [file.split('/')[-1], 51, 2, False, False, str(color), file], [3])
                        self.gui.dltsUpdateStop = False
                        addDataToPlot(self.gui, data)
        self.gui.dltsProgressBar.cancel.setEnabled(False)
        plot_all(self.gui)
        self.gui.switchDLTS()
        self.gui.dltsUpdateStop = True
        for v in VrVpCombis:
            self.gui.dltsVRbox.addItem(v)
        self.gui.dltsVRbox.setCurrentIndex(0)
        # self.gui.dltsVPbox.setCurrentIndex(0)
        self.gui.dltsUpdateStop = False
        self.gui.dltsPackTableLastRow = len(self.gui.dltsDataPacks) - 1
        if min(self.gui.dltsData[-1].time < -0.1):
            self.gui.startTrans_start.setText('-0.1')
            self.gui.dltsPulseWidthLine.setText('0.1')
        else:
            self.gui.startTrans_start.setText('-0.01')
            self.gui.dltsPulseWidthLine.setText('0.01')
        self.gui.startTransPointsLabel.setText('512')
        self.gui.stopTransPointsLabel.setText('512')

    def _cancel(self):
        self.cancel = True
