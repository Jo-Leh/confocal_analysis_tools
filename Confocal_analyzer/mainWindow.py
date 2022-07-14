# created 20-08-2019 by Johannes Lehmeyer
# note: based on Confocalizer and Spectral Imager by Maximilian Rühl

import numpy as np
import PyQt5
import pyqtgraph as pg

import sys
import os
import json

import operator
sys.path.append(os.path.dirname(os.getcwd()))

from PyQt5 import QtCore, QtGui, QtWidgets

from GUI.analyzer import Ui_MainWindow
from utility.ANDOR_SIF_READER import ANDOR_SIF_Spectrum
from utility.exception_hook import exception_hook
from imager_Subclass import ImagerWindow
from utility.simaging.spectrumseries import SpectrumSeries
from utility.measurement_class import MeasurementClass, OdmrMeasurement
from utility.dltsTools.dltsMeasClass import OD_DLTS_Transient
from utility import spectrumProcessing, savePicture_matplot
import utility.odmr_tools.recognizeLAPMeasFile as loadLAP

def getColor(text):
	if text.startswith('('):
		return eval(text)
	else:
		return text

def addToBox(name, box):
	active = box.count()
	box.addItem(name)
	box.setCurrentIndex(active)

def makeSpectrum(listSpectrum):
	return np.asarray([(x,y) for x,y in zip(listSpectrum.wavelength, listSpectrum.spectrum)])

def tableStandard(table, labels):
	table.setColumnCount(len(labels))
	table.setHorizontalHeaderLabels(labels)
	table.verticalHeader().setDefaultSectionSize(40)
	table.verticalHeader().hide()
	table.resizeColumnsToContents()

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


class DragDropGraphicView(pg.GraphicsLayoutWidget):
	dropped = QtCore.pyqtSignal(list)

	def __init__(self, type, parent=None):
		super(DragDropGraphicView, self).__init__(parent)
		self.setAcceptDrops(True)

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
			links = []
			for url in event.mimeData().urls():
				links.append(str(url.toLocalFile()))
			self.dropped.emit(links)
		else:
			event.ignore()

class Analyzer(QtWidgets.QMainWindow, Ui_MainWindow):
	"""Main Class for the UI"""
	progressSignal = QtCore.pyqtSignal(int)

	def __init__(self):
		super(Analyzer, self).__init__()
		self.setupUi(self)

		self.colors = ['w', 'r', (0, 100, 255), 'g', 'c', 'm', 'y']  # for black bg
		self.pen = pg.mkPen(width=1, color='r')
		self.setWindowTitle("CMMA (Confocal Microscope - Multiple Analysis) - - - imager")

		# lists
		self.loaded_spectra_list = []
		self.plot_item_list_spectra = []
		self.plot_item_list_fits = []
		self.plot_item_list_ints = []
		self.plot_item_list_bgs = []
		self.spectra_name_list = []
		self.spectra_label_list = []

		self.scale_spectra_list = []
		self.offset_y_spectra_list = []
		self.offset_x_spectra_list = []

		self.fit_result_lambda_c = []
		self.fit_result_sigma = []
		self.fit_result_amp = []
		self.fit_result_c = []
		self.fit_result_m = []
		self.fit_result_quad = []

		self.color_list = []

		# infinity Lines
		self.infLineLo = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.infLineHi = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.infLineVert = pg.InfiniteLine(pos=None, angle=0, pen='r', movable=True)

		self.infLineLo.sigPositionChangeFinished.connect(self.infLinePosChanged)
		self.infLineHi.sigPositionChangeFinished.connect(self.infLinePosChanged)
		self.infLineVert.sigPositionChangeFinished.connect(self.infLinePosChanged)

		# line edit
		self.confMeasList.cellChanged.connect(self.confMeasChanged)
		self.confLoading = False

		self.lineEdit_from_nm.returnPressed.connect(self.changeInfLinePos)
		self.lineEdit_to_nm.returnPressed.connect(self.changeInfLinePos)
		self.lineEdit_guess_c.returnPressed.connect(self.changeInfLinePos)
		self.lineEdit_intensity_from.returnPressed.connect(self.changeInfLinePosIntegrate)
		self.lineEdit_intensity_to.returnPressed.connect(self.changeInfLinePosIntegrate)
		self.lineEdit_bgConstOffset.returnPressed.connect(self.changeInfLinePosIntegrate)

		# actions
		self.actionQuit.triggered.connect(self.closeEvent)
		self.actionLoad_imager_Data.triggered.connect(self.load_imager)
		self.actionAdd_Spectrum.triggered.connect(self.add_spectrum)
		self.actionLoad_ODMR_Data.triggered.connect(self.load_odmr)
		self.actionLoad_Other_Data.triggered.connect(self.addMiscFile)
		self.actionLoad_Temp.triggered.connect(self.loadTemp)
		self.actionSave_Temp.triggered.connect(self.saveTemp)

		# buttons
		self.pushButton_Remove_Spectrum.clicked.connect(self.remove_spectrum)
		self.pushButton_Add_Spectrum.clicked.connect(self.add_spectrum)
		self.addimagerButton.clicked.connect(self.load_imager)
		self.pushButton_save.clicked.connect(self.save_spectrum)
		self.pushButton_run_fit.clicked.connect(self.run_fit)
		self.pushButton_remove_fit.clicked.connect(self.remove_fit)
		self.pushButton_integrate.clicked.connect(self.integrate_spectrum)
		self.pushButton_saveFitData.clicked.connect(self.saveFitData)


		# comboboxes
		self.confMeasList.itemSelectionChanged.connect(self.labelPeaks)
		tableStandard(self.confMeasList, ['label', 'plot?', 'color', 'shift nm', 'shift counts', 'scale', 'file'])
		# self.comboBox_Active_Spectrum.currentIndexChanged.connect(self.combo_active_spectrum_changed)
		self.confFitList.itemSelectionChanged.connect(self.combo_active_fit_changed)
		self.confFitList.cellChanged.connect(self.confFitChanged)
		tableStandard(self.confFitList, ['name', 'plot?', 'color', 'ass. file'])
		# self.comboBox_active_fit.currentIndexChanged.connect(self.combo_active_fit_changed)
		tableStandard(self.confLineList, ['name', 'plot?', 'color', 'pos nm', 'pos eV', 'pos cm-1'])
		self.confLineList.cellChanged.connect(self.confLineChanged)

		tableStandard(self.confIntList, ['result', 'plot?', 'color', 'start', 'stop', 'name', 'ass. file'])
		self.confIntList.cellChanged.connect(self.confIntChanged)
		self.pushButton_remove_integrate.clicked.connect(self.removeIntegration)

		self.infLineMarkersLabelList = []
		self.infLineList = []
		self.pushButton_Add_Marker.clicked.connect(self.addMarker)
		self.pushButton_Remove_Marker.clicked.connect(self.removeMarker)
		self.markerAdding = False

		# radioboxes
		self.radioButton_gaussian.setChecked(True)
		self.radioButton_wavelength.setChecked(True)
		self.radioButton_bg_constant.setChecked(True)
		# checkboxes
		self.checkBox_vertLines.stateChanged.connect(self.checkBox_vertLinesStateChanged)
		self.checkBox_vertLines.setChecked(False)

		# radiobuttons
		self.radioButton_bg_constant.toggled.connect(self.radio_btn_bg_toggled)
		self.radioButton_bg_linear.toggled.connect(self.radio_btn_bg_toggled)
		self.radioButton_bg_quad.toggled.connect(self.radio_btn_bg_toggled)
		self.radioButton_wavelength.toggled.connect(self.radio_btn_abscissa_toggled)
		self.radioButton_photonEnergy.toggled.connect(self.radio_btn_abscissa_toggled)
		self.radioButton_raman.toggled.connect(self.radio_btn_abscissa_toggled)

		# disable elements first
		self.disable_confocalizer_elements()

		# plot specific
		self.legend = pg.LegendItem()

		self.graphicsView = DragDropGraphicView(self)
		self.Confocalizer.layout().addWidget(self.graphicsView, 0, 2, 4, 1)
		self.graphicsView.dropped.connect(self.fileDropped)
		self.plot_item = self.graphicsView.addPlot()
		self.legend.setParentItem(self.plot_item)

		self.checkBox_vertLinesStateChanged()

		# frontpanel handlers

		self.actionConfocalizer.triggered.connect(self.switchConfocal)
		self.actionimager.triggered.connect(self.switchimager)
		self.actionODMR.triggered.connect(self.switchODMR)
		self.actionOther.triggered.connect(self.switchOther)
		self.actionDLTS.triggered.connect(self.switchDLTS)

		# self.loadFolder = 'C:/Users/od93yces/Data'
		self.loadFolder = 'E:/Data'
		self.saveFolder = 'E:/Data/analyses'

		self.switchimager()

		self.activeMeasMenu = QtWidgets.QMenu(self.activeMeasurementsButton)
		self.activeMeasurementsButton.setMenu(self.activeMeasMenu)
		self.activeMeasurementsButton.setDisabled(True)
		self.activeMeasList = []
		self.imager_GrWin = DragDropGraphicView(self)
		self.imager_GrWin.dropped.connect(self.fileDropped)
		self.Imager.layout().addWidget(self.imager_GrWin, 0, 2, 6, 1)
		imagerKwargs = {'GrWin': self.imager_GrWin,
			'pushButtonSaveIntRoi': self.pushButtonSaveIntRoi_imager,
			'lineLambda': [self.lambdaStart_imager, self.lambdaEnd_imager],
			'radioButton_fullBg': self.radioFullBg_imager,
			'radioButton_SubtractBg': self.radioSubBg_imager,
			'checkBox_iso': self.checkBox_iso_imager,
			'checkBox_intROI': self.checkBox_intROI_imager,
			'groupBox_options': self.groupBox_options_2,
			'labels': [self.label_frequ, self.label_voltage, self.label_var1, self.label_var2, self.label_var3, self.label_var4],
			'removeimagerButton': self.removeimagerButton,
			'comboBoximagerSelection': self.comboBoximagerSelection,
			'varCombos': [self.comboBoxVar1, self.comboBoxVar2, self.comboBoxVar3, self.comboBoxVar4],
			'axCombos': [self.comboBoxXaxis, self.comboBoxYaxis],
			'activeMeasurementsButton': self.activeMeasurementsButton,
			'abscissaButtons': [self.radioButtonWavelength, self.radioButtonEnergy, self.radioButtonRamanImg, self.imagerLaserWaveLine],
			'activeMeasMenu': self.activeMeasMenu,
			'activeMeasList': self.activeMeasList,
			'multipleMeasBox': self.multipleMeasBox}
		self.imager = ImagerWindow(**imagerKwargs)

		# saving / loading
		self.loadedSpecs = []
		self.loadedFolders = []
		self.panel = 1
		try:
			with open('userdata/preferences.json', 'r') as pref:
				self.preferences = json.load(pref)
		except Exception as e:
			print(e)
			self.preferences = {"closeMessage": True, "autosave": True, "saveQuestion": True}
		self.actionMessage_when_closing.setChecked(self.preferences['closeMessage'])
		self.actionMessage_when_closing.changed.connect(self.preferencesChanged)
		self.actionAutosave_on_Close.setChecked(self.preferences['autosave'])
		self.actionAutosave_on_Close.changed.connect(self.preferencesChanged)
		if self.preferences['autosave']:
			self.actionAsk_for_Save_on_Close.setChecked(False)
			self.actionAsk_for_Save_on_Close.setDisabled(True)
		else:
			self.actionAsk_for_Save_on_Close.setChecked(self.preferences['saveQuestion'])
			self.actionAsk_for_Save_on_Close.setEnabled(True)
		self.actionAsk_for_Save_on_Close.changed.connect(self.preferencesChanged)

		self.peakLabels = []
		self.checkBoxPeakLabeling.stateChanged.connect(self.labelPeaks)
		self.numberOfPeakLabels.textChanged.connect(self.labelPeaks)

		self.setAcceptDrops(True)
		self.graphicsView_odmr = DragDropGraphicView(self)
		self.ODMR.layout().addWidget(self.graphicsView_odmr, 0, 2, 10, 1)
		self.graphicsView_odmr.dropped.connect(self.fileDropped)

		self.odmr_data = []
		self.odmr_labels = []
		self.odmr_checks = []
		self.odmr_fits = []
		self.odmr_fitLabels = []
		self.odmr_fitChecks = []
		self.addOdmrButton.clicked.connect(self.load_odmr)
		self.removeOdmrButton.clicked.connect(self.removeOdmr)
		self.odmr_plot = self.graphicsView_odmr.addPlot()

		self.measurement_list.setColumnCount(6)
		self.measurement_list.setHorizontalHeaderLabels(['file', 'label', 'rate0', 'rate1', 'colour', 'dotted'])
		self.measurement_list.verticalHeader().setDefaultSectionSize(40)
		self.measurement_list.verticalHeader().hide()
		self.measurement_list.resizeColumnsToContents()
		self.measurement_list.cellChanged.connect(self.updateODMRPlot)

		self.fitTable_ODMR.setColumnCount(4)
		self.fitTable_ODMR.setHorizontalHeaderLabels(['ass. file', 'label', 'plot', 'colour'])
		self.fitTable_ODMR.verticalHeader().setDefaultSectionSize(40)
		self.fitTable_ODMR.verticalHeader().hide()
		self.fitTable_ODMR.resizeColumnsToContents()
		self.fitTable_ODMR.cellChanged.connect(self.updateODMRPlot)
		self.fitTable_ODMR.clicked.connect(self.changeActiveODMRFit)


		self.checkBox_average.clicked.connect(self.updateODMRPlot)
		self.checkBox_split_up_down.clicked.connect(self.updateODMRPlot)
		self.checkBox_average_APDs.clicked.connect(self.updateODMRPlot)
		self.checkBox_conv_Signal.clicked.connect(self.updateODMRPlot)
		self.checkBox_sweepwiseSignal.clicked.connect(self.updateODMRPlot)
		self.checkBox_overTimePlot.clicked.connect(self.updateODMRPlot)
		self.radioButton_showCountrates.setChecked(True)
		self.radioButton_showCountrates.toggled.connect(self.updateODMRPlot)
		self.radioButton_showRF.toggled.connect(self.updateODMRPlot)
		self.updateOdmrStop = False
		self.actionSave_Picture.triggered.connect(self.savePicture)

		self.calcFitButton_ODMR.clicked.connect(self.calcFitODMR)
		self.removeFitButton_ODMR.clicked.connect(self.removeFitODMR)


		lay = self.Simple.layout()
		widge = QtWidgets.QWidget()
		widge.setLayout(lay)
		self.Simple.setLayout(QtWidgets.QGridLayout())
		splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.Simple.layout().addWidget(splitter)
		splitter.addWidget(widge)
		self.graphicsViewSimple = DragDropGraphicView(self)
		splitter.addWidget(self.graphicsViewSimple)
		self.graphicsViewSimple.dropped.connect(self.fileDropped)
		self.simplePlot = self.graphicsViewSimple.addPlot()
		self.simplePlot.showAxis('right')
		self.simplePlotTwin = pg.ViewBox()
		self.simplePlot.scene().addItem(self.simplePlotTwin)
		self.simplePlot.getAxis('right').linkToView(self.simplePlotTwin)
		self.simplePlotTwin.setXLink(self.simplePlot)

		self.simpleAddData.clicked.connect(self.addMiscFile)
		self.simpleRemoveData.clicked.connect(self.removeMiscFile)
		tableStandard(self.simpleFileTable, ['label', 'plot?', 'colour', 'X', 'Y', 'axis', 'file'])
		self.simpleFileTable.verticalHeader().show()
		self.simpleFileTable.cellChanged.connect(self.simpleFileTableChanged)

		self.pushButtonSaveCalcData.clicked.connect(self.saveCalculatedData)

		tableStandard(self.simpleFitTable, ['name', 'plot?', 'colour', 'axis', 'ass. file'])
		axBox = QtWidgets.QComboBox()
		axBox.addItems([])
		tableAddRow(self.simpleFitTable, ['New Fit', False, 'w', axBox, 'None'], [0,1,2,3,4])
		# self.fitTable_ODMR.cellChanged.connect(self.updateODMRPlot)
		# self.fitTable_ODMR.clicked.connect(self.changeActiveODMRFit)
		tableStandard(self.simpleParameterTable, ['parameter', 'guess', 'fitvalue', 'error'])

		self.simpleFitTable.item(0,1).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
		self.simpleFitTable.item(0,0).setSelected(True)

		self.addParameterButton.clicked.connect(self.addParameter)
		self.removeParameterButton.clicked.connect(self.removeParameter)
		self.simpleRunFit.clicked.connect(self.runSimpleFit)
		self.simpleRemoveFit.clicked.connect(self.removeSimpleFit)
		self.simpleFitTable.itemSelectionChanged.connect(self.simpleFitSelectionChanged)
		self.simpleFitTable.cellChanged.connect(self.simpleFitTableChanged)

		self.simpleUpdateStop = True
		self.simpleData = []
		self.simplePlotData = []
		self.simplePlotFit = []
		self.simpleFitParameters = [{}]

		self.dltsPlotDataNumbers = []

		self.lineEditSimpleFitFunc.setPlaceholderText('enter your fit-function here')


		self.limLineLo = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.limLineHi = pg.InfiniteLine(pos=None, pen='r', movable=True)

		self.limLineLo.sigPositionChangeFinished.connect(self.limLinePosChanged)
		self.limLineHi.sigPositionChangeFinished.connect(self.limLinePosChanged)

		self.lineEditSimpleFrom.textChanged.connect(self.changeLimLinePos)
		self.lineEditSimpleTo.textChanged.connect(self.changeLimLinePos)

		self.checkBoxSimpleLimitLines.stateChanged.connect(self.simplePlotAll)


		#  DLTS --------------------------------------------

		lay = self.DLTS.layout()
		widge = QtWidgets.QWidget()
		widge.setLayout(lay)
		self.DLTS.setLayout(QtWidgets.QGridLayout())
		splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		self.DLTS.layout().addWidget(splitter)
		splitter.addWidget(widge)
		self.graphicsViewDLTS = DragDropGraphicView(self)
		splitter.addWidget(self.graphicsViewDLTS)
		self.graphicsViewDLTS.dropped.connect(self.fileDropped)
		self.dltsPlot = self.graphicsViewDLTS.addPlot()
		self.graphicsViewDLTS.nextRow()
		self.dltsDataPlot = self.graphicsViewDLTS.addPlot()

		self.addDLTSbutton.clicked.connect(self.addDLTSfile)
		self.removeDLTSbutton.clicked.connect(self.removeDLTSfile)
		self.dltsSaveDataButton.clicked.connect(self.saveDLTSdata)
		tableStandard(self.dltsFileTable, ['label', 'window', 'polyorder', 'plot raw', 'plot smooth', 'colour', 'file'])
		self.dltsFileTable.verticalHeader().show()
		self.dltsFileTable.cellChanged.connect(self.dltsFileTableChanged)
		self.dltsCorrTable.cellChanged.connect(self.dltsCorrTableChanged)

		tableStandard(self.dltsPackTable, ['name', 'plot?', 'path'])
		self.dltsPackTable.verticalHeader().show()
		self.dltsPackTable.clicked.connect(self.dltsPackTableClicked)

		# self.correlationFunctionComboBox.addItems(dltsFunctions.dltsMeasClass.correlationList)
		self.dltsUpdateStop = True
		tableStandard(self.dltsCorrTable, ['function', 'window', 'polyorder', 'plot raw', 'plot smooth', 'color', 'tau', 'maxRaw', 'maxSmooth'])
		for i, f in enumerate(dltsFunctions.dltsMeasClass.correlationList):
			tableAddRow(self.dltsCorrTable, [f, 15, 2, True, True, self.colors[i % len(self.colors)], 0, 0, 0])
		for i, f in enumerate(dltsFunctions.dltsMeasClass.correlationListBefore):
			tableAddRow(self.dltsCorrTable, [f, 15, 2, True, True, self.colors[i % len(self.colors)], 0, 0, 0])
		self.dltsUpdateStop = False
		self.calculateCorrelationButton.clicked.connect(self.calculateCorrelation)
		self.applySmoothingAllButton.clicked.connect(self.applySmoothing)

		self.plotAllRawButton.clicked.connect(self.plotAllRawDLTS)
		self.plotNoneRawButton.clicked.connect(self.plotNoneRawDLTS)
		self.plotAllSmoothButton.clicked.connect(self.plotAllSmoothDLTS)
		self.plotNoneSmoothButton.clicked.connect(self.plotNoneSmoothDLTS)
		self.plotAllCorrButton.clicked.connect(self.plotAllCorrDLTS)
		self.plotNoneCorrButton.clicked.connect(self.plotNoneCorrDLTS)
		self.plotAllCorrSmoothButton.clicked.connect(self.plotAllCorrSmoothDLTS)
		self.plotNoneCorrSmoothButton.clicked.connect(self.plotNoneCorrSmoothDLTS)


		self.dltsSaveSmoothedDataButton.clicked.connect(self.dltsSaveSmoothedData)
		self.dltsSaveCorrelationDataButton.clicked.connect(self.dltsSaveCorrelationData)

		self.dltsNormCorr.stateChanged.connect(self.dltsNormCorrStateChanged)

		self.startTrans_start.returnPressed.connect(self.changeTransLinePos)
		self.startTrans_stop.returnPressed.connect(self.changeTransLinePos)
		self.stopTrans_start.returnPressed.connect(self.changeTransLinePos)
		self.stopTrans_stop.returnPressed.connect(self.changeTransLinePos)

		self.binAvgLine.returnPressed.connect(self.applyBinning)

		self.startStartLine = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.startStopLine = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.stopStartLine = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.stopStopLine = pg.InfiniteLine(pos=None, pen='r', movable=True)
		self.startStartLabel = pg.InfLineLabel(line=self.startStartLine, text='before\nstart', movable=True, position=0.9)
		self.startStopLabel = pg.InfLineLabel(line=self.startStopLine, text='before\nstop', movable=True, position=0.9)
		self.stopStartLabel = pg.InfLineLabel(line=self.stopStartLine, text='after\nstart', movable=True, position=0.9)
		self.stopStopLabel = pg.InfLineLabel(line=self.stopStopLine, text='after\nstop', movable=True, position=0.9)

		self.startStartLine.sigPositionChangeFinished.connect(self.transLinePosChanged)
		self.startStopLine.sigPositionChangeFinished.connect(self.transLinePosChanged)
		self.stopStartLine.sigPositionChangeFinished.connect(self.transLinePosChanged)
		self.stopStopLine.sigPositionChangeFinished.connect(self.transLinePosChanged)
		self.startTransPointsLabel.returnPressed.connect(self.transientPointsChanged)
		self.stopTransPointsLabel.returnPressed.connect(self.transientPointsChanged)

		self.dltsVRbox.currentIndexChanged.connect(self.changeVoltages)

		self.dltsUpdateStop = True
		self.dltsData = []
		self.dltsDataPacks = []
		self.dltsPlotData = []
		self.dltsCorrelationData = []
		self.dltsCorrelationSmoothed = []

		self.dltsProgressBar = dltsFunctions.ProgressBar(self)
		lay.addWidget(self.dltsProgressBar)
		# self.switchODMR()
		# self.switchimager()
		# self.switchOther()
		self.switchDLTS()

		self.laserWave = 0
		self.laserWavelengthLine.returnPressed.connect(self.laserWaveChanged)
# ======================================================================================================
# ======================================================================================================
	# CONFOCALIZER
# ======================================================================================================
# ======================================================================================================


	def confMeasChanged(self, r, c):
		if self.confLoading is True:
			return
		self.confMeasList.resizeColumnToContents(c)
		if c in [3,4,5]:
			confocalizer.update_plot_scale_offset(self)
		elif c == 0:
			self.set_legend_name()
		elif c == 2:
			color = self.confMeasList.item(r, c).text()
			if color.startswith('('):
				self.color_list[r] = eval(color)
			else:
				self.color_list[r] = color
			self.add_spectra_to_plot_items()
			self.plot_all()
		elif c == 1:
			self.plot_all()

	def confFitChanged(self, r, c):
		self.confFitList.resizeColumnToContents(c)
		if c == 1:
			self.plot_all()
		if c == 2:
			self.plot_item_list_fits[r].setPen(pg.mkPen(width=2, color=getColor(self.confFitList.item(r, c).text()), style=QtCore.Qt.SolidLine))

	def confIntChanged(self, r, c):
		self.confIntList.resizeColumnToContents(c)
		if c == 1:
			self.plot_all()
		if c == 2:
			self.plot_item_list_ints[r].setPen(pg.mkPen(width=1, color=getColor(self.confIntList.item(r, c).text()), style=QtCore.Qt.DashLine))
			self.plot_item_list_bgs[r].setPen(pg.mkPen(width=1, color=getColor(self.confIntList.item(r, c).text()), style=QtCore.Qt.DashLine))

	def laserWaveChanged(self):
		for i in range(len(self.infLineList)):
			self.confLineChanged(i, 3)

	def confLineChanged(self, r, c):
		if self.markerAdding:
			return
		self.confLineList.resizeColumnToContents(c)
		if c == 1:
			self.plot_all()
		elif c == 2:
			self.infLineList[r].setPen(pg.mkPen(width=1, color=getColor(self.confLineList.item(r, c).text()), style=QtCore.Qt.SolidLine))
		elif c == 3:
			val = float(self.confLineList.item(r, c).text())
			self.markerAdding = True
			self.infLineList[r].setValue(val)
			self.confLineList.item(r, 4).setText('{:0.4f}'.format(confocalizer.eVfromNM(val)))
			try:
				self.laserWave = float(self.laserWavelengthLine.text())
				self.confLineList.item(r, 5).setText('{:0.4f}'.format((1/self.laserWave - 1/val) * 1e7))
			except Exception as e:
				print(e)
			self.markerAdding = False
		elif c == 4:
			val = confocalizer.nmFromeV(float(self.confLineList.item(r, c).text()))
			self.markerAdding = True
			self.infLineList[r].setValue(val)
			self.confLineList.item(r, 3).setText('{:0.4f}'.format(val))
			self.laserWave = 0
			try:
				self.laserWave = float(self.laserWavelengthLine.text())
				self.confLineList.item(r, 5).setText('{:0.4f}'.format((1/self.laserWave - 1/val) * 1e7))
			except Exception as e:
				print(e)
			self.markerAdding = False
		elif c == 5:
			self.laserWave = float(self.laserWavelengthLine.text())
			val = 1 / (1e-7 * float(self.confLineList.item(r, c).text()) + 1/self.laserWave)
			self.markerAdding = True
			self.infLineList[r].setValue(val)
			self.confLineList.item(r, 3).setText('{:0.4f}'.format(val))
			self.confLineList.item(r, 4).setText('{:0.4f}'.format(confocalizer.eVfromNM(val)))
			self.markerAdding = False



	def labelPeaks(self):
		"""tries to label a given number of highest peaks (#self.numberOfPeakLabels) via the spectral library module"""
		confocalizer.labelPeaks(self)

	def active_spectrum(self, multi=False):
		"""returns the index of the currently active spectrum"""
		indices = self.confMeasList.selectedIndexes()
		if multi:
			return indices
		if len(indices) == 0:
			return -1
		return indices[0].row()

	def active_fit(self, multi=False):
		"""returns the index of the currently active spectrum"""
		indices = self.confFitList.selectedIndexes()
		if multi:
			return indices
		if len(indices) == 0:
			return -1
		return indices[0].row()

	def addMarker(self):
		self.markerAdding = True
		i = self.confLineList.rowCount()
		marker = pg.InfiniteLine(pos=None, pen='y', movable=True)
		self.infLineList.append(marker)
		actMin, actMax = self.getActualLambdaMinMax()
		marker.setValue((actMin + actMax) / 2)
		marker.sigPositionChangeFinished.connect(self.markerMoved)
		marker.setObjectName('marker_{}'.format(i))
		val = marker.value()
		self.laserWave = 0
		try:
			self.laserWave = float(self.laserWavelengthLine.text())
		except Exception as e:
			print(e)
		if self.laserWave > 0:
			wavenumber = (1/self.laserWave - 1/val) * 1e7
			self.infLineMarkersLabelList.append(pg.InfLineLabel(line=marker, text='%.4f nm\n%.4f eV\n%.4f cm-1' % (val, confocalizer.eVfromNM(val), wavenumber), movable=True))
		else:
			self.infLineMarkersLabelList.append(pg.InfLineLabel(line=marker, text='%.4f nm\n%.4f eV' % (val, confocalizer.eVfromNM(val)), movable=True))
		tableAddRow(self.confLineList, [str(), True, 'y', '{:0.4f}'.format(val), '{:0.4f}'.format(confocalizer.eVfromNM(val)), 'NaN'])
		self.plot_all()
		self.markerAdding = False

	def removeIntegration(self):
		indices = self.confIntList.selectedIndexes()
		indices = sorted(indices, key=lambda x: x.row())
		if len(indices) == 0:
			return
		for index in indices[::-1]:
			i = index.row()
			self.confIntList.removeRow(i)
			self.plot_item_list_bgs.pop(i)
			self.plot_item_list_ints.pop(i)
		self.plot_all()

	def removeMarker(self):
		indices = self.confLineList.selectedIndexes()
		indices = sorted(indices, key=lambda x: x.row())
		if len(indices) == 0:
			return
		for index in indices[::-1]:
			i = index.row()
			self.confLineList.removeRow(i)
			self.infLineMarkersLabelList.pop(i)
			self.infLineList.pop(i)
		self.plot_all()

	def markerMoved(self):
		sender = self.sender()
		i = int(sender.objectName().split('_')[-1])
		marker = self.infLineList[i]
		label = self.infLineMarkersLabelList[i]
		val = marker.value()
		self.markerAdding = True
		self.confLineList.item(i, 3).setText('{:0.4f}'.format(val))
		self.confLineList.item(i, 4).setText('{:0.4f}'.format(confocalizer.eVfromNM(val)))
		self.laserWave = 0
		try:
			self.laserWave = float(self.laserWavelengthLine.text())
			waveN = (1/self.laserWave - 1/val) * 1e7
			self.confLineList.item(i, 5).setText('{:0.4f}'.format(waveN))
			label.setFormat('%.4f nm\n%.4f eV\n%.4f cm-1' % (val, confocalizer.eVfromNM(val), waveN))
		except Exception as e:
			print(e)
			label.setFormat('%.4f nm\n%.4f eV' % (val, confocalizer.eVfromNM(val)))
			self.confLineList.item(i, 5).setText('NaN')
		self.markerAdding = False

	def add_spectra_to_plot_items(self):
		"""scales the spectra according to given scales and offsets, then plots them"""
		confocalizer.add_spectra_to_plot_items(self)

	def add_spectrum(self):
		"""choose spectrum (-a) to load via file dialog"""
		files = QtGui.QFileDialog.getOpenFileNames(self, 'Select a file:', 'C:/Users/od93yces/Data', filter='*.sif;*.txt')[0]
		self.loadSpectrum(files)

	def loadSpectrum(self, files):
		"""load the given 'files' via the ANDOR_SIF_Spectrum handler
		updates the color, spectra, offset and scale lists
		enables elements, checks background choice and updates infinity-lines
		automatically plots all and switches to confocalizer-view"""
		self.switchConfocal()
		for singleFile in files:
			self.loaded_spectra_list.append(ANDOR_SIF_Spectrum.ANDOR_SIF_SPECTRUM(singleFile))
			if type(self.loaded_spectra_list[-1].get_propValueList()[0]) is str:
				self.spectra_name_list.append(self.loaded_spectra_list[-1].get_propValueList()[0])
			else:
				self.spectra_name_list.append(self.loaded_spectra_list[-1].get_propValueList()[0].decode('ISO-8859-1').split('\\')[-1])

			color = self.colors[len(self.color_list) % len(self.colors)]
			self.color_list.append(color)
			self.spectra_label_list.append(str(len(self.spectra_name_list)))
			self.confLoading = True
			tableAddRow(self.confMeasList, [singleFile.split('/')[-1], True, str(color), '0', '0', '1', singleFile])
			self.scale_spectra_list.append('1')
			self.confLoading = False
			self.offset_y_spectra_list.append('0')
			self.offset_x_spectra_list.append('0')

			self.enable_confocalizer_elements()
			self.radio_btn_bg_toggled()
			self.add_spectra_to_plot_items()
			self.infLinePosChanged()
			# self.combo_active_spectrum_changed()
		self.infLinePosChanged()
		self.plot_all()
		self.loadedSpecs.append(files)

	def changeInfLinePos(self):
		"""changes the position of the infinity-lines when the numbers are changed"""
		confocalizer.changeInfLinePos(self, 0)

	def changeInfLinePosIntegrate(self):
		"""changes the position of the infinity-lines when the numbers are changed"""
		confocalizer.changeInfLinePos(self, 1)

	def checkBox_vertLinesStateChanged(self):
		"""shows or hides the infinity-lines depending on the state of the checkbox"""
		confocalizer.checkBox_vertLinesStateChanged(self)

	def combo_active_fit_changed(self):
		"""switches the currently active fit to show the respective data"""
		confocalizer.combo_active_fit_changed(self)

	# def combo_active_spectrum_changed(self):
	# 	"""changes the active spectrum for editing and so on"""
	# 	confocalizer.combo_active_spectrum_changed(self)

	def disable_confocalizer_elements(self):
		"""disables most of the elements on the confocalizer-page"""
		self.tabWidget.setDisabled(True)
		self.pushButton_Remove_Spectrum.setDisabled(True)
		self.pushButton_save.setDisabled(True)

	def enable_confocalizer_elements(self):
		"""enables most of the elements on the confocalizer-page"""
		self.tabWidget.setEnabled(True)
		self.pushButton_Remove_Spectrum.setEnabled(True)
		self.pushButton_save.setEnabled(True)
		# self.label_legend_name.setEnabled(True)
		# self.lineEdit_lengend_name.setEnabled(True)

	def getActualLambdaMinMax(self):
		"""returns the min/max values for the wavelength including the applied shift"""
		return confocalizer.getActualLambdaMinMax(self)

	def getActualCountsMinMax(self):
		"""returns the min/max values for the wavelength including applied shift and scaling"""
		return confocalizer.getActualCountsMinMax(self)

	def infLinePosChanged(self):
		"""changes the numbers shown according to the actual position of the infinity-lines, the fit-center-guess is the middle between the lines
		if the lines are outside the range, they are set to the edges"""
		confocalizer.infLinePosChanged(self)

	def plot_all(self):
		"""utility (re-)plotting of infinity-lines, spectra and fits"""
		confocalizer.plot_all(self)

	def radio_btn_abscissa_toggled(self):
		self.add_spectra_to_plot_items()
		self.plot_all()

	def remove_fit(self):
		"""removes the currently selected fit"""
		confocalizer.remove_fit(self)

	def remove_legend_items(self):
		"""removes all entries from the plot-legend"""
		confocalizer.remove_legend_items(self)

	def remove_spectrum(self):
		"""removes the currently selected spectrum and all the information for it, then re-plots everything"""
		confocalizer.remove_spectrum(self)

	def saveFitData(self):
		"""saves all confocalizer fit-data via a file-dialog"""
		a = self.fit_result_lambda_c
		b = self.fit_result_sigma
		c = self.fit_result_amp
		d = self.fit_result_c
		e = self.fit_result_m

		filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Fit Data', self.loadFolder, '*.txt')[0]
		np.savetxt(filename, np.column_stack([range(len(a)), a, b, c, d, e]), delimiter='\t')

	def save_spectrum(self):
		"""saves the active (rescaled/shifted) spectrum via a file dialogue"""
		i = self.active_spectrum()
		scale = float(self.scale_spectra_list[i])
		offset_y = float(self.offset_y_spectra_list[i])
		offset_x = float(self.offset_x_spectra_list[i])
		x = np.array(self.loaded_spectra_list[i].get_wavelength()) + offset_x
		y = np.array(self.loaded_spectra_list[i].get_counts()) * scale + offset_y
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Save scaled spectrum', self.loadFolder, '*.txt')[0]
		np.savetxt(filename, np.column_stack([x, y]), delimiter='\t', fmt=['%1.4e', '%1.4e'], newline=os.linesep)

	def set_legend_name(self):
		"""sets the current name in the legend"""
		i = self.active_spectrum()
		name = self.confMeasList.item(i, 0).text()
		self.spectra_label_list[i] = name
		self.plot_all()

	# Calculating
	def get_alignment_param(self):
		"""utility, returning a list of scale, and offset (x and y) for the currently selected spectrum"""
		return confocalizer.get_alignment_param(self)

	def integrate_spectrum(self):
		"""if subtract background is checked, a linear background is subtracted from the integration
		integrates the shifted/scaled spectrum via the spectrumProcessing module
		plots the background and the integration"""
		a = float(self.lineEdit_intensity_from.text())
		b = float(self.lineEdit_intensity_to.text())
		i = self.active_spectrum()
		if i < 0:
			raise Exception('Need to select a spectrum first!')
		spectrum = makeSpectrum(self.loaded_spectra_list[i])

		start = np.argmin(np.abs(spectrum[:, 0] - a))
		stop = np.argmin(np.abs(spectrum[:, 0] - b))

		if self.radioButton_bgLin.isChecked():
			spectrum, bgData = spectrumProcessing.subtractLinearBackground(spectrum, start, stop, True)
			bg = bgData[3]
			x = bgData[2]
		else:
			offset = float(self.lineEdit_bgConstOffset.text())
			spectrum = spectrumProcessing.subtractConstantBackground(spectrum, start, stop, offset)
			x = spectrum[:,0]
			bg = np.full(len(x), offset)
		self.plot_item_list_bgs.append(pg.PlotCurveItem(x, bg, pen=pg.mkPen(width=1, color=self.color_list[i], style=QtCore.Qt.DashLine)))


		scale = float(self.scale_spectra_list[i])
		offset_x = float(self.offset_x_spectra_list[i])
		offset_y = float(self.offset_y_spectra_list[i])

		integral, x, y = spectrumProcessing.spectrumIntegration(spectrum, start, stop, offset_x, offset_y, scale, True)

		self.plot_item_list_ints.append(pg.PlotCurveItem(x, y, pen=pg.mkPen(width=1, color=self.color_list[i], style=QtCore.Qt.DashLine)))

		tableAddRow(self.confIntList, ['{:0.4f}'.format(integral), True, self.color_list[i], '{:0.4f}'.format(start), '{:0.4f}'.format(stop), str(self.confIntList.rowCount()), self.confMeasList.item(i, 6).text()], [0,3,4,6])
		self.plot_all()

	def run_fit(self):
		i = self.active_spectrum()
		if i < 0:
			raise Exception('Need to select a spectrum first!')

		scale, d_x, d_y = self.get_alignment_param()

		x_start = float(self.lineEdit_from_nm.text())
		x_end = float(self.lineEdit_to_nm.text())

		spectrum = makeSpectrum(self.loaded_spectra_list[i])
		start = np.argmin(np.abs(spectrum[:, 0] - x_start))
		stop = np.argmin(np.abs(spectrum[:, 0] - x_end))

		x = spectrum[start:stop,0] + d_x
		y = spectrum[start:stop,1] * scale + d_y

		if self.radioButton_gaussian.isChecked():
			peak_name = 'Gaussian'
		elif self.radioButton_lorentzian.isChecked():
			peak_name = 'Lorentzian'
		else:
			peak_name = 'Voigt'
		if self.radioButton_bg_constant.isChecked():
			background_name = 'Constant'
		elif self.radioButton_bg_linear.isChecked():
			background_name = 'Linear'
		else:
			background_name = 'Quadratic'

		# try:
		c = float(self.lineEdit_guess_c.text())
		m = q = np.nan
		if background_name == 'Linear' or background_name == 'Quadratic':
			m = float(self.lineEdit_guess_slope.text())
		if background_name == 'Quadratic':
			q = float(self.lineEdit_guess_quad.text())
		center = float(self.lineEdit_guess_center.text())
		sigma = float(self.lineEdit_guess_sigma.text())
		amp = float(self.lineEdit_guess_amp.text())
		peakVary = (not self.checkBox_fixed_lambda.isChecked(), not self.checkBox_fixed_sigma.isChecked(), not self.checkBox_fixed_amp.isChecked())
		bgVary = (not self.checkBox_fixed_c.isChecked(), not self.checkBox_fixed_m.isChecked(), not self.checkBox_fixed_quad.isChecked())
		# except Exception as e:
		# 	print(e)
		# 	return

		out, peakRes, bgRes = spectrumProcessing.peakFitting((x,y), peak_name, background_name, (center, sigma, amp), peakVary, (c,m,q), bgVary, True)

		print(out.fit_report(min_correl=0.25))

		self.label_fit_result_c.setText(str(bgRes[0]))
		self.label_fit_result_m.setText(str(bgRes[1]))
		self.label_fit_result_quad.setText(str(bgRes[2]))
		self.fit_result_c.append(bgRes[0])
		self.fit_result_m.append(bgRes[1])
		self.fit_result_quad.append(bgRes[2])


		self.label_fit_result_lambda.setText(str(peakRes[0]))
		self.label_fit_result_sigma.setText(str(peakRes[1]))
		self.label_fit_result_amp.setText(str(peakRes[2]))
		self.fit_result_lambda_c.append(peakRes[0])
		self.fit_result_sigma.append(peakRes[1])
		self.fit_result_amp.append(peakRes[2])

		self.plot_item_list_fits.append(pg.PlotCurveItem(x, out.best_fit, pen=pg.mkPen(width=2, color=self.colors[i], style=QtCore.Qt.SolidLine)))
		tableAddRow(self.confFitList, [peak_name + ' ' + background_name, True, self.confMeasList.item(i, 2).text(), self.confMeasList.item(i, 6).text()], [3])
		# addToBox('Spectrum [' + str(i + 1) + '] ' + peak_name + ' ' + background_name, self.comboBox_active_fit)
		self.combo_active_fit_changed()
		self.plot_all()

	def radio_btn_bg_toggled(self):
		"""changes the availability of input for fits, depending on the chosen background"""
		confocalizer.radio_btn_bg_toggled(self)

	# ======================================================================================================
# ======================================================================================================
	# IMAGER
# ======================================================================================================
# ======================================================================================================


	def load_imager(self):
		"""loads a measurement series for the imager panel, given by a file dialog"""
		directory = QtGui.QFileDialog.getExistingDirectory(self, "Select spectrum series directory", self.loadFolder)
		self.getLoadimager(directory)
		self.loadedFolders.append(directory)

	def getLoadimager(self, directory):
		"""loads the given 'directory' as a measurement series for the imager-panel"""
		self.switchimager()
		series = SpectrumSeries(directory)
		unsorted_data, var = series.get_spectra()
		if len(unsorted_data) == 0:
			return
		self.imager.noChange = True
		xFin = False
		for i, va in enumerate(var):
			if va > 1:
				if xFin:
					self.imager.comboBoxYaxis.setCurrentIndex(i)
					break
				else:
					self.imager.comboBoxXaxis.setCurrentIndex(i)
					xFin = True
		self.imager.noChange = False
		self.imager.data = np.asarray(sorted(unsorted_data, key=operator.itemgetter(1)))
		self.imager.dataSets.append(MeasurementClass(self.imager.data))
		if len(self.imager.dataSets) > 1:
			self.activeMeasurementsButton.setEnabled(True)
		sorter = []
		for d in self.imager.data:
			sorter.append(np.asarray(d[1]))
		self.imager.sorter = np.asarray(sorter)
		self.imager.sorterSets.append(self.imager.sorter)

		#########START
		xCoorsRed = []
		yCoorsRed = []
		zCoorsRed = []
		Volts = []
		Frequs = []
		Rots = []
		piezos = []

		for i in range(0, np.shape(self.imager.data)[0]):
			xCoorsRed.append(self.imager.data[i][1][1])
			yCoorsRed.append(self.imager.data[i][1][2])
			zCoorsRed.append(self.imager.data[i][1][4])
			Volts.append(self.imager.data[i][1][0])
			Frequs.append(self.imager.data[i][1][3])
			Rots.append(self.imager.data[i][1][5])
			piezos.append(self.imager.data[i][1][6])
		self.imager.xCoors = sorted(list(set(xCoorsRed)))
		self.imager.yCoors = sorted(list(set(yCoorsRed)))
		self.imager.zCoors = sorted(list(set(zCoorsRed)))
		self.imager.voltages = sorted(list(set(Volts)))
		self.imager.frequencies = sorted(list(set(Frequs)))
		self.imager.nrXpos = len(self.imager.xCoors)
		self.imager.nrYpos = len(self.imager.yCoors)
		self.imager.nrZpos = len(self.imager.zCoors)

		self.imager.nrVoltages = len(self.imager.voltages)
		self.imager.nrFrequencies = len(self.imager.frequencies)
		#########END
		self.imager.changeActiveMeas()
		# self.imager.changeVariables()


		self.imager.dimension = 2 if self.imager.nrFrequencies > 1 and self.imager.nrVoltages > 1 else 1

		self.imager.lambda_min = self.imager.data[0][2].spectrum[:, 0][0]
		self.imager.lambda_max = self.imager.data[0][2].spectrum[:, 0][-1]
		self.imager.lambdaStart = self.imager.lambda_min
		self.imager.lambdaEnd = self.imager.lambda_max

		self.comboBoxVar1.clear()
		for x in self.imager.xCoors:
			self.comboBoxVar1.addItem(str(x))
		self.comboBoxVar2.clear()
		for y in self.imager.yCoors:
			self.comboBoxVar2.addItem(str(y))
		self.comboBoxVar1.setCurrentIndex(0)
		self.comboBoxVar2.setCurrentIndex(0)
		self.imager.updateWavelengths()
		self.imager.updateImage()
		measname = os.path.basename(directory)
		addToBox(measname, self.comboBoximagerSelection)
		act = QtWidgets.QAction(measname, self.activeMeasMenu, checkable=True)
		act.changed.connect(self.imager.changeActiveMeas)
		self.activeMeasMenu.addAction(act)
		self.activeMeasList.append(act)
		act.setChecked(True)

		self.imager.changeVariables()

		self.groupBox_options_2.setEnabled(True)
		self.comboBoximagerSelection.setEnabled(True)
		self.removeimagerButton.setEnabled(True)
		self.comboBoxXaxis.setEnabled(True)
		self.comboBoxYaxis.setEnabled(True)
		self.loadFolder = os.path.dirname(directory)





# ======================================================================================================
# ======================================================================================================
	# ODMR
# ======================================================================================================
# ======================================================================================================


	def changeActiveODMRFit(self, index):
		odmr.activeFitChange(self, index)

	def updateODMRPlot(self):
		if self.updateOdmrStop:
			return
		if self.checkBox_conv_Signal.checkState():
			self.checkBox_sweepwiseSignal.setEnabled(True)
		else:
			self.checkBox_sweepwiseSignal.setEnabled(False)
		if self.checkBox_average.checkState():
			self.checkBox_split_up_down.setEnabled(True)
		else:
			self.checkBox_split_up_down.setEnabled(False)
			self.checkBox_split_up_down.setCheckState(False)
		odmr.updatePlotList(self)
		odmr.plotData(self)

	def removeFitODMR(self):
		odmr.removeFit(self)
		self.updateODMRPlot()

	def calcFitODMR(self):
		self.updateOdmrStop = True
		odmr.calcFit(self)
		self.updateOdmrStop = False
		self.updateODMRPlot()

	def load_odmr(self):
		"""loads the files given by dialog box into the ODMR interface"""
		files = QtGui.QFileDialog.getOpenFileNames(self, "Select ODMR measurement file(s)", self.loadFolder,
												   filter="*.txt")[0]
		self.getLoadOdmr(files)

	def saveDLTSdata(self):
		dltsFunctions.saveData(self)

	def changeVoltages(self):
		if not self.dltsUpdateStop:
			dltsFunctions.changeVoltages(self)

	def addDLTSfile(self):
		files = QtGui.QFileDialog.getOpenFileNames(self, "Select DLTS transient file(s)", self.loadFolder, filter="*.txt")[0]
		self.loadDLTSfile(files)

	def transLinePosChanged(self):
		dltsFunctions.transLinePosChanged(self)

	def changeTransLinePos(self):
		dltsFunctions.changeTransLinePos(self)

	def transientPointsChanged(self):
		dltsFunctions.transientPointsChanged(self)

	def calculateCorrelation(self):
		dltsFunctions.calculateCorrelation(self)

	def applySmoothing(self):
		dltsFunctions.applySmoothing(self)

	def applyBinning(self):
		dltsFunctions.applyBinning(self)

	def plotAllRawDLTS(self):
		dltsFunctions.plotAllRaw(self)

	def plotAllSmoothDLTS(self):
		dltsFunctions.plotAllSmooth(self)

	def plotNoneRawDLTS(self):
		dltsFunctions.plotNoneRaw(self)

	def plotNoneSmoothDLTS(self):
		dltsFunctions.plotNoneSmooth(self)

	def plotNoneCorrDLTS(self):
		dltsFunctions.plotNoneCorr(self)

	def plotAllCorrDLTS(self):
		dltsFunctions.plotAllCorr(self)

	def plotNoneCorrSmoothDLTS(self):
		dltsFunctions.plotNoneCorrSmooth(self)

	def plotAllCorrSmoothDLTS(self):
		dltsFunctions.plotAllCorrSmooth(self)

	def dltsSaveSmoothedData(self):
		dltsFunctions.dltsSaveSmoothedData(self)

	def dltsSaveCorrelationData(self):
		dltsFunctions.dltsSaveCorrelationData(self)

	def dltsNormCorrStateChanged(self):
		dltsFunctions.changeNormState(self)

	def loadDLTSfile(self, files):
		self.switchDLTS()
		try:
			files[0].endswith('.fdlts')
			dltsFunctions.loadFile(self, files[0])
		except Exception as e:
			print(e)
			self.thread = dltsFunctions.LoadWorker(files, self)
			self.thread.sig_step.connect(self.dltsProgressBar.signal_accept)
			self.dltsProgressBar.cancelSig.connect(self.thread._cancel)
			self.thread.start()
		# for i, file in enumerate(files):
		# 	data = OD_DLTS_Transient(file)
		# 	self.dltsData.append(data)
		# 	color = self.colors[self.dltsFileTable.rowCount() % len(self.colors)]
		# 	self.dltsUpdateStop = True
		# 	tableAddRow(self.dltsFileTable, [file.split('/')[-1], 51, 2, True, True, str(color), file], [3])
		# 	self.dltsUpdateStop = False
		# 	dltsFunctions.addDataToPlot(self, data)
		# 	self.progressSignal.emit(int((i+1)/n))
		# self.dltsProgressBar.cancel.setEnabled(False)
		# dltsFunctions.plot_all(self)

	def removeDLTSfile(self):
		dltsFunctions.removeFile(self)

	def dltsFileTableChanged(self, r, c):
		if self.dltsUpdateStop:
			return
		if c == 0:
			dltsFunctions.updateLegend(self, r)
		elif c in [3, 4]:
			dltsFunctions.plot_all(self)
		elif c == 5:
			color = getColor(self.dltsFileTable.item(r, c).text())
			pen = pg.mkPen(width=1, color=color)
			self.dltsPlotData[r].setPen(pen)
		elif c in [1,2]:
			dltsFunctions.resmooth(self)
		self.dltsFileTable.resizeColumnToContents(c)

	def dltsCorrTableChanged(self, r, c):
		if self.dltsUpdateStop:
			return
		if c in [1,2]:
			dltsFunctions.smoothCorrelation(self)
		elif c in [3,4,5]:
			dltsFunctions.plotCorr(self)

	def dltsPackTableClicked(self, index):
		dltsFunctions.dltsPackTableClicked(self, index)

	def getLoadOdmr(self, files):
		self.switchODMR()
		"""loads the 'files' as an OdmrMeasurement Class each"""
		for file in files:
			data = OdmrMeasurement(file)
			self.odmr_data.append(data)
			self.updateOdmrStop = True
			odmr.addToOdmrTable(self, file)
			self.updateOdmrStop = False
		odmr.updatePlotList(self)
		odmr.plotData(self)

	def removeOdmr(self):
		odmr.removeFromTable(self)
		odmr.updatePlotList(self)
		odmr.plotData(self)


# ======================================================================================================
# ======================================================================================================
	# MISC
# ======================================================================================================
# ======================================================================================================


	def savePicture(self):
		if self.panel == 2:
			savePicture_matplot.saveODMRpic(self)
			# plotData, plotColors, plotStyles = odmr.getSaveData(self)
			# picSaveBox = savePicture_matplot.SavePicture(plotData, plotColors, plotStyles=plotStyles, parent=self)
			# picSaveBox.exec()
		elif self.panel == 3:
			savePicture_matplot.saveMiscPic(self)
		elif self.panel == 0:
			savePicture_matplot.saveSpecPlot(self)
		elif self.panel == 1:
			savePicture_matplot.saveImager(self)
		elif self.panel == 4:
			savePicture_matplot.saveDLTSpic(self)

	# Handling Front, special
	def switchConfocal(self):
		"""switches to the confocalizer-page of the front-panel"""
		self.stackedWidget.setCurrentIndex(0)
		self.plot_all()
		self.setWindowTitle("FICOM - - - fiCom Confocalizer")
		self.panel = 0

	def switchimager(self):
		"""switches to the imager/scan/stuff-page of the front-panel"""
		self.stackedWidget.setCurrentIndex(1)
		self.setWindowTitle("FICOM - - - fIcom Imager")
		self.panel = 1

	def switchODMR(self):
		"""switches to the odmr-page of the front-panel"""
		self.stackedWidget.setCurrentIndex(2)
		self.setWindowTitle("FICOM - - - ficOm ODMR")
		self.panel = 2

	def switchDLTS(self):
		"""switches to the odmr-page of the front-panel"""
		self.stackedWidget.setCurrentIndex(4)
		self.setWindowTitle("FICOM - - - Ficom F-DLTS")
		self.panel = 4

	def switchOther(self):
		"""switches to the misc-page of the front-panel"""
		self.stackedWidget.setCurrentIndex(3)
		self.setWindowTitle("FICOM - - - ficoM Miscplot")
		self.panel = 3

	# User utility
	def preferencesChanged(self):
		"""adjusts the user options and saves them:
		'closeMessage': whether it should be asked before closing
		'autosave': automatically saves the state on closing
		'saveQuestion': if autosave is off, asks whether to save the state before closing"""
		self.preferences['closeMessage'] = self.actionMessage_when_closing.isChecked()
		check = self.preferences['autosave'] == self.actionAutosave_on_Close.isChecked()
		self.preferences['autosave'] = self.actionAutosave_on_Close.isChecked()
		if self.preferences['autosave']:
			self.actionAsk_for_Save_on_Close.setChecked(False)
			self.actionAsk_for_Save_on_Close.setDisabled(True)
		elif check:
			self.preferences['saveQuestion'] = self.actionAsk_for_Save_on_Close.isChecked()
		else:
			self.actionAsk_for_Save_on_Close.setChecked(self.preferences['saveQuestion'])
			self.actionAsk_for_Save_on_Close.setEnabled(True)
		with open('userdata/preferences.json', 'w') as pref:
			json.dump(self.preferences, pref)

	def saveTemp(self):
		"""saves the current state in a temporary file"""
		self.saveCurrentState('userdata/temp.npy')

	def saveCurrentState(self, filename):
		"""saves the current state in a given 'filename'"""
		saveArray = np.asarray([self.loadedSpecs, self.loadedFolders, self.panel])
		np.save(filename, saveArray, allow_pickle=True)

	def loadTemp(self):
		"""loads the state from a temporary file"""
		self.loadState('userdata/temp.npy')

	def loadState(self, filename):
		"""loads the state from given 'filename', includes so far:
		- the loaded spectra in the confocalizer
		- the loaded measurements for the imaging-window
		- the currently opened front-panel"""
		data = np.load(filename, allow_pickle=True)
		for f in data[0]:
			self.loadSpectrum(f)
			self.loadedSpecs.append(f)
		for f in data[1]:
			self.getLoadimager(f)
			self.loadedFolders.append(f)
		if data[2] == 1:
			self.switchimager()
		elif data[2] == 0:
			self.switchConfocal()
		else:
			self.switchODMR()

	def closeEvent(self, QCloseEvent, *args, **kwargs):
		if self.preferences['closeMessage']:
			choice = QtGui.QMessageBox.question(self, "Quit Program", "Sure you want to quit?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
			if choice == QtGui.QMessageBox.Yes:
				if self.preferences['autosave']:
					self.saveTemp()
				elif self.preferences['saveQuestion']:
					self.saveEvent()
				self.close()
			else:
				try:
					QCloseEvent.ignore()
				except:
					pass
		else:
			if self.preferences['autosave']:
				self.saveTemp()
			elif self.preferences['saveQuestion']:
				self.saveEvent()
			self.close()

	def saveEvent(self):
		choice = QtGui.QMessageBox.question(self, 'Save State?', 'Do you want to save the current state before closing?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
		if choice == QtGui.QMessageBox.Yes:
			self.saveCurrentState('userdata/temp.npy')

	def fileDropped(self, l):
		spec = False
		if l[0].endswith('.txt'):
			with open(l[0]) as file:
				info = file.readline()
			if info.startswith('# Exposure Time:'):
				spec = True
		if spec or l[0].endswith('.sif'):
			self.switchConfocal()
			self.loadSpectrum(l)
		elif 'OD-DLTS' in l[0] or 'DLTS' in l[0] or 'dlts' in l[0]:
			self.loadDLTSfile(l)
		elif not l[0][-4] == '.':
			self.switchimager()
			for folder in l:
				self.getLoadimager(folder)
		else:
			try:
				self.switchODMR()
				self.getLoadOdmr(l)
			except:
				self.switchOther()
				self.loadMiscFile(l)

	def addMiscFile(self):
		"""loads the files given by dialog box into the ODMR interface"""
		files = QtGui.QFileDialog.getOpenFileNames(self, "Select measurement file(s)", self.loadFolder)[0]
		self.loadMiscFile(files)

	def loadMiscFile(self, files):
		self.switchOther()
		for file in files:
			data = loadLAP.loadLAPFile(file)
			color = self.colors[self.simpleFileTable.rowCount() % len(self.colors)]
			self.simpleUpdateStop = True
			boxX, boxY = miscPlot.getXYBoxes(self, data)
			axBox = QtWidgets.QComboBox()
			axBox.addItems(['1', '2'])
			axBox.currentIndexChanged.connect(self.axisChanged)
			tableAddRow(self.simpleFileTable, [file.split('/')[-1], True, str(color), boxX, boxY, axBox, file], [6])
			self.simpleData.append(data)
			self.simpleUpdateStop = False
			miscPlot.addDataToPlot(self, data)
		miscPlot.plot_all(self)

	def removeMiscFile(self):
		miscPlot.removeFile(self)

	def simpleFileTableChanged(self, r, c):
		if self.simpleUpdateStop:
			return
		if c == 0:
			miscPlot.updateLegend(self)
		elif c == 1:
			miscPlot.plot_all(self)
		elif c == 2:
			color = getColor(self.simpleFileTable.item(r, c).text())
			pen = pg.mkPen(width=1, color=color)
			self.simplePlotData[r].setPen(pen)
		elif c in [3, 4, 5]:
			self.axisChanged(self)
		self.simpleFileTable.resizeColumnToContents(c)

	def axisChanged(self):
		miscPlot.axisChanged(self)
		miscPlot.plot_all(self)

	def calculateSimple(self):
		miscPlot.calculateSimple(self)

	def saveCalculatedData(self):
		miscPlot.saveCalculatedData(self)

	def updateViews(self):
		miscPlot.updateViews(self)

	def runSimpleFit(self):
		miscPlot.runSimpleFit(self)

	def removeSimpleFit(self):
		indices = miscPlot.activeFit(self, True)
		indices = sorted(indices, key=lambda x: x.row())
		for index in indices[::-1]:
			i = index.row()
			if i == 0:
				continue
			self.simpleFitTable.removeRow(i)
			self.simpleFitParameters.pop(i)
			self.simplePlotFit.pop(i-1)

	def addParameter(self):
		miscPlot.addFitParameter(self)

	def removeParameter(self):
		miscPlot.removeParameter(self)

	def simpleFitSelectionChanged(self):
		i = miscPlot.activeFit(self)
		if i == 0:
			self.addParameterButton.setEnabled(True)
			self.removeParameterButton.setEnabled(True)
		else:
			self.addParameterButton.setEnabled(False)
			self.removeParameterButton.setEnabled(False)
		self.updateSimpleFitParameters()

	def updateSimpleFitParameters(self):
		miscPlot.updateFitParams(self)

	def simpleFitTableChanged(self, r, c):
		if self.simpleUpdateStop:
			return
		if c == 0:
			miscPlot.updateLegend(self)
		elif c == 1:
			miscPlot.plot_all(self)
		elif c == 2:
			color = getColor(self.simpleFitTable.item(r, c).text())
			pen = pg.mkPen(width=1, color=color)
			self.simplePlotFit[r-1].setPen(pen)
		self.simpleFitTable.resizeColumnToContents(c)

	def limLinePosChanged(self):
		miscPlot.limLinePosChanged(self)

	def changeLimLinePos(self):
		miscPlot.changeLimLinePos(self)

	def simplePlotAll(self):
		miscPlot.plot_all(self)

	def simpleParameterTableChanged(self, r, c):
		if self.simpleUpdateStop:
			return
		if c == 1 and miscPlot.activeFit(self) == 0:
			self.simpleFitParameters[0][self.simpleParameterTable.item(r,0).text()][0] = float(self.simpleParameterTable.item(r,c).text())
		self.simpleParameterTable.resizeColumnToContents(c)





import confocalizer_functions as confocalizer
import odmr_functions as odmr
import miscPlot
import dltsFunctions

if __name__ == '__main__':
	sys.excepthook = exception_hook

	app = QtCore.QCoreApplication.instance()
	if app is None:
		app = QtWidgets.QApplication(sys.argv)
	ui = Analyzer()
	ui.show()
	ui.showMaximized()

	app.exec()