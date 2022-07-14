from mainWindow import Analyzer, pg, tableAddRow
from PyQt5 import QtCore, QtWidgets, QtGui
import utility.odmr_tools.recognizeLAPMeasFile as loadLAP

import numpy as np
import lmfit
import string



def getColor(text):
	if text.startswith('('):
		return eval(text)
	else:
		return text

def activeData(gui:Analyzer, multi=False):
	"""returns the index of the currently active spectrum"""
	indices = gui.simpleFileTable.selectedIndexes()
	if multi:
		return indices
	if len(indices) == 0:
		return -1
	return indices[0].row()

def activeFit(gui:Analyzer, multi=False):
	"""returns the index of the currently active spectrum"""
	indices = gui.simpleFitTable.selectedIndexes()
	if multi:
		return indices
	if len(indices) == 0:
		return -1
	return indices[0].row()

def addDataToPlot(gui:Analyzer, data:dict):
	row = gui.simpleFileTable.rowCount() - 1
	x = data[gui.simpleFileTable.cellWidget(row, 3).currentText()]
	y = data[gui.simpleFileTable.cellWidget(row, 4).currentText()]
	if row == 0:
		gui.lineEditSimpleFrom.setText(str(min(x)))
		gui.lineEditSimpleTo.setText(str(max(x)))
	pen = pg.mkPen(width=1, color=gui.colors[row % len(gui.colors)])
	item = pg.PlotCurveItem(x, y, pen=pen)
	gui.simplePlotData.append(item)
	gui.calcBoxInput.addItem(' - - {} - - '.format(row))
	gui.calcBoxData.addItem(' - - {} - - '.format(row))

def addFitParameter(gui:Analyzer):
	i = activeFit(gui)
	params = gui.simpleFitParameters[i]
	newParam = None
	for l in string.ascii_letters:
		if l not in params.keys():
			params.update({l:[0, np.nan, np.nan]})
			newParam = l
			break
	if newParam is None:
		raise Exception('Too many parameters with simple letters!')
	gui.simpleUpdateStop = True
	tableAddRow(gui.simpleParameterTable, [newParam, '0', 'nan', 'nan'], [2,3])
	gui.simpleUpdateStop = False

def axisChanged(gui:Analyzer):
	for i, data in enumerate(gui.simpleData):
		x = data[gui.simpleFileTable.cellWidget(i, 3).currentText()]
		y = data[gui.simpleFileTable.cellWidget(i, 4).currentText()]
		pen = pg.mkPen(width=1, color=getColor(gui.simpleFileTable.item(i, 2).text()))
		item = pg.PlotCurveItem(x, y, pen=pen)
		gui.simplePlotData[i] = item

def calculateSimple(gui:Analyzer):
	inputIndex = gui.calcBoxInput.currentIndex()
	dataIndex = gui.calcBoxData.currentIndex()
	inputKeyX = gui.simpleFileTable.cellWidget(inputIndex, 3).currentText()
	dataKeyX = gui.simpleFileTable.cellWidget(dataIndex, 3).currentText()
	inputKeyY = gui.simpleFileTable.cellWidget(inputIndex, 4).currentText()
	dataKeyY = gui.simpleFileTable.cellWidget(dataIndex, 4).currentText()
	inputDataX = gui.simpleData[inputIndex][inputKeyX]
	inputDataY = gui.simpleData[inputIndex][inputKeyY]
	calctype = gui.calcBoxType.currentText()
	if gui.radioButtonCalcData.isChecked():
		datUse = True
		calcDataX = gui.simpleData[dataIndex][dataKeyX]
		calcDataY = gui.simpleData[dataIndex][dataKeyY]
	else:
		datUse = False
		calcDataX = calcDataY = float(gui.lineEditCalcScalar.text())
	if gui.radioButtonXaxis.isChecked():
		outputX = doCalcType(gui, inputDataX, calcDataX)
		outputY = inputDataY
		yKey = '{}: {}'.format(inputIndex, inputKeyY)
		if datUse:
			xKey = '{}: {} {} {}: {}'.format(inputIndex, inputKeyX, calctype, dataIndex, dataKeyX)
			name = 'X: {}: {} {} {}: {}'.format(gui.simpleFileTable.item(inputIndex, 0).text(), inputKeyX, calctype, gui.simpleFileTable.item(dataIndex, 0).text(), dataKeyX)
		else:
			xKey = '{}: {} {} {}'.format(inputIndex, inputKeyX, calctype, calcDataX)
			name = 'X: {}: {} {} {}'.format(gui.simpleFileTable.item(inputIndex, 0).text(), inputKeyX, calctype, calcDataX)
		shortname = xKey
	else:
		outputY = doCalcType(gui, inputDataY, calcDataY)
		outputX = inputDataX
		xKey = '{}: {}'.format(inputIndex, inputKeyX)
		if datUse:
			yKey = '{}: {} {} {}: {}'.format(inputIndex, inputKeyY, calctype, dataIndex, dataKeyY)
			name = 'Y: {}: {} {} {}: {}'.format(gui.simpleFileTable.item(inputIndex, 0).text(), inputKeyY, calctype, gui.simpleFileTable.item(dataIndex, 0).text(), dataKeyY)
		else:
			yKey = '{}: {} {} {}'.format(inputIndex, inputKeyY, calctype, calcDataY)
			name = 'Y: {}: {} {} {}'.format(gui.simpleFileTable.item(inputIndex, 0).text(), inputKeyY, calctype, calcDataY)
		shortname = yKey
	data = {xKey: outputX, yKey: outputY}
	gui.simpleUpdateStop = True
	color = gui.colors[gui.simpleFileTable.rowCount() % len(gui.colors)]
	boxX, boxY = getXYBoxes(gui, data)
	axBox = QtWidgets.QComboBox()
	axBox.addItems(['1', '2'])
	axBox.currentIndexChanged.connect(gui.axisChanged)
	gui.simpleData.append(data)
	tableAddRow(gui.simpleFileTable, [shortname, True, str(color), boxX, boxY, axBox, name], [6])
	gui.simpleUpdateStop = False
	addDataToPlot(gui, data)
	plot_all(gui)

def changeLimLinePos(gui:Analyzer):
	loVal = gui.lineEditSimpleFrom.text()
	hiVal = gui.lineEditSimpleTo.text()
	gui.limLineLo.setValue(float(loVal))
	gui.limLineHi.setValue(float(hiVal))

def limLinePosChanged(gui:Analyzer):
	posLo = gui.limLineLo.value()
	posHi = gui.limLineHi.value()
	gui.lineEditSimpleFrom.setText(str('%0.4f' % posLo))
	gui.lineEditSimpleTo.setText(str('%0.4f' % posHi))

def doCalcType(gui:Analyzer, inputData, calcData):
	calcFunction = gui.calcBoxType.currentIndex()
	if calcFunction == 0:
		return inputData + calcData
	elif calcFunction == 1:
		return inputData - calcData
	elif calcFunction == 2:
		return inputData * calcData
	elif calcFunction == 3:
		return inputData / calcData

def removeFile(gui:Analyzer):
	for index in activeData(gui, True)[::-1]:
		i = index.row()
		gui.simplePlotData.pop(i)
		gui.simpleFileTable.removeRow(i)
		gui.simpleData.pop(i)
		gui.calcBoxInput.removeItem(i)
		gui.calcBoxData.removeItem(i)
	plot_all(gui)

def removeParameter(gui:Analyzer):
	i = activeFit(gui)
	index = gui.simpleParameterTable.selectedIndexes()
	if len(index) < 1:
		raise Exception('Need to select a parameter!')
	row = index[0].row()
	param = gui.simpleParameterTable.item(index[0].row(), 0).text()
	gui.simpleFitParameters[i].pop(param)
	gui.simpleParameterTable.removeRow(row)

def plot_all(gui:Analyzer):
	gui.simplePlot.clear()
	gui.simplePlotTwin.clear()
	# removeSimpleLegend()

	if gui.checkBoxSimpleLimitLines.checkState():
		gui.simplePlot.addItem(gui.limLineLo)
		gui.simplePlot.addItem(gui.limLineHi)

	for i, line in enumerate(gui.simplePlotData):
		if gui.simpleFileTable.item(i, 1).checkState():
			# gui.legend
			if gui.simpleFileTable.cellWidget(i, 5).currentIndex() == 1:
				gui.simplePlotTwin.addItem(line)
			else:
				gui.simplePlot.addItem(line)

	for i, line in enumerate(gui.simplePlotFit):
		if gui.simpleFitTable.item(i+1, 1).checkState():
			gui.simplePlotFitNumbers.append(i)
			if gui.simpleFitTable.cellWidget(i+1, 3).currentIndex() == 1:
				gui.simplePlotTwin.addItem(line)
			else:
				gui.simplePlot.addItem(line)
	updateViews(gui)

def runSimpleFit(gui:Analyzer):
	fitNumber = gui.simpleFitTable.rowCount()
	dataNumber = activeData(gui)
	params = {}
	paramText = 'x'
	for j in range(gui.simpleParameterTable.rowCount()):
		key = gui.simpleParameterTable.item(j,0).text()
		if key == 'x':
			raise Exception('Do not use "x" as a parameter!')
		val = gui.simpleParameterTable.item(j,1).text()
		params.update({key: None if val == 'None' else float(val)})
		paramText += ', {}'.format(key)
	fitText = gui.lineEditSimpleFitFunc.text()
	declareText = 'lambda {}: {}'.format(paramText, fitText)
	fitFunc = eval(declareText)
	xStart = float(gui.lineEditSimpleFrom.text())
	xStop = float(gui.lineEditSimpleTo.text())
	fullXData = gui.simpleData[dataNumber][gui.simpleFileTable.cellWidget(dataNumber, 3).currentText()]
	start = np.argmin(np.abs(fullXData - xStart))
	stop = np.argmin(np.abs(fullXData - xStop))
	xData = fullXData[start:stop]
	yData = gui.simpleData[dataNumber][gui.simpleFileTable.cellWidget(dataNumber, 4).currentText()][start:stop]
	model = lmfit.model.Model(fitFunc)
	modelParams = model.make_params()
	try:
		for param in modelParams.keys():
			val = params[param]
			if val is None:
				continue
			modelParams[param].set(params[param])
	except:
		raise Exception('Fit function and params do not fit!')
	result = model.fit(yData, x=xData, params=modelParams)
	parameterData = {}
	gui.simpleFitParameters.append(parameterData)
	keys = result.params.keys()
	for i in range(gui.simpleParameterTable.rowCount()):
		key = gui.simpleParameterTable.item(i, 0).text()
		if key not in keys:
			continue
		inVal = modelParams[key].value
		outVal = result.params[key].value
		err = result.params[key].stderr
		parameterData.update({key: [inVal, outVal, err]})
	color = gui.simpleFileTable.item(dataNumber, 2).text()
	gui.simpleUpdateStop = True
	axBox = QtWidgets.QComboBox()
	axBox.addItems(['1', '2'])
	if gui.simpleFileTable.cellWidget(dataNumber, 5).currentText() == '2':
		axBox.setCurrentIndex(1)
	axBox.currentIndexChanged.connect(gui.axisChanged)
	xName = gui.simpleFileTable.cellWidget(dataNumber, 3).currentText()
	yName = gui.simpleFileTable.cellWidget(dataNumber, 4).currentText()
	fName = gui.simpleFileTable.item(dataNumber, 6).text()
	tableAddRow(gui.simpleFitTable, [str(fitNumber), True, color, axBox, 'x:{}, y:{}, file:{}'.format(xName, yName, fName)], [4])
	gui.simpleFitTable.item(fitNumber, 0).setSelected(True)
	gui.simpleUpdateStop = False
	updateFitParams(gui, fitNumber)
	plotItem = pg.PlotCurveItem(xData, result.best_fit, pen=pg.mkPen(width=2, color=color))
	gui.simplePlotFit.append(plotItem)
	plot_all(gui)

def saveCalculatedData(gui:Analyzer):
	i = activeData(gui)
	name = gui.simpleFileTable.item(i, 6).text()
	if name.startswith('X: ') or name.startswith('Y: '):
		filename = QtGui.QFileDialog.getSaveFileName(gui, 'Save Fit Data', gui.loadFolder, '*.txt')[0]
		loadLAP.dictToLAPfile(filename, gui.simpleData[i])
	else:
		raise Exception('It does not make sense to save measurement data again...')

def updateFitParams(gui:Analyzer, fitNumber=None):
	if fitNumber is None:
		i = activeFit(gui)
	else:
		i = fitNumber
	gui.simpleUpdateStop = True
	while gui.simpleParameterTable.rowCount() > 0:
		gui.simpleParameterTable.removeRow(gui.simpleParameterTable.rowCount() - 1)
	params = gui.simpleFitParameters[i]
	for k, v in params.items():
		tableAddRow(gui.simpleParameterTable, [k, '{:0.4f}'.format(v[0]), '{:0.4f}'.format(v[1]), '{:0.4f}'.format(v[2])], [2,3])
	gui.simpleUpdateStop = False



def updateLegend(gui:Analyzer):
	pass

def getXYBoxes(gui:Analyzer, data:dict):
	boxX = QtWidgets.QComboBox()
	boxX.addItems(data.keys())
	boxY = QtWidgets.QComboBox()
	boxY.addItems(data.keys())
	boxY.setCurrentIndex(1)
	boxX.currentIndexChanged.connect(gui.axisChanged)
	boxY.currentIndexChanged.connect(gui.axisChanged)
	return boxX, boxY


def updateViews(gui):
	# view has resized; update auxiliary views to match
	p1 = gui.simplePlot
	p2 = gui.simplePlotTwin
	p2.setGeometry(p1.vb.sceneBoundingRect())

	# need to re-update linked axes since this was called
	# incorrectly while views had different shapes.
	# (probably this should be handled in ViewBox.resizeEvent)
	p2.linkedViewChanged(p1.vb, p2.XAxis)
