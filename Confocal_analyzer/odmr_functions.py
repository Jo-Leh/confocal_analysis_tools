from mainWindow import Analyzer, pg
from PyQt5 import QtCore, QtWidgets
from utility.odmr_tools import analyseODMRFunctions

import numpy as np

def getColor(text):
	if text.startswith('('):
		return eval(text)
	else:
		return text

def activeFitChange(gui:Analyzer, index):
	i = index.row()
	vals = gui.odmr_fits[i].best_values
	gui.labelFitF0_ODMR.setText('{:.4E}'.format(vals['mid']))
	gui.labelFitD_ODMR.setText('{:.4E}'.format(vals['distance']))
	gui.labelFitWidth_ODMR.setText('{:.4E}'.format(vals['linewidth']))
	gui.labelFitC_ODMR.setText('{:.4E}'.format(vals['contrast']))

def calcFit(gui:Analyzer):
	try:
		i = gui.measurement_list.selectedIndexes()[0].row()
	except:
		raise Exception('You need to select data to fit to!')
	xData = gui.odmr_data[i].filterFrequ
	yData = gui.odmr_data[i].sigAvg
	f0Guess = float(gui.textF0Guess_ODMR.text())
	dGuess = float(gui.textDGuess_ODMR.text())
	nGuess = float(gui.textNGuess_ODMR.text())
	wGuess = float(gui.textWidthGuess_ODMR.text())
	cGuess = float(gui.textCGuess_ODMR.text())
	bounds = {'contrast': (0, np.inf),
			  'mid': (0, np.inf),
			  'linewidth': (0, np.inf),
			  'distance': (0, np.inf)}
	vary = {'contrast': not gui.checkFixC_ODMR.checkState(),
			  'mid': not gui.checkFixF0_ODMR.checkState(),
			  'linewidth': not gui.checkFixWidth_ODMR.checkState(),
			  'distance': not gui.checkFixD_ODMR.checkState()}
	fit = analyseODMRFunctions.splittedODMRFit(xData, yData, cGuess, f0Guess, wGuess, dGuess, vary=vary, bounds=bounds)

	gui.odmr_fits.append(fit)
	vals = fit.best_values
	gui.labelFitF0_ODMR.setText('{:.4E}'.format(vals['mid']))
	gui.labelFitD_ODMR.setText('{:.4E}'.format(vals['distance']))
	gui.labelFitWidth_ODMR.setText('{:.4E}'.format(vals['linewidth']))
	gui.labelFitC_ODMR.setText('{:.4E}'.format(vals['contrast']))

	file = gui.odmr_labels[i]
	j = len(gui.odmr_fits) - 1
	gui.fitTable_ODMR.insertRow(j)
	name = QtWidgets.QTableWidgetItem(file)
	name.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
	gui.fitTable_ODMR.setItem(j, 0, name)
	gui.fitTable_ODMR.setItem(j, 1, QtWidgets.QTableWidgetItem('fit {}'.format(j)))
	gui.odmr_fitLabels.append('fit {}'.format(j))
	item = QtWidgets.QTableWidgetItem()
	gui.odmr_fitChecks.append(item)
	item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
	item.setCheckState(QtCore.Qt.Checked)
	gui.fitTable_ODMR.setItem(j, 2, gui.odmr_fitChecks[-1])

	color = getColor(gui.measurement_list.item(i, 4).text())
	gui.fitTable_ODMR.setItem(j, 3, QtWidgets.QTableWidgetItem(color))
	gui.fitTable_ODMR.resizeColumnsToContents()



def removeFit(gui:Analyzer):
	indices = gui.fitTable_ODMR.selectedIndexes()
	for index in indices:
		i = index.row()
		gui.fitTable_ODMR.removeRow(i)
		gui.odmr_fits.pop(i)
		gui.odmr_fitLabels.pop(i)
		gui.odmr_fitChecks.pop(i)

def plotData(gui:Analyzer):
	gui.odmr_plot.clear()
	for plot in gui.odmr_plotlist:
		gui.odmr_plot.addItem(plot)

def getSaveData(gui:Analyzer):
	pass


def updatePlotList(gui:Analyzer):
	gui.odmr_plotlist = []
	minX = np.inf
	maxX = -np.inf
	x = [0]
	for i, dat in enumerate(gui.odmr_data):
		if gui.odmr_checks[i][2].checkState():
			plotType = pg.ScatterPlotItem
		else:
			plotType = pg.PlotCurveItem
		color = gui.measurement_list.item(i, 4).text()
		if color.endswith(')'):
			color = eval(color)
		if gui.radioButton_showCountrates.isChecked():
			p1 = gui.odmr_checks[i][0].checkState()
			p2 = gui.odmr_checks[i][1].checkState()
			try:
				y0 = dat.avgPercent0
				y1 = dat.avgPercent1
				if gui.checkBox_average_APDs.checkState():
					y0 = (y0 + y1) / 2
					p1 = True
					p2 = False
			except:
				if gui.checkBox_overTimePlot.checkState():
					x = dat.time
					y0 = dat.countRate0
					y1 = dat.countRate1
					if gui.checkBox_average_APDs.checkState():
						y0 = (y0 + y1) / 2
						p1 = True
						p2 = False
					for up in dat.upSweepTimes:
						gui.odmr_plotlist.append(pg.InfiniteLine(pos=up, pen=pg.mkPen(width=1, color='r')))
					for down in dat.downSweepTimes:
						gui.odmr_plotlist.append(pg.InfiniteLine(pos=down, pen=pg.mkPen(width=1, color='b')))
				else:
					if gui.checkBox_conv_Signal.checkState():
						x = dat.filterFrequ
						if gui.checkBox_average_APDs.checkState():
							if gui.checkBox_split_up_down.checkState():
								if gui.checkBox_sweepwiseSignal.checkState():
									dat.makeSweepwiseSignal()
									y0 = dat.sweepwiseUpAvg
									y1 = dat.sweepwiseDownAvg
								else:
									y0 = dat.sigAvgUp
									y1 = dat.sigAvgDown
								p1 = p2 = True
							else:
								if gui.checkBox_sweepwiseSignal.checkState():
									dat.makeSweepwiseSignal()
									y0 = dat.sweepwiseAvg
								else:
									y0 = dat.sigAvg
								p1 = True
								p2 = False
						else:
							if gui.checkBox_split_up_down.checkState():
								if gui.checkBox_sweepwiseSignal.checkState():
									dat.makeSweepwiseSignal()
									y0 = dat.sweepwiseUp0
									y1 = dat.sweepwiseUp1
									y2 = dat.sweepwiseDown0
									y3 = dat.sweepwiseDown1
								else:
									y0 = dat.sigUp0
									y1 = dat.sigUp1
									y2 = dat.sigDown0
									y3 = dat.sigDown1
								if gui.odmr_checks[i][0].checkState():
									gui.odmr_plotlist.append(plotType(x, y0, pen=pg.mkPen(width=1, color=color)))
									gui.odmr_plotlist.append(plotType(x, y2, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DotLine)))
								if gui.odmr_checks[i][1].checkState():
									gui.odmr_plotlist.append(plotType(x, y1, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DashLine)))
									gui.odmr_plotlist.append(plotType(x, y3, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DashDotLine)))
								continue
							if gui.checkBox_sweepwiseSignal.checkState():
								dat.makeSweepwiseSignal()
								y0 = dat.sweepwise0
								y1 = dat.sweepwise1
							else:
								y0 = dat.signal0
								y1 = dat.signal1
					elif gui.checkBox_split_up_down.checkState():
						x = dat.filterFrequ
						if not gui.checkBox_average_APDs.checkState():
							y0 = dat.countsUp0
							y1 = dat.countsUp1
							y2 = dat.countsDown0
							y3 = dat.countsDown1
							if gui.odmr_checks[i][0].checkState():
								gui.odmr_plotlist.append(plotType(x, y0, pen=pg.mkPen(width=1, color=color)))
								gui.odmr_plotlist.append(plotType(x, y2, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DotLine)))
							if gui.odmr_checks[i][1].checkState():
								gui.odmr_plotlist.append(plotType(x, y1, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DashLine)))
								gui.odmr_plotlist.append(plotType(x, y3, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DashDotLine)))
							continue
						else:
							y0 = (dat.countsUp0 + dat.countsUp1) / 2
							y1 = (dat.countsDown0 + dat.countsDown1) / 2
							p1 = p2 = True
					elif gui.checkBox_average.checkState():
						x = dat.filterFrequ
						y0 = dat.avgCounts0
						y1 = dat.avgCounts1
						if gui.checkBox_average_APDs.checkState():
							y0 = (y0 + y1) / 2
							p1 = True
							p2 = False
					else:
						x = dat.frequency
						y0 = dat.countRate0
						y1 = dat.countRate1
						if gui.checkBox_average_APDs.checkState():
							y0 = (y0 + y1) / 2
							p1 = True
							p2 = False
			if p1:
				gui.odmr_plotlist.append(plotType(x, y0, pen=pg.mkPen(width=1, color=color)))
			if p2:
				gui.odmr_plotlist.append(plotType(x, y1, pen=pg.mkPen(width=1, color=color, style=QtCore.Qt.DashLine)))
		elif gui.radioButton_showRF.isChecked():
			if gui.checkBox_overTimePlot.checkState():
				x = dat.time
			else:
				x = dat.frequency
			try:
				gui.odmr_plotlist.append(plotType(x, dat.reflectedPower, pen=pg.mkPen(width=1, color=color)))
			except:
				pass
		else:
			if gui.checkBox_overTimePlot.checkState():
				x = dat.time
			else:
				x = dat.frequency
			try:
				gui.odmr_plotlist.append(plotType(x, dat.temperature, pen=pg.mkPen(width=1, color=color)))
			except:
				pass

	if min(x) < minX:
		minX = min(x)
	if max(x) > maxX:
		maxX = max(x)
	for i, fit in enumerate(gui.odmr_fits):
		if gui.odmr_fitChecks[i].checkState():
			color = getColor(gui.fitTable_ODMR.item(i, 3).text())
			x = np.linspace(minX, maxX, 5001)
			y = analyseODMRFunctions.splittedODMRLorentz(x, **fit.best_values)
			gui.odmr_plotlist.append(pg.PlotCurveItem(x, y, pen=pg.mkPen(width=1, color=color)))

def addToOdmrTable(gui:Analyzer, file):
	i = len(gui.odmr_data) - 1
	gui.measurement_list.insertRow(i)
	name = QtWidgets.QTableWidgetItem(file)
	name.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
	gui.measurement_list.setItem(i, 0, name)
	gui.measurement_list.setItem(i, 1, QtWidgets.QTableWidgetItem(file.split('/')[-1]))
	gui.odmr_labels.append(file.split('/')[-1])
	gui.odmr_checks.append((QtWidgets.QTableWidgetItem(), QtWidgets.QTableWidgetItem(), QtWidgets.QTableWidgetItem()))
	for item in gui.odmr_checks[-1]:
		item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
		item.setCheckState(QtCore.Qt.Checked)
	gui.measurement_list.setItem(i, 2, gui.odmr_checks[-1][0])
	gui.measurement_list.setItem(i, 3, gui.odmr_checks[-1][1])
	gui.measurement_list.setItem(i, 4, QtWidgets.QTableWidgetItem(str(gui.colors[i % len(gui.colors)])))
	gui.measurement_list.setItem(i, 5, gui.odmr_checks[-1][2])
	for i in range(4):
		gui.measurement_list.resizeColumnToContents(i + 1)

def removeFromTable(gui:Analyzer):
	indices = gui.measurement_list.selectedIndexes()
	indices = sorted(indices, key= lambda x: x.row())
	for index in indices[::-1]:
		i = index.row()
		gui.measurement_list.removeRow(i)
		gui.odmr_data.pop(i)
		gui.odmr_labels.pop(i)
		gui.odmr_checks.pop(i)
