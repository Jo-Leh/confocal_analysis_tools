from PyQt5 import QtCore

# from PySide2 import QtCore

import numpy as np
import pyqtgraph as pg

from utility import spectrumProcessing

def getLabelTitle(labelNr, axNr, value):
	labelNames = ['f', 'V', 'X', 'Y', 'Z', 'R', 'lambda', 'piezo', 'stepper']
	labelUnits = ['MHz', 'V', 'µm', 'µm', 'µm', '°', 'nm', 'V']
	colors = ['red', 'blue']
	return "<span style='font-size: 14pt; color: %s'>%s: %0.2f %s" % (colors[axNr], labelNames[labelNr], value, labelUnits[labelNr])


class ImagerWindow:
	"""kwargs consists of:
	- GrWin: imager_GrWin
	- pushButtonSaveIntRoi: pushButtonSaveIntRoi_imager
	- lineLambda: [lambdaStart_imager, lambdaEnd_imager]
	- radioButton_fullBg: radioFullBg_imager
	- radioButton_SubtractBg: radioSubBg_imager
	- checkBox_iso: checkBox_iso_imager
	- checkBox_intROI: checkBox_intROI_imager
	- groupBox_options: groupBox_options_2
	- labels: [label_frequ, label_voltage, label_var1, label_var2]
	- removeimagerButton
	- varCombos: [self.comboBoxVar1, self.comboBoxVar2]
	- axCombos: [self.comboBoxXaxis, self.comboBoxYaxis]
	- abscissaButtons: [self.radioButtonWavelength, self.radioButtonEnergy, self.radioButtonRamanImg, self.imagerLaserWaveLine]
	- activeMeasurementsButton"""

	def __init__(self, **kwargs):
		self.hist = pg.HistogramLUTItem()
		self.GrWin = kwargs['GrWin']
		self.ImPlot = self.GrWin.addPlot()
		self.GrWin.addItem(self.hist)
		self.hist.autoHistogramRange()
		self.GrWin.nextRow()
		self.RoiPlot = self.GrWin.addPlot()
		self.GrWin.nextRow()
		self.RoiIntPlot = self.GrWin.addPlot()
		self.RoiIntPlot.hide()
		# kwargs['pushButtonSaveIntRoi'].clicked.connect(self.saveIntRoiTxt)
		self.infLineLo = pg.InfiniteLine(pos=1, pen='r', movable=True)
		self.infLineHi = pg.InfiniteLine(pos=2, pen='r', movable=True)
		self.infLineLo.sigPositionChangeFinished.connect(self.infLinePosChanged)
		self.infLineHi.sigPositionChangeFinished.connect(self.infLinePosChanged)

		self.infLinePos = pg.InfiniteLine(pos=1, pen='r', movable=True)
		self.infLinePos.sigPositionChanged.connect(self.specROImoved)
		self.RoiIntPlot.addItem(self.infLinePos)

		self.isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
		self.hist.vb.addItem(self.isoLine)
		self.isoLine.setZValue(1000)
		self.isoLine.sigDragged.connect(self.updateIsocurve)

		self.lineEdit_lambdaStart, self.lineEdit_lambdaEnd = kwargs['lineLambda']
		for l in kwargs['lineLambda']:
			l.returnPressed.connect(self.updateWavelengths)

		for box in kwargs['varCombos']:
			box.currentIndexChanged.connect(self.updateImage)
		self.comboBoxVar1, self.comboBoxVar2, self.comboBoxVar3, self.comboBoxVar4 = kwargs['varCombos']

		self.radioButton_fullBg = kwargs['radioButton_fullBg']
		self.radioButton_fullBg.setChecked(True)
		self.radioButton_fullBg.toggled.connect(self.updateImage)
		self.radioButton_SubtractBg = kwargs['radioButton_SubtractBg']
		self.radioButton_SubtractBg.toggled.connect(self.updateImage)

		self.checkBox_iso = kwargs['checkBox_iso']
		self.checkBox_iso.stateChanged.connect(self.updateIsocurve)
		self.iso = pg.IsocurveItem(pen='g')
		self.ImPlot.addItem(self.iso)
		self.iso.setZValue(5)

		self.checkBox_intROI = kwargs['checkBox_intROI']
		self.checkBox_intROI.stateChanged.connect(self.intROIstateChanged)

		self.activeSpecNr = 0
		self.lambdaStart = 0
		self.lambdaEnd = 0
		self.lambda_min = 0
		self.lambda_max = 0
		self.LastAcceptedRoiY = 0
		self.LastAcceptedRoiX = 0

		# for IntRoi Plot
		self.IntRoiLineData = []
		self.IntRoixData = []

		# displayOptions
		self.radioButtonWavelength, self.radioButtonEnergy, self.radioButtonRamanImg, self.imagerLaserWaveLine = kwargs['abscissaButtons']
		self.radioButtonWavelength.setChecked(True)
		self.radioButtonWavelength.toggled.connect(self.updateRoiPlot)
		self.radioButtonEnergy.toggled.connect(self.updateRoiPlot)
		self.radioButtonRamanImg.toggled.connect(self.updateRoiPlot)
		self.imagerLaserWaveLine.returnPressed.connect(self.updateRoiPlot)

		# ROIS
		self.pen1 = pg.mkPen('r', width=2, style=QtCore.Qt.DotLine)
		self.pen2 = pg.mkPen('g', width=2, style=QtCore.Qt.DashLine)
		self.specROI = pg.RectROI([0, 0], [1, 1], movable=True, translateSnap=True, maxBounds=None, pen=self.pen1, parent=self.ImPlot)

		self.specROI.removeHandle(self.specROI.getHandles()[-1])
		self.ImPlot.addItem(self.specROI)
		self.specROI.sigRegionChanged.connect(self.specROImoved)

		self.intROI = pg.LineSegmentROI(positions=[(0, 0), (1, 1)], parent=self.ImPlot, pen=self.pen2)
		self.ImPlot.addItem(self.intROI)
		self.intROI.sigRegionChanged.connect(self.update_intROIplot)
		self.intROI.hide()

		self.image = pg.ImageItem()
		self.ImPlot.addItem(self.image)

		self.groupBox_options = kwargs['groupBox_options']
		self.groupBox_options.setDisabled(True)

		self.label_frequ, self.label_voltage, self.label_var1, self.label_var2, self.label_var3, self.label_var4 = kwargs['labels']

		# image axes
		self.comboBoxXaxis, self.comboBoxYaxis = kwargs['axCombos']
		axes = ['frequency', 'voltage', 'x position', 'y position', 'z position', 'rotation', 'wavelength', 'piezo', 'stepper']
		for ax in axes:
			self.comboBoxXaxis.addItem(ax)
			self.comboBoxYaxis.addItem(ax)

		self.comboBoxXaxis.setEnabled(False)
		self.comboBoxYaxis.setEnabled(False)
		self.comboBoxXaxis.setCurrentIndex(2)
		self.comboBoxYaxis.setCurrentIndex(3)

		self.comboBoxXaxis.currentIndexChanged.connect(self.changeVariables)
		self.comboBoxYaxis.currentIndexChanged.connect(self.changeVariables)

		self.activeMeasMenu = kwargs['activeMeasMenu']
		self.activeMeasurementsButton = kwargs['activeMeasurementsButton']
		self.multipleMeasBox = kwargs['multipleMeasBox']
		self.activeMeasList = kwargs['activeMeasList']

		# File Working
		self.removeimagerButton = kwargs['removeimagerButton']
		self.comboBoximagerSelection = kwargs['comboBoximagerSelection']

		self.removeimagerButton.setDisabled(True)
		self.removeimagerButton.clicked.connect(self.removeMeasurement)
		self.comboBoximagerSelection.setDisabled(True)
		self.comboBoximagerSelection.currentIndexChanged.connect(self.changeActiveMeas)

		# Definitions
		self.colors = ['w', 'r', (0, 100, 255), 'g', 'c', 'm', 'y']

		self.activeVar1 = 0
		self.activeVar2 = 0
		self.nrFrequencies = 0
		self.nrVoltages = 0
		self.dimension = 0
		self.nrXpos = 0
		self.nrYpos = 0
		self.nrZpos = 0
		self.nrRots = 0
		self.nrPiezos = 0
		self.nrSteppers = 0
		self.data = np.empty(0)
		self.dataSets = []
		self.relevantData = []
		self.relevantSorter = []
		self.frequencies = []
		self.voltages = []
		self.xCoors = []
		self.yCoors = []
		self.zCoors = []
		self.rotations = []
		self.piezos = []
		self.steppers = []
		self.intensity_image = np.empty(0)
		self.sorter = np.empty(0)
		self.sorterSets = []

		self.nrXaxis = 0
		self.nrYaxis = 0
		self.xAxis = []
		self.yAxis = []
		self.choice1 = []
		self.choice2 = []
		self.xIndex = 0
		self.yIndex = 1
		self.indexVar1 = 2
		self.indexVar2 = 3
		self.indexVar3 = 4
		self.indexVar4 = 5
		self.var1 = []
		self.var2 = []
		self.var3 = []
		self.var4 = []
		self.varLabels = [
			"<span style='font-size: 14pt; font-weight: 600'>f (MHz)",
			"<span style='font-size: 14pt; font-weight: 600'>V (V)",
			"<span style='font-size: 14pt; font-weight: 600'>X (µm)",
			"<span style='font-size: 14pt; font-weight: 600'>Y (µm)",
			"<span style='font-size: 14pt; font-weight: 600'>Z (µm)",
			"<span style='font-size: 14pt; font-weight: 600'>R (°)"
		]
		self.ignoreUpdate = False
		self.lowPos = 0
		self.highPos = 0

		self.xCoorSets = []
		self.yCoorSets = []
		self.zCoorSets = []
		self.voltageSets = []
		self.frequencySets = []
		self.rotationSets = []
		self.piezoSets = []
		self.stepperSets = []

		self.xCoorNrSets = []
		self.yCoorNrSets = []
		self.zCoorNrSets = []
		self.voltageNrSets = []
		self.frequencyNrSets = []
		self.rotationNrSets = []
		self.piezoNrSets = []
		self.stepperNrSets = []

		self.activeDatas = []
		self.activeSorters = []

		self.xSets = []
		self.xNrSets = []
		self.ySets = []
		self.yNrSets = []

		self.activeSpecNumbers = []

		self.relDataSets = []
		self.relSorterSets = []

		self.intensityImages = []
		self.noChange = False

	# GUI utility
	def changeActiveMeas(self):
		self.activeDatas = []
		self.activeSorters = []
		if len(self.activeMeasList) < 1:
			return

		for i, act in enumerate(self.activeMeasList):
			if act.isChecked():
				self.activeDatas.append(self.dataSets[i].data)
				self.activeSorters.append(self.sorterSets[i])
		self.xCoorSets = []
		self.yCoorSets = []
		self.zCoorSets = []
		self.voltageSets = []
		self.frequencySets = []
		self.rotationSets = []
		self.piezoSets = []
		self.stepperSets = []

		self.xCoorNrSets = []
		self.yCoorNrSets = []
		self.zCoorNrSets = []
		self.voltageNrSets = []
		self.frequencyNrSets = []
		self.rotationNrSets = []
		self.piezoNrSets = []
		self.stepperNrSets = []

		for j, dataSet in enumerate(self.activeDatas):
			xCoorsRed = []
			yCoorsRed = []
			zCoorsRed = []
			Volts = []
			Frequs = []
			rots = []
			piezos = []
			steppers = []

			for i in range(0, np.shape(dataSet)[0]):
				xCoorsRed.append(dataSet[i][1][1])
				yCoorsRed.append(dataSet[i][1][2])
				zCoorsRed.append(dataSet[i][1][4])
				Volts.append(dataSet[i][1][0])
				Frequs.append(dataSet[i][1][3])
				rots.append(dataSet[i][1][5])
				piezos.append(dataSet[i][1][6])
				steppers.append(dataSet[i][1][7])

			self.xCoorSets.append(sorted(list(set(xCoorsRed))))
			self.yCoorSets.append(sorted(list(set(yCoorsRed))))
			self.zCoorSets.append(sorted(list(set(zCoorsRed))))
			self.voltageSets.append(sorted(list(set(Volts))))
			self.frequencySets.append(sorted(list(set(Frequs))))
			self.rotationSets.append(sorted(list(set(rots))))
			self.piezoSets.append(sorted(list(set(piezos))))
			self.stepperSets.append(sorted(list(set(steppers))))

			self.xCoorNrSets.append(len(self.xCoorSets[j]))
			self.yCoorNrSets.append(len(self.yCoorSets[j]))
			self.zCoorNrSets.append(len(self.zCoorSets[j]))
			self.voltageNrSets.append(len(self.voltageSets[j]))
			self.frequencyNrSets.append(len(self.frequencySets[j]))
			self.piezoNrSets.append(len(self.piezoSets[j]))
			self.stepperNrSets.append(len(self.stepperSets[j]))

		i = self.comboBoximagerSelection.currentIndex()
		try:
			self.data = self.dataSets[i].data
			self.sorter = self.sorterSets[i]
		except IndexError:
			self.clearImage()
			self.comboBoximagerSelection.setDisabled(True)
			self.removeimagerButton.setDisabled(True)
			return

		#########START
		xCoorsRed = []
		yCoorsRed = []
		zCoorsRed = []
		Volts = []
		Frequs = []
		rots = []
		piezos = []
		steppers = []

		for i in range(0, np.shape(self.data)[0]):
			xCoorsRed.append(self.data[i][1][1])
			yCoorsRed.append(self.data[i][1][2])
			zCoorsRed.append(self.data[i][1][4])
			Volts.append(self.data[i][1][0])
			Frequs.append(self.data[i][1][3])
			rots.append(self.data[i][1][5])
			piezos.append(self.data[i][1][6])
			steppers.append(self.data[i][1][7])

		self.xCoors = sorted(list(set(xCoorsRed)))
		self.yCoors = sorted(list(set(yCoorsRed)))
		self.zCoors = sorted(list(set(zCoorsRed)))
		self.voltages = sorted(list(set(Volts)))
		self.frequencies = sorted(list(set(Frequs)))
		self.rotations = sorted(list(set(rots)))
		self.piezos = sorted(list(set(piezos)))
		self.steppers = sorted(list(set(steppers)))

		self.nrXpos = len(self.xCoors)
		self.nrYpos = len(self.yCoors)
		self.nrZpos = len(self.zCoors)
		self.nrVoltages = len(self.voltages)
		self.nrFrequencies = len(self.frequencies)
		self.nrRots = len(self.rotations)
		self.nrPiezos = len(self.piezos)
		self.nrSteppers = len(self.steppers)
		#########END
		self.changeVariables()

		self.dimension = 2 if self.nrXaxis > 1 and self.nrYaxis > 1 else 1

		self.lambda_min = self.data[0][2].spectrum[:, 0][0]
		self.lambda_max = self.data[0][2].spectrum[:, 0][-1]
		self.lambdaStart = self.lambda_min
		self.lambdaEnd = self.lambda_max

		self.updateWavelengths()
		# self.updateImage()

	def changeVariables(self):
		if self.noChange:
			return
		if self.comboBoxXaxis.currentIndex() == self.comboBoxYaxis.currentIndex():
			return
		self.xIndex = self.comboBoxXaxis.currentIndex()
		self.wavelength = 0
		if self.xIndex == 0:
			self.nrXaxis = self.nrFrequencies
			self.xAxis = self.frequencies
			self.xSets = self.frequencySets
			self.xNrSets = self.frequencyNrSets
		elif self.xIndex == 1:
			self.nrXaxis = self.nrVoltages
			self.xAxis = self.voltages
			self.xSets = self.voltageSets
			self.xNrSets = self.voltageNrSets
		elif self.xIndex == 2:
			self.nrXaxis = self.nrXpos
			self.xAxis = self.xCoors
			self.xSets = self.xCoorSets
			self.xNrSets = self.xCoorNrSets
		elif self.xIndex == 3:
			self.nrXaxis = self.nrYpos
			self.xAxis = self.yCoors
			self.xSets = self.yCoorSets
			self.xNrSets = self.yCoorNrSets
		elif self.xIndex == 4:
			self.nrXaxis = self.nrZpos
			self.xAxis = self.zCoors
			self.xSets = self.zCoorSets
			self.xNrSets = self.zCoorNrSets
		elif self.xIndex == 5:
			self.nrXaxis = self.nrRots
			self.xAxis = self.rotations
			self.xSets = self.rotationSets
			self.xNrSets = self.rotationNrSets
		elif self.xIndex == 6:
			self.nrXaxis = self.nrPiezos
			self.xAxis = self.piezos
			self.xSets = self.piezoSets
			self.xNrSets = self.piezoNrSets
		elif self.xIndex == 7:
			self.nrXaxis = self.nrSteppers
			self.xAxis = self.steppers
			self.xSets = self.stepperSets
			self.xNrSets = self.stepperNrSets
		else:
			self.wavelength = 1
		self.yIndex = self.comboBoxYaxis.currentIndex()
		if self.yIndex == 0:
			self.nrYaxis = self.nrFrequencies
			self.yAxis = self.frequencies
			self.ySets = self.frequencySets
			self.yNrSets = self.frequencyNrSets
		elif self.yIndex == 1:
			self.nrYaxis = self.nrVoltages
			self.yAxis = self.voltages
			self.ySets = self.voltageSets
			self.yNrSets = self.voltageNrSets
		elif self.yIndex == 2:
			self.nrYaxis = self.nrXpos
			self.yAxis = self.xCoors
			self.ySets = self.xCoorSets
			self.yNrSets = self.xCoorNrSets
		elif self.yIndex == 3:
			self.nrYaxis = self.nrYpos
			self.yAxis = self.yCoors
			self.ySets = self.yCoorSets
			self.yNrSets = self.yCoorNrSets
		elif self.yIndex == 4:
			self.nrYaxis = self.nrZpos
			self.yAxis = self.zCoors
			self.ySets = self.zCoorSets
			self.yNrSets = self.zCoorNrSets
		elif self.yIndex == 5:
			self.nrYaxis = self.nrRots
			self.yAxis = self.rotations
			self.ySets = self.rotationSets
			self.yNrSets = self.rotationNrSets
		elif self.yIndex == 6:
			self.nrYaxis = self.nrPiezos
			self.yAxis = self.piezos
			self.ySets = self.piezoSets
			self.yNrSets = self.piezoNrSets
		elif self.yIndex == 7:
			self.nrYaxis = self.nrSteppers
			self.yAxis = self.steppers
			self.ySets = self.stepperSets
			self.yNrSets = self.stepperNrSets
		else:
			self.wavelength = 2

		self.dimension = 2 if len(self.xAxis) > 1 and len(self.yAxis) > 1 else 1

		indices = [self.frequencies, self.voltages, self.xCoors, self.yCoors, self.zCoors, self.rotations]
		# if self.xIndex < 2 and self.yIndex < 2:
		# 	self.var1 = self.xCoors
		# 	self.var2 = self.yCoors
		# 	self.indexVar1 = 2
		# 	self.indexVar2 = 3
		# 	self.label_var1.setText(self.varLabels[2])
		# 	self.label_var2.setText(self.varLabels[3])
		# elif self.xIndex > 1 and self.yIndex > 1:
		# 	self.var1 = self.frequencies
		# 	self.var2 = self.voltages
		# 	self.indexVar1 = 0
		# 	self.indexVar2 = 1
		# 	self.label_var1.setText(self.varLabels[0])
		# 	self.label_var2.setText(self.varLabels[1])
		# else:
		xDone = False
		yDone = False
		zDone = False
		for i in range(6):
			if not i == self.xIndex and not i == self.yIndex:
				if not xDone:
					self.var1 = indices[i]
					self.label_var1.setText(self.varLabels[i])
					self.indexVar1 = i
					xDone = True
				elif not yDone:
					self.var2 = indices[i]
					self.label_var2.setText(self.varLabels[i])
					self.indexVar2 = i
					yDone = True
				elif not zDone:
					self.var3 = indices[i]
					self.label_var3.setText(self.varLabels[i])
					self.indexVar3 = i
					zDone = True
				else:
					self.var4 = indices[i]
					self.label_var4.setText(self.varLabels[i])
					self.indexVar4 = i
					yDone = True
		print('yDone: ' + str(yDone))

		self.ignoreUpdate = True
		self.comboBoxVar1.clear()
		for x in self.var1:
			self.comboBoxVar1.addItem(str(x))
		self.comboBoxVar2.clear()
		for y in self.var2:
			self.comboBoxVar2.addItem(str(y))
		self.comboBoxVar3.clear()
		for z in self.var3:
			self.comboBoxVar3.addItem(str(z))
		self.comboBoxVar4.clear()
		for r in self.var4:
			self.comboBoxVar4.addItem(str(r))

		self.ignoreUpdate = False
		if self.wavelength > 0:
			self.wavelengthImage()
			return
		self.comboBoxVar1.setCurrentIndex(0)
		self.comboBoxVar2.setCurrentIndex(0)
		self.comboBoxVar3.setCurrentIndex(0)
		self.comboBoxVar4.setCurrentIndex(0)
		self.updateWavelengths()
		self.updateImage()
		self.intROI.setPos((0,0), finish=False)
		self.intROI.setSize(1,finish=False)
		try:
			self.specROI.setPos((0,0))
			self.infLinePos.setValue(self.lowPos)
		except:
			pass

	def clearImage(self):
		self.image.clear()
		self.RoiPlot.clear()
		self.iso.hide()

	def intROIstateChanged(self):
		if self.checkBox_intROI.isChecked():
			self.intROI.show()
			self.RoiIntPlot.show()
			if self.dimension < 2:
				self.infLinePos.show()
			else:
				self.infLinePos.hide()
		else:
			self.RoiIntPlot.hide()
			self.intROI.hide()

	def infLinePosChanged(self):
		posLo = self.infLineLo.value()
		posHi = self.infLineHi.value()
		if self.radioButtonEnergy.isChecked():
			loVal = 1239.841857 / posHi
			hiVal = 1239.841857 / posLo
		elif self.radioButtonRamanImg.isChecked():
			laserWave = float(self.imagerLaserWaveLine.text())
			loVal = 1/(1/laserWave - 1e-7 * posLo)
			hiVal = 1/(1/laserWave - 1e-7 * posHi)
		else:
			hiVal = posHi
			loVal = posLo
		if hiVal > loVal > self.lambda_min and loVal < self.lambda_max:
			self.lineEdit_lambdaStart.setText(str('%0.2f' % loVal))
		else:
			self.lineEdit_lambdaStart.setText(str(self.lambdaStart))

		if loVal < hiVal < self.lambda_max and hiVal > self.lambda_min:
			self.lineEdit_lambdaEnd.setText(str('%0.2f' % posHi))
		else:
			self.lineEdit_lambdaEnd.setText(str(self.lambdaEnd))

		self.updateWavelengths()

	def removeMeasurement(self):
		i = self.comboBoximagerSelection.currentIndex()
		act = self.activeMeasList.pop(i)
		self.dataSets.pop(i)
		if len(self.dataSets) < 2:
			self.activeMeasurementsButton.setEnabled(False)
		self.comboBoximagerSelection.removeItem(i)
		self.activeMeasMenu.removeAction(act)
		self.changeActiveMeas()

	def getActiveSpecs(self):
		linePos = self.infLinePos.value()
		self.activeSpecNumbers = []
		for i in range(len(self.xSets)):
			try:
				if len(self.xAxis) > 1:
					x = (np.abs(np.asarray(self.xSets[i]) - linePos)).argmin()
					y = 0
				else:
					x = 0
					y = (np.abs(np.asarray(self.ySets) - linePos)).argmin()

				self.activeSpecNumbers.append(int(x * len(self.yAxis) + y))
			except Exception as e:
				print('Test 6', e)


	def specROImoved(self):
		if self.dimension > 1:
			x = int(self.specROI.pos()[0])
			y = int(self.specROI.pos()[1])
		else:
			linePos = self.infLinePos.value()
			if len(self.xAxis) > 1:
				x = (np.abs(np.asarray(self.xAxis) - linePos)).argmin()
				y = 0
				if min(self.xAxis) > linePos:
					self.infLinePos.setValue(self.lowPos)
				if linePos > max(self.xAxis):
					self.infLinePos.setValue(self.highPos)
			else:
				x = 0
				y = (np.abs(np.asarray(self.yAxis) - linePos)).argmin()
				if min(self.yAxis) > linePos:
					self.infLinePos.setValue(self.lowPos)
				if linePos > max(self.yAxis):
					self.infLinePos.setValue(self.highPos)

		if 0 <= x < len(self.xAxis) and 0 <= y < len(self.yAxis):
			self.LastAcceptedRoiX = x
			self.LastAcceptedRoiY = y
			xPos = self.xAxis[x]
			yPos = self.yAxis[y]
			self.activeSpecNr = int(x * len(self.yAxis) + y)
			try:
				self.getActiveSpecs()
			except Exception as e:
				print('Test 7', e)
			self.label_frequ.setText(getLabelTitle(self.xIndex, 0, xPos))
			self.label_voltage.setText(getLabelTitle(self.yIndex, 1, yPos))
			self.updateRoiPlot()
		else:
			self.specROI.setPos(self.LastAcceptedRoiX, self.LastAcceptedRoiY)

	def update_intROIplot(self):
		if self.dimension > 1:
			self.IntRoiLineData = self.intROI.getArrayRegion(self.intensity_image, self.image)
			self.RoiIntPlot.clear()
			self.infLinePos.hide()
			self.IntRoixData = np.arange(len(self.IntRoiLineData))
			self.RoiIntPlot.plot(self.IntRoixData, self.IntRoiLineData)
		else:
			self.RoiIntPlot.clear()
			if self.nrXaxis > 1:
				self.IntRoixData = self.xAxis
				self.IntRoiLineData = self.intensity_image[:,0]
			else:
				self.IntRoixData = self.yAxis
				self.IntRoiLineData = self.intensity_image[0]
			self.lowPos = self.IntRoixData[0]
			self.highPos = self.IntRoixData[-1]
			self.RoiIntPlot.plot(self.IntRoixData, self.IntRoiLineData)
			self.RoiIntPlot.addItem(self.infLinePos)
			self.infLinePos.show()
			self.RoiIntPlot.setXRange(min(self.IntRoixData), max(self.IntRoixData))
			self.RoiIntPlot.setYRange(min(self.IntRoiLineData), max(self.IntRoiLineData))
			if self.multipleMeasBox.isChecked():
				for i in range(len(self.xSets)):
					try:
						if self.nrXaxis > 1:
							IntRoixData = self.xSets[i]
							IntRoiLineData = self.intensityImages[i][:,0]
						else:
							IntRoixData = self.ySets[i]
							IntRoiLineData = self.intensityImages[i][0]
						self.RoiIntPlot.plot(IntRoixData, IntRoiLineData, pen=pg.mkPen(width=1, color=self.colors[i+1], style=QtCore.Qt.SolidLine))
					except Exception as e:
						print('Test 8', e)

	def getIntensityData(self, data):
		intensity_list = []
		wavelengths = self.relevantData[0][2].spectrum[:, 0]
		idxLo = np.argmin(np.abs(np.array(wavelengths) - self.lambdaStart))
		idxHi = np.argmin(np.abs(np.array(wavelengths) - self.lambdaEnd))

		for i in range(0, np.shape(data)[0]):
			if self.radioButton_SubtractBg.isChecked():
				# new_y_list = []
				# x_start = data[i][2].spectrum[idxLo:idxHi, 0][0]
				# x_end = data[i][2].spectrum[idxLo:idxHi, 0][-1]
				# y_start = data[i][2].spectrum[idxLo:idxHi, 1][0]
				# y_end = data[i][2].spectrum[idxLo:idxHi, 1][-1]
				# m = (y_end - y_start) / (x_end - x_start)
				# for j in range(0, len(data[i][2].spectrum[idxLo:idxHi, 1])):
				# 	x = data[i][2].spectrum[idxLo:idxHi, 0][j]
				# 	y = data[i][2].spectrum[idxLo:idxHi, 1][j] - (x - x_start) * m - y_start
				# 	new_y_list.append(y)
				new_y_list = spectrumProcessing.subtractLinearBackground(data[i][2].spectrum, idxLo, idxHi)

				value = np.trapz(new_y_list[:,1], x=data[i][2].spectrum[idxLo:idxHi, 0])
			else:
				value = np.trapz(data[i][2].spectrum[idxLo:idxHi, 1], x=data[i][2].spectrum[idxLo:idxHi, 0])
			intensity_list.append(value)  # use first intensity value in each spectrum as test
		return np.asarray(intensity_list)

	def getRelevantData(self, data, sorter):
		chooserX = self.indexVar1 - 1
		if chooserX < 0:
			chooserX = 3
		relX = np.where(sorter[:,chooserX] == self.var1[self.activeVar1])
		relSpecX = data[relX]
		relSortX = sorter[relX]

		chooserY = self.indexVar2 - 1
		if chooserY < 0:
			chooserY = 3
		relY = np.where(relSortX[:,chooserY] == self.var2[self.activeVar2])
		relevantSorter = relSortX[relY]
		relevantData = relSpecX[relY]

		xAx = self.xIndex - 1
		if xAx < 0:
			xAx = 3
		yAx = self.yIndex - 1
		if yAx < 0:
			yAx = 3
		ziplist = zip(list(relevantSorter), list(relevantData))
		relevantData = [x for _,x in sorted(ziplist, key=lambda x: (x[0][xAx], x[0][yAx]))]
		# try:
		# 	self.intensity_image = np.reshape(intensity_array[:self.nrXaxis*(self.nrYaxis-1)], (self.nrXaxis, (self.nrYaxis-1)))
		# except Exception as e2:
		return relevantData, relevantSorter

	def wavelengthImage(self):
		if len(self.activeMeasList) < 1:
			return
		if self.ignoreUpdate:
			return
		self.activeVar1 = self.comboBoxVar1.currentIndex()
		self.activeVar2 = self.comboBoxVar2.currentIndex()
		if self.activeVar1 < 0 or self.activeVar2 < 0:
			return
		self.relDataSets = []
		self.relSorterSets = []
		for i, dataSet in enumerate(self.activeDatas):
			try:
				dat, sort = self.getRelevantData(dataSet, self.activeSorters[i])
				self.relDataSets.append(dat)
				self.relSorterSets.append(sort)
			except Exception as e:
				print('Test 9', e)
		im = []
		for d in self.relevantData:
			im.append(d[2].spectrum[:, 1])
		self.intensity_image = np.asarray(im)
		try:
			self.image.setImage(self.intensity_image)
			self.hist.setImageItem(self.image)

			mean = self.intensity_image.mean()
			self.iso.setLevel(mean)
			self.isoLine.setValue(mean)
			self.specROImoved()
			self.updateRoiPlot()
			self.updateIsocurve()
			self.update_intROIplot()
			if self.dimension < 2:
				self.ImPlot.hide()
				self.hist.hide()
				self.checkBox_intROI.setChecked(True)
			else:
				self.ImPlot.show()
				self.hist.show()
		except Exception as e:
			print('Test 10', e)


	def updateImage(self):
		if len(self.activeMeasList) < 1:
			return
		if self.ignoreUpdate:
			return
		self.activeVar1 = self.comboBoxVar1.currentIndex()
		self.activeVar2 = self.comboBoxVar2.currentIndex()
		if self.activeVar1 < 0 or self.activeVar2 < 0:
			return
		print("self.activeVar1 " + str(self.activeVar1))

		self.relevantData, self.relevantSorter = self.getRelevantData(self.data, self.sorter)

		if self.dimension < 2:
			self.relDataSets = []
			self.relSorterSets = []
			for i, dataSet in enumerate(self.activeDatas):
				try:
					dat, sort = self.getRelevantData(dataSet, self.activeSorters[i])
					self.relDataSets.append(dat)
					self.relSorterSets.append(sort)
				except Exception as e:
					print('Test 11', e)
		# chooserX = self.indexVar1 - 1
		# if chooserX < 0:
		# 	chooserX = 3
		# relX = np.where(self.sorter[:,chooserX] == self.var1[self.activeVar1])
		# relSpecX = self.data[relX]
		# relSortX = self.sorter[relX]
		#
		# chooserY = self.indexVar2 - 1
		# if chooserY < 0:
		# 	chooserY = 3
		# relY = np.where(relSortX[:,chooserY] == self.var2[self.activeVar2])
		# self.relevantSorter = relSortX[relY]
		# self.relevantData = relSpecX[relY]
		#
		# xAx = self.xIndex - 1
		# if xAx < 0:
		# 	xAx = 3
		# yAx = self.yIndex - 1
		# if yAx < 0:
		# 	yAx = 3
		# ziplist = zip(list(self.relevantSorter), list(self.relevantData))
		# self.relevantData = [x for _,x in sorted(ziplist, key=lambda x: (x[0][xAx], x[0][yAx]))]
		#
		# print("shapeData %0.1f" % np.shape(self.relevantData)[0])

		# intensity_list = []
		# wavelengths = self.relevantData[0][2].spectrum[:, 0]
		# idxLo = np.argmin(np.abs(np.array(wavelengths) - self.lambdaStart))
		# idxHi = np.argmin(np.abs(np.array(wavelengths) - self.lambdaEnd))
		#
		# for i in range(0, np.shape(self.relevantData)[0]):
		# 	if self.radioButton_SubtractBg.isChecked():
		# 		new_y_list = []
		# 		x_start = self.relevantData[i][2].spectrum[idxLo:idxHi, 0][0]
		# 		x_end = self.relevantData[i][2].spectrum[idxLo:idxHi, 0][-1]
		# 		y_start = self.relevantData[i][2].spectrum[idxLo:idxHi, 1][0]
		# 		y_end = self.relevantData[i][2].spectrum[idxLo:idxHi, 1][-1]
		# 		m = (y_end - y_start) / (x_end - x_start)
		# 		for j in range(0, len(self.relevantData[i][2].spectrum[idxLo:idxHi, 1])):
		# 			x = self.relevantData[i][2].spectrum[idxLo:idxHi, 0][j]
		# 			y = self.relevantData[i][2].spectrum[idxLo:idxHi, 1][j] - (x - x_start) * m - y_start
		# 			new_y_list.append(y)
		#
		# 		value = np.trapz(new_y_list, x=self.relevantData[i][2].spectrum[idxLo:idxHi, 0])
		# 	else:
		# 		value = np.trapz(self.relevantData[i][2].spectrum[idxLo:idxHi, 1], x=self.relevantData[i][2].spectrum[idxLo:idxHi, 0])
		# 	intensity_list.append(value)  # use first intensity value in each spectrum as test


		intensity_array = self.getIntensityData(self.relevantData)
		try:
			self.intensity_image = np.reshape(intensity_array, (self.nrXaxis, self.nrYaxis))
		except Exception as e:
			print("RESHAPE ERROR, Dimension Mismatch!!")
			print('Test 2', e)
		if self.dimension < 2:
			self.intensityImages = []
			for i in range(len(self.xSets)):
				try:
					intensity_array = self.getIntensityData(self.relDataSets[i])
					self.intensityImages.append(np.reshape(intensity_array, (self.xNrSets[i], self.yNrSets[i])))
				except Exception as e:
					print('Test 3', e)
		try:
			self.image.setImage(self.intensity_image)
			self.hist.setImageItem(self.image)

			mean = self.intensity_image.mean()
			self.iso.setLevel(mean)
			self.isoLine.setValue(mean)
			self.specROImoved()
			self.updateRoiPlot()
			self.updateIsocurve()
			self.update_intROIplot()
			if self.dimension < 2:
				self.ImPlot.hide()
				self.hist.hide()
				self.checkBox_intROI.setChecked(True)
			else:
				self.ImPlot.show()
				self.hist.show()
		except Exception as e:
			print('Test 1', e)


	def updateIsocurve(self):
		if self.checkBox_iso.isChecked():
			self.iso.setData(self.intensity_image)
			self.iso.setLevel(self.isoLine.value())
			self.iso.show()
		else:
			self.iso.hide()

	def updateRoiPlot(self):
		self.RoiPlot.clear()
		self.RoiPlot.addItem(self.infLineHi)
		self.RoiPlot.addItem(self.infLineLo)
		wavelength = list(self.relevantData[self.activeSpecNr][2].spectrum[:, 0])
		counts = list(self.relevantData[self.activeSpecNr][2].spectrum[:, 1])
		if self.radioButtonWavelength.isChecked():
			x = wavelength
		elif self.radioButtonEnergy.isChecked():
			x = 1239.841857 / np.array(wavelength)
		else:
			laserWave = float(self.imagerLaserWaveLine.text())
			x = (1/laserWave - 1/np.array(wavelength)) * 1e7
		self.RoiPlot.plot(x, counts)
		if self.multipleMeasBox.isChecked():
			for i, nr in enumerate(self.activeSpecNumbers):
				try:
					wavelength = list(self.relDataSets[i][nr][2].spectrum[:, 0])
					if self.radioButtonWavelength.isChecked():
						x = wavelength
					elif self.radioButtonEnergy.isChecked():
						x = 1239.841857 / np.array(wavelength)
					else:
						laserWave = float(self.imagerLaserWaveLine.text())
						x = (1/laserWave - 1/np.array(wavelength)) * 1e7
					counts = list(self.relDataSets[i][nr][2].spectrum[:, 1])
					self.RoiPlot.plot(x, counts, pen=pg.mkPen(width=1, color=self.colors[i+1], style=QtCore.Qt.SolidLine))
				except Exception as e:
					print('Test 4', e)

	def updateWavelengths(self):
		try:
			start = float(self.lineEdit_lambdaStart.text())
			end = float(self.lineEdit_lambdaEnd.text())

			if (start >= self.lambda_min) and (start <= self.lambda_max) and (start < end):
				self.lambdaStart = start
			else:
				self.lambdaStart = self.lambda_min
			# self.lineEdit_lambdaStart.setText(str('%.2f'%self.lambda_min))

			if (end > self.lambda_min) and (end < self.lambda_max) and (start < end):
				self.lambdaEnd = end
			else:
				self.lambdaEnd = self.lambda_max
			# self.lineEdit_lambdaEnd.setText(str('%.2f'%self.lambda_max))

		except:
			self.lambdaStart = self.lambda_min
			self.lambdaEnd = self.lambda_max

		try:
			self.lineEdit_lambdaStart.setText(str('%.2f' % self.lambdaStart))
			self.lineEdit_lambdaEnd.setText(str('%.2f' % self.lambdaEnd))
			if self.radioButtonWavelength.isChecked():
				self.infLineLo.setValue(self.lambdaStart)
				self.infLineHi.setValue(self.lambdaEnd)
			elif self.radioButtonEnergy.isChecked():
				self.infLineLo.setValue(1239.841857 / self.lambdaEnd)
				self.infLineHi.setValue(1239.841857 / self.lambdaStart)
			else:
				laserWave = float(self.imagerLaserWaveLine.text())
				self.infLineLo.setValue((1/laserWave - 1/self.lambdaStart) * 1e7)
				self.infLineHi.setValue((1/laserWave - 1/self.lambdaEnd) * 1e7)
			self.updateImage()
		except Exception as e:
			print('Test 5', e)