from PyQt5 import QtCore, QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import os
import numpy as np
from subprocess import call



from mainWindow import Analyzer


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


colorlist = ['w', 'r', '(0, 100, 255)', 'g', 'c', 'm', 'y']
stdColors = plt.rcParams['axes.prop_cycle'].by_key()['color']
figureRoot = r'C:\Users\od93yces\Documents\Figures'

def saveDLTSpic(gui:Analyzer):
	msg = QtWidgets.QMessageBox()
	msg.setIcon(QtWidgets.QMessageBox.Question)
	msg.setText('Transients or Spectra?')
	msg.setWindowTitle('which plot?')
	msg.setStandardButtons(QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No|QtWidgets.QMessageBox.Cancel)
	bY = msg.button(QtWidgets.QMessageBox.Yes)
	bY.setText('transients')
	bN = msg.button(QtWidgets.QMessageBox.No)
	bN.setText('spectra')
	msg.exec_()
	data = []
	lines = []
	if msg.clickedButton() == bY:
		plotLines = gui.dltsPlot.items
		for i in range(gui.dltsFileTable.rowCount()):
			label = gui.dltsFileTable.item(i, 0).text()
			col = gui.dltsFileTable.item(i, 5).text()
			if col in colorlist:
				col = stdColors[colorlist.index(col)]
			if gui.dltsFileTable.item(i, 3).checkState():
				data.append((label, col, '--'))
				lines.append((gui.dltsData[i].time, gui.dltsData[i].signal))
			if gui.dltsFileTable.item(i, 4).checkState():
				data.append((label, col, '-'))
				lines.append((gui.dltsData[i].time, gui.dltsData[i].smoothed))
		xRange = gui.dltsPlot.getAxis('bottom').range
		yRange = gui.dltsPlot.getAxis('left').range
		xlabel = 'time (s)'
		ylabel = 'signal'
	elif msg.clickedButton() == bN:
		for i in range(gui.dltsCorrTable.rowCount()):
			label = gui.dltsCorrTable.item(i, 0).text()
			col = gui.dltsCorrTable.item(i, 5).text()
			if col in colorlist:
				col = stdColors[colorlist.index(col)]
			if gui.dltsCorrTable.item(i, 3).checkState():
				data.append((label, col, '--'))
				lines.append((gui.dltsCorrelationData['temperature'], gui.dltsCorrelationData[label]))
			if gui.dltsCorrTable.item(i, 4).checkState():
				data.append((label, col, '-'))
				lines.append((gui.dltsCorrelationSmoothed['temperature'], gui.dltsCorrelationSmoothed[label].signal))
		xRange = gui.dltsDataPlot.getAxis('bottom').range
		yRange = gui.dltsDataPlot.getAxis('left').range
		xlabel = 'temperature (K)'
		ylabel = 'signal'
	dialogue = PictureEditDialogue(lines, data, ranges=[xRange, yRange], labels=[xlabel, ylabel])
	dialogue.exec()

def saveMiscPic(gui:Analyzer):
	plotLines = gui.simplePlot.items
	plotLinesRight = gui.simplePlotTwin.addedItems
	lines = []
	for l in plotLines:
		lines.append((l.xData, l.yData))
	twinLines = []
	for l in plotLinesRight:
		twinLines.append((l.xData, l.yData))
	data = []
	twinDat = []
	for i in range(gui.simpleFileTable.rowCount()):
		if not gui.simpleFileTable.item(i, 1).checkState():
			continue
		label = gui.simpleFileTable.item(i, 0).text()
		col = gui.simpleFileTable.item(i, 2).text()
		if col in colorlist:
			col = stdColors[colorlist.index(col)]
		if gui.simpleFileTable.cellWidget(i, 5).currentIndex() == 1:
			twinDat.append((label, col))
		else:
			data.append((label, col))
	xRange = gui.simplePlot.getAxis('bottom').range
	yRange = gui.simplePlot.getAxis('left').range
	twinRange = gui.simplePlot.getAxis('right').range
	dialogue = PictureEditDialogue(lines, data, twinLines, twinDat, ranges=[xRange, yRange, twinRange])
	dialogue.exec()

def saveODMRpic(gui:Analyzer):
	plotLines = gui.odmr_plot.items
	lines = []
	for l in plotLines:
		try:
			lines.append((l.xData, l.yData))
		except:
			xData = []
			yData = []
			for d in l.data:
				xData.append(d[0])
				yData.append(d[1])
			lines.append((xData, yData))
	data = []
	for i in range(gui.measurement_list.rowCount()):
		if gui.measurement_list.item(i, 2).checkState():
			label = gui.measurement_list.item(i, 1).text()
			col = gui.measurement_list.item(i, 4).text()
			if col in colorlist:
				col = stdColors[colorlist.index(col)]
			ls = 'o' if gui.measurement_list.item(i, 5).checkState() else '-'
			data.append((label, col, ls))
	xRange = gui.odmr_plot.getAxis('bottom').range
	yRange = gui.odmr_plot.getAxis('left').range
	dialogue = PictureEditDialogue(lines, data, ranges=[xRange, yRange], labels=['frequency (Hz)', 'signal'])
	dialogue.exec()

def saveSpecPlot(gui:Analyzer):
	plotLines = gui.plot_item.items
	lines = []
	data = []
	for l in plotLines:
		try:
			lines.append((l.xData, l.yData))
		except:
			try:
				xData = []
				yData = []
				for d in l.data:
					xData.append(d[0])
					yData.append(d[1])
				lines.append((xData, yData))
			except:
				try:
					if gui.checkBox_vertLines.checkState():
						lines.append(l.p)
						data.append([])
				except:
					pass
	for i in range(gui.confMeasList.rowCount()):
		if gui.confMeasList.item(i, 1).checkState():
			label = gui.confMeasList.item(i, 0).text()
			col = gui.confMeasList.item(i, 2).text()
			if col in colorlist:
				col = stdColors[colorlist.index(col)]
			data.append((label, col))
	xRange = gui.plot_item.getAxis('bottom').range
	yRange = gui.plot_item.getAxis('left').range
	dialogue = PictureEditDialogue(lines, data, ranges=[xRange, yRange], labels=['wavelength (nm)', 'signal'])
	dialogue.exec()

def saveImager(gui:Analyzer):
	plotLines = gui.imager.RoiPlot.items
	lines = []
	data = []
	for l in plotLines:
		try:
			lines.append((l.xData, l.yData))
		except:
			try:
				xData = []
				yData = []
				for d in l.data:
					xData.append(d[0])
					yData.append(d[1])
				lines.append((xData, yData))
			except:
				try:
					lines.append(l.p)
					data.append([])
				except:
					pass
	doc = QtGui.QTextDocument()
	doc.setHtml(gui.imager.label_frequ.text())
	x = doc.toPlainText()
	doc.setHtml(gui.imager.label_voltage.text())
	y = doc.toPlainText()

	label = '{} {}'.format(x, y)
	col = 'w'
	if col in colorlist:
		col = stdColors[colorlist.index(col)]
	data.append((label, col))
	xRange = gui.imager.RoiPlot.getAxis('bottom').range
	yRange = gui.imager.RoiPlot.getAxis('left').range
	dialogue = PictureEditDialogue(lines, data, ranges=[xRange, yRange])
	dialogue.exec()

	if gui.imager.checkBox_intROI.isChecked():
		plotLines = gui.imager.RoiIntPlot.items
		lines = []
		data = []
		for l in plotLines:
			try:
				lines.append((l.xData, l.yData))
			except:
				try:
					xData = []
					yData = []
					for d in l.data:
						xData.append(d[0])
						yData.append(d[1])
					lines.append((xData, yData))
				except:
					try:
						lines.append(l.p)
						data.append([])
					except:
						pass
		doc = QtGui.QTextDocument()
		doc.setHtml(gui.imager.label_frequ.text())
		x = doc.toPlainText()
		doc.setHtml(gui.imager.label_voltage.text())
		y = doc.toPlainText()

		label = '{} {}'.format(x, y)
		col = 'w'
		if col in colorlist:
			col = stdColors[colorlist.index(col)]
		data.append((label, col))
		xRange = gui.imager.RoiIntPlot.getAxis('bottom').range
		yRange = gui.imager.RoiIntPlot.getAxis('left').range
		dialogue = PictureEditDialogue(lines, data, ranges=[xRange, yRange])
		dialogue.exec()


class PictureEditDialogue(QtWidgets.QDialog):
	def __init__(self, plotData, data, twins=None, twinData=None, ranges=None, labels=None, parent=None, xlabel='', ylabel=''):
		super().__init__(parent)
		self.setLayout(QtWidgets.QGridLayout())
		self.table = QtWidgets.QTableWidget()
		tableStandard(self.table, ['label', 'color', 'linestyle'])
		self.layout().addWidget(self.table, 5, 0, 1, 4)
		self.xRangeLow = QtWidgets.QLineEdit('0')
		self.xRangeHi = QtWidgets.QLineEdit('0')
		self.yRangeLow = QtWidgets.QLineEdit('0')
		self.yRangeHi = QtWidgets.QLineEdit('0')
		self.twinRangeLow = QtWidgets.QLineEdit('0')
		self.twinRangeHi = QtWidgets.QLineEdit('0')
		self.boxes = [self.xRangeLow,
				self.xRangeHi,
				self.yRangeLow,
				self.yRangeHi,
				self.twinRangeLow,
				self.twinRangeHi]
		if labels is not None:
			self.xLabel = QtWidgets.QLineEdit(labels[0])
			self.yLabel = QtWidgets.QLineEdit(labels[1])
		else:
			self.xLabel = QtWidgets.QLineEdit()
			self.yLabel = QtWidgets.QLineEdit()
		self.twinLabel = QtWidgets.QLineEdit()
		self.layout().addWidget(QtWidgets.QLabel('x low'), 0, 0)
		self.layout().addWidget(self.xRangeLow, 0, 1)
		self.layout().addWidget(QtWidgets.QLabel('x high'), 0, 2)
		self.layout().addWidget(self.xRangeHi, 0, 3)
		self.layout().addWidget(QtWidgets.QLabel('y low'), 1, 0)
		self.layout().addWidget(self.yRangeLow, 1, 1)
		self.layout().addWidget(QtWidgets.QLabel('y high'), 1, 2)
		self.layout().addWidget(self.yRangeHi, 1, 3)
		self.layout().addWidget(QtWidgets.QLabel('x label'), 3, 0)
		self.layout().addWidget(self.xLabel, 3, 1)
		self.layout().addWidget(QtWidgets.QLabel('y label'), 3, 2)
		self.layout().addWidget(self.yLabel, 3, 3)
		self.plotData = plotData
		self.data = []
		if data is not None:
			for i, d in enumerate(data):
				self.data.append([])
				self.data[i].append(d[0]) if len(d) > 0 else self.data[i].append('')
				self.data[i].append(d[1]) if len(d) > 1 else self.data[i].append('r')
				self.data[i].append(d[2]) if len(d) > 2 else self.data[i].append('-')
		self.twins = twins
		self.twinData = twinData
		self.ranges = ranges
		self.labels = labels
		self.xRangeLow.setText(str(ranges[0][0]))
		self.xRangeHi.setText(str(ranges[0][1]))
		self.yRangeLow.setText(str(ranges[1][0]))
		self.yRangeHi.setText(str(ranges[1][1]))
		if self.twins is not None and len(twins) > 0:
			self.ax2.set_ylim(self.ranges[2])
			self.twinRangeLow.setText(str(self.ranges[2][0]))
			self.twinRangeHi.setText(str(self.ranges[2][1]))
			self.layout().addWidget(QtWidgets.QLabel('twin low'), 2, 0)
			self.layout().addWidget(self.twinRangeLow, 2, 1)
			self.layout().addWidget(QtWidgets.QLabel('twin high'), 2, 2)
			self.layout().addWidget(self.twinRangeHi, 2, 3)
			self.layout().addWidget(QtWidgets.QLabel('twin label'), 4, 0)
			self.layout().addWidget(self.twinLabel, 4, 1)
		self.plotAll(start=True)
		for b in self.boxes:
			b.textChanged.connect(self.changeAxes)
		self.xLabel.textChanged.connect(self.changeLabels)
		self.yLabel.textChanged.connect(self.changeLabels)
		self.twinLabel.textChanged.connect(self.changeLabels)
		self.table.cellChanged.connect(self.changeLines)

		self.saveButton = QtWidgets.QPushButton('Save Image')
		self.layout().addWidget(self.saveButton, 6, 0, 1, 4)
		self.saveButton.clicked.connect(self.saveImage)

	def plotAll(self, start=False):
		self.plot = plt.subplot()
		for i, l in enumerate(self.plotData):
			try:
				len(l[0])
				self.plot.plot(l[0], l[1], self.data[i][2], color=self.data[i][1], label=self.data[i][0])
				if start:
					tableAddRow(self.table, self.data[i])
			except:
				try:
					len(l[0])
					self.plot.plot(l[0], l[1])
					if start:
						tableAddRow(self.table, ['', 'r', '-'])
						self.data.append(['', 'r', '-'])
				except:
					if l[0] == 0:
						self.plot.axhline(y=l[1], color=self.data[i][1], linestyle=self.data[i][2], label=self.data[i][0])
						if start:
							tableAddRow(self.table, self.data[i])
					else:
						self.plot.axvline(x=l[0], color=self.data[i][1], linestyle=self.data[i][2], label=self.data[i][0])
						if start:
							tableAddRow(self.table, self.data[i])
		if self.twins is not None and len(self.twins) > 0:
			self.ax2 = plt.twinx(self.plot)
			for i, l in enumerate(self.twins):
				try:
					self.ax2.plot(l[0], l[1], self.data[i][2], color=self.twinData[i][1], label=self.twinData[i][0])
					if start:
						tableAddRow(self.table, self.twinData[i], '-')
				except:
					self.ax2.plot(l[0], l[1])
					if start:
						tableAddRow(self.table, ['', 'r', '-'])
						self.data.append(['', 'r', '-'])
		else:
			self.ax2 = None
		if self.ranges is not None:
			self.plot.set_xlim(self.ranges[0])
			self.plot.set_ylim(self.ranges[1])
			if self.ax2 is not None:
				self.ax2.set_ylim(self.ranges[2])
		self.plot.legend()
		if self.labels is not None:
			self.plot.set_xlabel(self.labels[0])
			self.plot.set_ylabel(self.labels[1])
			if self.ax2 is not None:
				self.ax2.set_xlabel(self.labels[0])
		plt.tight_layout()
		plt.show()

	def changeAxes(self):
		try:
			xL = float(self.xRangeLow.text())
			xH = float(self.xRangeHi.text())
			yL = float(self.yRangeLow.text())
			yH = float(self.yRangeHi.text())
			twinL = float(self.twinRangeLow.text())
			twinH = float(self.twinRangeHi.text())
			self.ranges = ((xL, xH), (yL, yH), (twinL, twinH))
			plt.close('all')
			self.plotAll()
		except:
			pass

	def changeLabels(self):
		self.labels = (self.xLabel.text(), self.yLabel.text(), self.twinLabel.text())
		plt.close('all')
		self.plotAll()


	def changeLines(self):
		try:
			for i in range(self.table.rowCount()):
				for j in range(3):
					self.data[i][j] = self.table.item(i, j).text()
			plt.close('all')
			self.plotAll()
		except:
			pass

	def saveImage(self):
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Image', figureRoot, 'PDF (*.pdf);;JPEG (*.jpg);;bitmap (*.bmp)')[0]
		saveFigure(filename)




def saveFigure(name:str, emf=True, skipSave=False, callingFileSav='', jpeg=True):
	if skipSave:
		return
	os.makedirs(os.path.dirname(name), exist_ok=True)
	if name.endswith('.pdf'):
		if ':' in name:
			file = name
		else:
			file = name
		plt.savefig(file)
		if emf:
			call(["C:/Program Files/Inkscape/inkscape.exe", "--file", file, "--export-emf", file[:-4] + ".emf", "--without-gui"])
		if jpeg:
			plt.savefig(file[:-4] + '.jpeg')
	else:
		try:
			plt.savefig(name, dpi=250)
		except:
			plt.savefig(name)
	if len(callingFileSav) > 0:
		with open(callingFileSav, 'r') as file:
			text = file.readlines()
		check = False
		for i, line in enumerate(text):
			if '__main__' in line:
				index = i + 1
				check = True
				break
		if not check:
			print('could not save sourcefile')
			return
		savText = []
		for i, line in enumerate(text[index:]):
			stripline = stripTabs(line)
			if not (stripline.startswith('#') or stripline == '\n'):
				savText.append(line)
		with open(name[:-4] + '.txt', 'w') as file:
			file.writelines(savText)


def stripTabs(line):
	stripline = line
	while stripline.startswith('\t'):
		stripline = stripline[1:]
	return stripline


class SavePicture(QtWidgets.QDialog):
	def __init__(self, plotData, plotColors=(), plotLabels=(), plotStyles=(), parent=None):
		super().__init__(parent)
		self.layout = QtWidgets.QGridLayout()
		# a figure instance to plot on
		self.figure = Figure()

		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas(self.figure)

		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.toolbar = NavigationToolbar(self.canvas, self)

		self.layout.addWidget(self.toolbar, 0, 0)
		self.layout.addWidget(self.canvas, 1, 0)
		self.setLayout(self.layout)

		ax = self.figure.add_subplot(111)
		ax.clear()
		for dat in plotData:
			ax.plot(dat[0], dat[1])
		self.canvas.draw()
