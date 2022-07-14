import numpy as np
import pyqtgraph as pg
import scipy.constants as const

from utility import spectralLibrary
from mainWindow import Analyzer


def makeSpectrum(listSpectrum):
	return np.asarray([(x,y) for x,y in zip(listSpectrum.wavelength, listSpectrum.spectrum)])

def nmFromeV(energy):
	return const.h * const.c / energy / const.e * 1e9
# def measChanged

def eVfromNM(wavelength):
	return const.h * const.c / wavelength / 1e-9 / const.e


def labelPeaks(gui:Analyzer):
	"""tries to label a given number of highest peaks (#gui.numberOfPeakLabels) via the spectral library module"""
	if gui.checkBoxPeakLabeling.isChecked():
		acts = gui.active_spectrum(True)
		gui.peakLabels = []
		gui.plot_all()
		for a in acts:
			act = gui.loaded_spectra_list[a.row()]
			spec = makeSpectrum(act)
			try:
				n = int(gui.numberOfPeakLabels.text())
			except:
				return
			peaks = spectralLibrary.recognisePeaks(spec, n)
			for peak in peaks:
				labelText = spectralLibrary.labelPeak(peak[0])
				label = pg.TextItem(labelText)
				gui.plot_item.addItem(label)
				label.setPos(peak[0], peak[1])
				label.setAnchor((0, 1))
				gui.peakLabels.append(label)
	else:
		for label in gui.peakLabels:
			label.hide()
		gui.peakLabels = []

def add_spectra_to_plot_items(gui:Analyzer):
	"""scales the spectra according to given scales and offsets, then plots them"""
	gui.plot_item_list_spectra = []
	for i, spectrum in enumerate(gui.loaded_spectra_list):
		scale = float(gui.confMeasList.item(i, 5).text())
		offset_y = float(gui.confMeasList.item(i, 4).text())
		offset_x = float(gui.confMeasList.item(i, 3).text())

		if gui.radioButton_wavelength.isChecked():
			print("Wavelength style")
			x = np.array(spectrum.get_wavelength()) + offset_x
		elif gui.radioButton_photonEnergy.isChecked():
			print("Energy style")
			x = 1239.841857 / (np.array(spectrum.get_wavelength()) + offset_x)
		else:
			print('Raman style')
			gui.laserWave = float(gui.laserWavelengthLine.text())
			x = (1/gui.laserWave - 1/(np.array(spectrum.get_wavelength()) + offset_x)) * 1e7
		y = np.array(spectrum.get_counts()) * scale + offset_y
		gui.plot_item_list_spectra.append(pg.PlotCurveItem(x, y, pen=pg.mkPen(width=1, color=gui.color_list[i]), name=gui.spectra_label_list[i]))
		# gui.textBrowser.append('(' + str(i + 1) + ') ' + gui.spectra_name_list[i])

def changeInfLinePos(gui:Analyzer, t):
	"""changes the position of the infinity-lines when the numbers are changed"""
	if t == 0:
		loVal = gui.lineEdit_from_nm.text()
		hiVal = gui.lineEdit_to_nm.text()
		gui.infLineLo.setValue(float(loVal))
		gui.infLineHi.setValue(float(hiVal))
		gui.lineEdit_intensity_from.setText(loVal)
		gui.lineEdit_intensity_to.setText(hiVal)
		try:
			gui.infLineVert.setValue(float(gui.lineEdit_guess_c.text()))
		except:
			pass
	else:
		loVal = gui.lineEdit_intensity_from.text()
		hiVal = gui.lineEdit_intensity_to.text()
		gui.infLineLo.setValue(float(loVal))
		gui.infLineHi.setValue(float(hiVal))
		gui.lineEdit_from_nm.setText(loVal)
		gui.lineEdit_to_nm.setText(hiVal)
		try:
			gui.infLineVert.setValue(float(gui.lineEdit_bgConstOffset.text()))
		except:
			pass

def checkBox_vertLinesStateChanged(gui:Analyzer):
	"""shows or hides the infinity-lines depending on the state of the checkbox"""
	if gui.checkBox_vertLines.isChecked():
		gui.infLineLo.show()
		gui.infLineHi.show()
		gui.infLineVert.show()
	else:
		gui.infLineLo.hide()
		gui.infLineHi.hide()
		gui.infLineVert.hide()

def combo_active_fit_changed(gui:Analyzer):
	"""switches the currently active fit to show the respective data"""
	if len(gui.scale_spectra_list) > 0:
		i = gui.active_fit()
		gui.label_fit_result_lambda.setText(str('%.5f' % gui.fit_result_lambda_c[i]))
		gui.label_fit_result_sigma.setText(str('%.5e' % gui.fit_result_sigma[i]))
		gui.label_fit_result_amp.setText(str('%.5e' % gui.fit_result_amp[i]))
		gui.label_fit_result_c.setText(str('%.5e' % gui.fit_result_c[i]))
		gui.label_fit_result_m.setText(str('%.5e' % gui.fit_result_m[i]))
		gui.label_fit_result_quad.setText(str('%.5e' % gui.fit_result_quad[i]))

# def combo_active_spectrum_changed(gui:Analyzer):
# 	"""changes the active spectrum for editing and so on"""
# 	i = gui.active_spectrum()
# 	if i > 0:
# 		if len(gui.scale_spectra_list) == i:
# 			return
# 		print("comboboxindex " + str(i))
# 		gui.lineEdit_scale.setText(str(gui.scale_spectra_list[i]))
# 		gui.lineEdit_offset_y.setText(str(gui.offset_y_spectra_list[i]))
# 		gui.lineEdit_offset_x.setText(str(gui.offset_x_spectra_list[i]))
# 		# gui.lineEdit_lengend_name.setText(gui.spectra_label_list[i])
# 		gui.infLinePosChanged()

def getActualLambdaMinMax(gui:Analyzer):
	"""returns the min/max values for the wavelength including the applied shift"""
	i = gui.active_spectrum()
	d_x = gui.get_alignment_param()[1]
	x_full = np.array(gui.loaded_spectra_list[i].get_wavelength()) + d_x
	return min(x_full), max(x_full)

def getActualCountsMinMax(gui:Analyzer):
	"""returns the min/max values for the wavelength including applied shift and scaling"""
	i = gui.active_spectrum()
	scale, d_x, d_y = gui.get_alignment_param()

	y_full = np.array(gui.loaded_spectra_list[i].get_counts()) * scale + d_y
	return min(y_full), max(y_full)

def infLinePosChanged(gui:Analyzer):
	"""changes the numbers shown according to the actual position of the infinity-lines, the fit-center-guess is the middle between the lines
	if the lines are outside the range, they are set to the edges"""
	posLo = gui.infLineLo.value()
	posHi = gui.infLineHi.value()
	posVert = gui.infLineVert.value()
	gui.lineEdit_guess_sigma.setText(str(0.2))
	minVal, maxVal = gui.getActualLambdaMinMax()
	if posHi > posLo > minVal and posLo < maxVal:
		gui.lineEdit_from_nm.setText(str('%0.2f' % posLo))
		gui.lineEdit_intensity_from.setText(str('%0.2f' % posLo))
	else:
		gui.lineEdit_from_nm.setText('{:0.2f}'.format(minVal))
		gui.lineEdit_intensity_from.setText('{:0.2f}'.format(minVal))
		gui.infLineLo.setValue(minVal)
		posLo = minVal

	if posLo < posHi < maxVal and posHi > minVal:
		gui.lineEdit_to_nm.setText(str('%0.2f' % posHi))
		gui.lineEdit_intensity_to.setText(str('%0.2f' % posHi))
	else:
		gui.lineEdit_to_nm.setText('{:0.2f}'.format(maxVal))
		gui.lineEdit_intensity_to.setText('{:0.2f}'.format(maxVal))
		gui.infLineHi.setValue(maxVal)

	if gui.getActualCountsMinMax()[0] < posVert < gui.getActualCountsMinMax()[1]:
		gui.lineEdit_guess_c.setText(str('%0.2f' % posVert))
		gui.lineEdit_bgConstOffset.setText(str('%0.2f' % posVert))
		gui.lineEdit_guess_amp.setText(
			str('%0.2f' % (gui.getActualCountsMinMax()[1] - gui.getActualCountsMinMax()[0])))
	else:
		gui.infLineVert.setValue(gui.getActualCountsMinMax()[0] + 1)

def plot_all(gui:Analyzer):
	"""utility (re-)plotting of infinity-lines, spectra and fits"""
	# gui.textBrowser.clear()
	gui.plot_item.clear()
	gui.plot_item.addItem(gui.infLineLo)
	gui.plot_item.addItem(gui.infLineHi)
	gui.plot_item.addItem(gui.infLineVert)
	gui.remove_legend_items()
	for i, spectrum in enumerate(gui.plot_item_list_spectra):
		if not gui.confMeasList.item(i, 1).checkState():
			continue
		# print("Spectrum x data %f" % spectrum.getData()[0][0])
		gui.legend.addItem(spectrum, gui.spectra_label_list[i])
		gui.plot_item.addItem(spectrum)

	for i, fit in enumerate(gui.plot_item_list_fits):
		if not gui.confFitList.item(i, 1).checkState():
			continue
		gui.plot_item.addItem(fit)

	for i, line in enumerate(gui.infLineList):
		if not gui.confLineList.item(i, 1).checkState():
			continue
		gui.plot_item.addItem(line)

	for i, line in enumerate(gui.plot_item_list_ints):
		if not gui.confIntList.item(i, 1).checkState():
			continue
		gui.plot_item.addItem(line)

	for i, line in enumerate(gui.plot_item_list_bgs):
		if not gui.confIntList.item(i, 1).checkState():
			continue
		gui.plot_item.addItem(line)

def radio_btn_bg_toggled(gui:Analyzer):
	"""changes the availability of input for fits, depending on the chosen background"""
	if gui.radioButton_bg_constant.isChecked():
		gui.label_m.setDisabled(True)
		gui.lineEdit_guess_slope.setDisabled(True)
		gui.label_fit_result_m.setDisabled(True)
		gui.checkBox_fixed_m.setDisabled(True)
	else:
		gui.label_m.setEnabled(True)
		gui.lineEdit_guess_slope.setEnabled(True)
		gui.label_fit_result_m.setEnabled(True)
		gui.checkBox_fixed_m.setEnabled(True)
	if gui.radioButton_bg_quad.isChecked():
		gui.label_q.setEnabled(True)
		gui.lineEdit_guess_quad.setEnabled(True)
		gui.label_fit_result_quad.setEnabled(True)
		gui.checkBox_fixed_quad.setEnabled(True)
	else:
		gui.label_q.setDisabled(True)
		gui.lineEdit_guess_quad.setDisabled(True)
		gui.label_fit_result_quad.setDisabled(True)
		gui.checkBox_fixed_quad.setDisabled(True)


def remove_fit(gui:Analyzer):
	"""removes the currently selected fit"""
	indices = gui.active_fit(multi=True)
	indices = sorted(indices, key= lambda x: x.row())
	for index in indices[::-1]:
		i = index.row()
		gui.plot_item_list_fits.pop(i)
		gui.confFitList.removeRow(i)
		gui.fit_result_lambda_c.pop(i)
		gui.fit_result_sigma.pop(i)
		gui.fit_result_amp.pop(i)
		gui.fit_result_c.pop(i)
		gui.fit_result_m.pop(i)
	gui.plot_all()

def remove_legend_items(gui:Analyzer):
	"""removes all entries from the plot-legend"""
	while len(gui.legend.items) > 0:
		gui.legend.scene().removeItem(gui.legend)
		gui.legend = pg.LegendItem()
		gui.legend.setParentItem(gui.plot_item)

def remove_spectrum(gui:Analyzer):
	"""removes the currently selected spectrum and all the information for it, then re-plots everything"""
	indices = gui.active_spectrum(True)
	indices = sorted(indices, key= lambda x: x.row())
	for index in indices[::-1]:
		i = index.row()
		gui.plot_item_list_spectra.pop(i)
		gui.loaded_spectra_list.pop(i)
		gui.spectra_name_list.pop(i)
		gui.color_list.pop(i)
		# gui.comboBox_Active_Spectrum.removeItem(i)
		gui.scale_spectra_list.pop(i)
		gui.offset_y_spectra_list.pop(i)
		gui.offset_x_spectra_list.pop(i)
		gui.confMeasList.removeRow(i)
	gui.plot_all()

def update_plot_scale_offset(gui):
	"""updates the changes in scale and offset for the plot, and the list for further processing"""
	i = gui.active_spectrum()
	scale = float(gui.confMeasList.item(i, 5).text())
	offset_y = float(gui.confMeasList.item(i, 4).text())
	offset_x = float(gui.confMeasList.item(i, 3).text())
	# scale = float(gui.lineEdit_scale.text())
	# offset_y = float(gui.lineEdit_offset_y.text())
	# offset_x = float(gui.lineEdit_offset_x.text())
	gui.scale_spectra_list[i] = scale
	gui.offset_y_spectra_list[i] = offset_y
	gui.offset_x_spectra_list[i] = offset_x
	gui.add_spectra_to_plot_items()
	gui.plot_all()

def get_alignment_param(self):
	"""utility, returning a list of scale, and offset (x and y) for the currently selected spectrum"""
	i = self.active_spectrum()
	scale = float(self.scale_spectra_list[i])
	offset_y = float(self.offset_y_spectra_list[i])
	offset_x = float(self.offset_x_spectra_list[i])
	return scale, offset_x, offset_y




