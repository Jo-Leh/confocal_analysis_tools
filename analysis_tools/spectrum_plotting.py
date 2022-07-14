import copy
import sys
sys.path.append(r'C:\ProgramData\Anaconda3\pkgs')
sys.path.append(r"C:\ProgramData\Anaconda3\Library")
sys.path.append(r"C:\ProgramData\Anaconda3\Lib")
sys.path.append(r'C:\Users\od93yces\PycharmProjects')

import matplotlib.pyplot as plt
import numpy as np
import os
import operator

from subprocess import call

from Confocal_analyzer.utility.ANDOR_SIF_READER import ANDOR_SIF_Spectrum
from Confocal_analyzer.utility.simaging.spectrumseries import SpectrumSeries
from Confocal_analyzer.utility import spectrumProcessing
from Confocal_analyzer.utility import spectralLibrary

from PIL import Image
import tqdm

dataRoot = 'C:/Users/od93yces/Data/'
figureRoot = 'C:/Users/od93yces/Documents/Figures/'

confocalRoot = dataRoot + 'confocal_measurements/'
confocalLapRoot = dataRoot + 'confocal_LAP_measurements/'



if os.path.isfile('C:/Users/od93yces/Documents/test.txt'):
	with open('C:/Users/od93yces/Documents/test1.txt', 'w+') as f:
		f.write('test')
else:
	with open('C:/Users/od93yces/Documents/test.txt', 'w+') as f:
		f.write('test')

def labviewToDict(arr):
	dic = {}
	for tup in arr:
		dic.update({tup[0]: tup[1]})
	return dic

def helloWorld(kwargs):
	return 'hello World {}'.format(kwargs)

def loadSpectrum(file):
	spectrum = ANDOR_SIF_Spectrum.ANDOR_SIF_SPECTRUM(file)
	return np.array(spectrum.get_wavelength()), np.array(spectrum.get_counts())


def loadFolderSpectra(folder):
	if not folder.endswith('/'):
		folder += '/'
	spectra = []
	for fold, dirs, files in sorted(os.walk(folder)):
		for f in files:
			spectra.append(loadSpectrum(fold + f))
	return spectra


def loadLapSpectra(folder):
	if not os.path.isdir(folder):
		raise OSError(folder + ' is not a directory')
	series = SpectrumSeries(folder)
	unsorteddata, var = series.get_spectra()
	seriesSpectra = np.asanyarray(sorted(unsorteddata, key=operator.itemgetter(1)))
	spectra = []
	information = []
	voltages = []
	frequencies = []
	xPositions = []
	yPositions = []
	zPositions = []
	rotations = []
	for seriesSpectrum in seriesSpectra:
		spectra.append(np.transpose(np.loadtxt(seriesSpectrum[0])))
		information.append(np.asarray(seriesSpectrum[1]))
		if not seriesSpectrum[1][0] in voltages:
			voltages.append(seriesSpectrum[1][0])
		if not seriesSpectrum[1][3] in frequencies:
			frequencies.append(seriesSpectrum[1][3])
		if not seriesSpectrum[1][1] in xPositions:
			xPositions.append(seriesSpectrum[1][1])
		if not seriesSpectrum[1][2] in yPositions:
			yPositions.append(seriesSpectrum[1][2])
		if not seriesSpectrum[1][4] in zPositions:
			zPositions.append(seriesSpectrum[1][4])
		if not seriesSpectrum[1][5] in rotations:
			rotations.append(seriesSpectrum[1][5])
	return np.asarray(spectra), np.asarray(information), (np.asarray(voltages), np.asarray(xPositions), np.asarray(yPositions), np.asarray(frequencies), np.asarray(zPositions), np.asarray(rotations))

def reshapeLapSpectra(spectra, information, axis):
	sortSpec = np.asarray([x for _, x in sorted(zip(information[:,axis], spectra), key=lambda pair: pair[0])])
	sortInf = sorted(information, key=lambda t: t[axis])
	return spectra, information



def getBorderedSpectrum(spectrum, borders=()):
	if len(borders) == 1:
		area = np.where(borders[0] <= spectrum[0])
		smallSpectrumX = spectrum[0][area]
		smallSpectrumY = spectrum[1][area]
	elif len(borders) > 1:
		low = np.where(borders[0] <= spectrum[0])
		middleSpectrumX = spectrum[0][low]
		middleSpectrumY = spectrum[1][low]
		area = np.where(borders[1] >= middleSpectrumX)
		smallSpectrumX = middleSpectrumX[area]
		smallSpectrumY = middleSpectrumY[area]
	else:
		smallSpectrumX = spectrum[0]
		smallSpectrumY = spectrum[1]
	return smallSpectrumX, smallSpectrumY


def subtractLinearBackground(spectrum):
	x_start, x_end = (spectrum[0][0], spectrum[0][-1])
	y_start, y_end = (spectrum[1][0], spectrum[1][-1])
	m = (y_end - y_start) / (x_end - x_start)
	smallSpectrumX = spectrum[0]
	smallSpectrumY = spectrum[1] - (spectrum[0] - x_start) * m - y_start
	return smallSpectrumX, smallSpectrumY




def plotSpectrum(spectrum, fig=0, label=None, borders=(), subtractBg=False, normalize=False, color=None, linestyle='-'):
	plt.figure(fig, figsize=(12,5))
	plt.ticklabel_format(axis='both', style='sci', scilimits=(-2,4), useOffset=False)
	plt.xlabel('wavelength (nm)')
	plt.ylabel('counts')
	waitspec = getBorderedSpectrum(spectrum, borders)
	if subtractBg:
		smallSpectrumX, smallSpectrumY = subtractLinearBackground(waitspec)
		plt.ylabel('counts, shifted')
	else:
		smallSpectrumX, smallSpectrumY = waitspec

	if normalize:
		smallSpectrumY /= max(smallSpectrumY)
		plt.ylabel('PL intensity')

	if label is None:
		plt.plot(smallSpectrumX, smallSpectrumY, linestyle, color=color)
	else:
		plt.plot(smallSpectrumX, smallSpectrumY, linestyle, label=label, color=color)
		plt.legend(prop={'size': 12})
	plt.tight_layout()


def saveFigure(name:str, emf=True, skipSave=False, callingFileSav='', jpeg=True, dpi=250):
	if skipSave:
		return
	os.makedirs(os.path.dirname(figureRoot + name), exist_ok=True)
	if name.endswith('.pdf'):
		print('a')
		if ':' in name:
			file = name
		else:
			file = figureRoot + name
		plt.savefig(file)
		print('b')
		if emf:
			call(["C:/Program Files/Inkscape/inkscape.exe", "--file", file, "--export-emf", file[:-4] + ".emf", "--without-gui"])
		print('c')
		if jpeg:
			plt.savefig(file[:-4] + '.jpeg', dpi=dpi)
		print('d')
	else:
		try:
			plt.savefig(figureRoot + name, dpi=dpi)
		except:
			plt.savefig(figureRoot + name)
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
		with open(figureRoot + name[:-4] + '.txt', 'w') as file:
			file.writelines(savText)

def stripTabs(line):
	stripline = line
	while stripline.startswith('\t'):
		stripline = stripline[1:]
	return stripline

def getIntensities(spectra, lambdaBorders=(), subtractBg=False):
	intensities = np.empty_like(spectra[:,0,0])
	borderedSpectra = []
	for spectrum in spectra:
		borderSpectrum = getBorderedSpectrum(spectrum, lambdaBorders)
		if subtractBg:
			borderedSpectra.append(subtractLinearBackground(borderSpectrum))
		else:
			borderedSpectra.append(borderSpectrum)
	for i, spectrum in enumerate(borderedSpectra):
		intensities[i] = np.trapz(spectrum[1], x=spectrum[0])
	return intensities


def plotIntensities(intensities, reshapedInformation, label=None, fig=0, plotBy=(None, None, None, None, None), normIntensity=False):
	x = y = None
	xTitle = ''
	yTitle = ''
	titles = ('voltage (V)', r'x position ($\mu$m)', r'y position ($\mu$m)', 'frequency (Hz)', r'z Position ($\mu$m)')
	for i, ax in enumerate(plotBy):
		if ax == 'x':
			x = reshapedInformation[i]
			xTitle = titles[i]
		elif ax == 'y':
			y = reshapedInformation[i]
			yTitle = titles[i]
	if x is None and y is None:
		x = reshapedInformation[1]
		xTitle = titles[1]
		y = reshapedInformation[2]
		yTitle = titles[2]
	plt.figure(fig)
	plt.ticklabel_format(axis='both', style='sci', scilimits=(-2,4), useOffset=False)
	if x is None:
		x = y
		xTitle = yTitle
	if len(y) > 1:
		z = np.transpose(np.reshape(intensities, (len(x), len(y))))
		zTitle = 'counts'
		if normIntensity:
			a = np.amax(z)
			z /= a
			zTitle = 'relative intensity'
		plt.pcolormesh(x, y, z)
		cbar = plt.colorbar()
		cbar.set_label(zTitle)
		plt.xlabel(xTitle)
		plt.ylabel(yTitle)
	else:
		plt.xlabel(xTitle)
		if normIntensity:
			plt.ylabel('relative intensity')
			if label is None:
				plt.plot(x, intensities/max(intensities))
			else:
				plt.plot(x, intensities/max(intensities), label=label)
				plt.legend()
		else:
			plt.ylabel('counts')
			if label is None:
				plt.plot(x, intensities)
			else:
				plt.plot(x, intensities, label=label)
				plt.legend()
	plt.tight_layout()

def plotPeakIntensities(spectra, borderList=(), subtractBg=True, labelList=(), xAxis=None):
	intensities = np.empty((len(borderList), len(spectra)))
	for i, border in enumerate(borderList):
		for j, spectrum in enumerate(spectra):
			if subtractBg:
				borderSpectrum = subtractLinearBackground(getBorderedSpectrum(spectrum, border))
			else:
				borderSpectrum = getBorderedSpectrum(spectrum, border)
			intensities[i,j] = np.trapz(borderSpectrum[1], x=borderSpectrum[0])
	if xAxis is None:
		xAxis = range(len(spectra))
	if len(labelList) == len(borderList):
		for i, intensity in enumerate(intensities):
			plt.plot(xAxis, intensity, 'o-', label=labelList[i])
		plt.legend()
	else:
		for i, intensity in enumerate(intensities):
			plt.plot(xAxis, intensity, 'o-')




def intensityCompSpectrum(spectrum, border1, border2, subtractBg=True):
	if subtractBg:
		borderSpectrum1 = subtractLinearBackground(getBorderedSpectrum(spectrum, border1))
		borderSpectrum2 = subtractLinearBackground(getBorderedSpectrum(spectrum, border2))
	else:
		borderSpectrum1 = getBorderedSpectrum(spectrum, border1)
		borderSpectrum2 = getBorderedSpectrum(spectrum, border2)
	intensity1 = np.trapz(borderSpectrum1[1], x=borderSpectrum1[0])
	intensity2 = np.trapz(borderSpectrum2[1], x=borderSpectrum2[0])
	return intensity1/intensity2

def plotIntensityComps(spectra, border1, border2, subtractBg=True, xAxis=None, label=None):
	ratios = np.empty(len(spectra))
	for i, spectrum in enumerate(spectra):
		ratios[i] = intensityCompSpectrum(spectrum, border1, border2, subtractBg)
	if xAxis is None:
		if label is None:
			plt.plot(ratios, 'o')
		else:
			plt.plot(ratios, 'o', label=label)
			plt.legend()
	else:
		if label is None:
			plt.plot(xAxis, ratios, 'o')
		else:
			plt.plot(xAxis, ratios, 'o', label=label)
			plt.legend()
	plt.tight_layout()

def getPeakFit(spectrum, peakKind='Gaussian', backgroundKind='Linear',fitBorders=(0,2000), peaknumber=1, returnGuess=False, splitGuess=False):
	borderSpectrum = getBorderedSpectrum(spectrum, fitBorders)
	x = borderSpectrum[0]
	y = borderSpectrum[1]
	maxPos = np.argmax(y)
	backgroundGuess = (y[0], (y[-1] - y[0])/(x[-1] - x[0]), 1)
	if peaknumber == 1:
		bounds = [[fitBorders, (0, np.inf), (0, np.inf)]]
		peakGuess = (x[maxPos], 1, y[maxPos]-y[0])
		fit, peak, bg = spectrumProcessing.peakFitting(borderSpectrum, peakKind, backgroundKind, peakGuess, backgroundGuess=backgroundGuess, labelResults=True, bounds=bounds)
		if returnGuess:
			return fit, peak, bg, peakGuess
		return fit, peak, bg
	else:
		peaks = spectralLibrary.recognisePeaks(np.array(borderSpectrum).transpose(), peaknumber)
		peakGuess = []
		for p in peaks:
			peakGuess.append((p[0], 1, p[1] - y[0]))
		peakGuess.sort(key=lambda x: x[0])
		bounds = []
		for i, g in enumerate(peakGuess):
			l = fitBorders[0] if i == 0 or not splitGuess else peakGuess[i-1][0]
			h = fitBorders[1] if i == len(peakGuess) - 1 or not splitGuess else peakGuess[i+1][0]
			bounds.append([[l, h], [0, np.inf], [0, np.inf]])
		fit = spectrumProcessing.peakFitting(borderSpectrum, peakKind, backgroundKind, peakGuess, backgroundGuess=backgroundGuess, labelResults=False, peakNumber=peaknumber, bounds=bounds)
		if returnGuess:
			return fit, peakGuess
		return fit

def plotPeakFit(spectrum, makeFit=True, fit=None, peakKind='Gaussian', backgroundKind='Linear',fitBorders=(0,2000), peaknumber=1, returnGuess=False, splitGuess=False):
	if makeFit:
		if peaknumber == 1:
			if returnGuess:
				fit, peak, bg, guess = getPeakFit(spectrum, peakKind, backgroundKind, fitBorders, returnGuess=returnGuess)
			else:
				fit, peak, bg = getPeakFit(spectrum, peakKind, backgroundKind, fitBorders, returnGuess=returnGuess)
		else:
			if returnGuess:
				fit, guess = getPeakFit(spectrum, peakKind, backgroundKind, fitBorders, peaknumber, returnGuess=returnGuess, splitGuess=splitGuess)
			else:
				fit = getPeakFit(spectrum, peakKind, backgroundKind, fitBorders, peaknumber, returnGuess=returnGuess, splitGuess=splitGuess)
	x = getBorderedSpectrum(spectrum, fitBorders)[0]
	plt.plot(x, fit.model.eval(fit.params, **{fit.model.independent_vars[0]: x}), label='fit')
	if makeFit:
		if peaknumber == 1:
			if returnGuess:
				return fit, peak, bg, guess
			return fit, peak, bg
		else:
			if returnGuess:
				return fit, guess
			return fit

def getPeakIntensitiesFit(spectra, peakKind='Gaussian', backgroundKind='Linear', fitBorders=(0,2000)):
	intensities = np.empty(len(spectra))
	for i, spectrum in enumerate(spectra):
		intensities[i] = getPeakFit(spectrum, peakKind, backgroundKind, fitBorders)[1][2]
	return intensities

def make_small_ax_nm_z(sortedSpectra, info, axis, borderAxis, specBorder, zlim):
	x = sortedSpectra[0,0]
	y = info[:,axis]
	z = copy.deepcopy(sortedSpectra[:,1])
	if len(borderAxis) == 2:
		low = np.where(borderAxis[0] <= y)
		cutY = y[low]
		cutZ = z[low]
		area = np.where(borderAxis[1] >= cutY)
		smallY = cutY[area]
		smallZ1 = cutZ[area]
	else:
		smallY = y
		smallZ1 = z
	if len(specBorder) == 2:
		low = np.where(specBorder[0] <= x)
		cutX = x[low]
		cutZ = smallZ1[:,low]
		area = np.where(specBorder[1] >= cutX)
		smallX = cutX[area]
		smallZ2 = cutZ[:,0,area]
		smallZ = smallZ2[:,0]
	else:
		smallX = x
		smallZ = smallZ1
	if len(zlim) == 2:
		smallZ[np.where(zlim[0] > smallZ)] = zlim[0]
		smallZ[np.where(zlim[1] < smallZ)] = zlim[1]
	return smallX, smallY, smallZ


def gif_of_spectra(sortedSpectra, info, axis, borderAxis=(), specBorder=(), zlim=None, ylabel='', path='', gif=True, video=True, framerate=60, floatsort=False):
	smallX, smallY, smallZ = make_small_ax_nm_z(sortedSpectra, info, axis, borderAxis, specBorder, ())
	if zlim is None:
		zlim = (np.min(smallZ), np.max(smallZ))
	for i, y in tqdm.tqdm(enumerate(smallY)):
		plt.plot(smallX, smallZ[i])
		plt.xlabel('wavelength (nm)')
		plt.ylabel(ylabel)
		plt.title(y)
		plt.ylim(*zlim)
		plt.tight_layout()
		plt.savefig(f'{path}/{y}.jpg', dpi=250)
		plt.close()
	gif_of_images(path, video=video, gif=gif, framerate=framerate, floatsort=floatsort)

def gif_of_images(path, video=True, gif=True, framerate=60, floatsort=False):
	if gif:
		images = []
		lister = os.listdir(path)
		if floatsort:
			lister = sorted(lister, key=lambda x: float(x.split('.jpg')[0]))
		for f in tqdm.tqdm(lister):
			if f.endswith('.jpg'):
				im = Image.open(f'{path}/{f}')
				images.append(im)
		im0 = images[0]
		im0.save(f'{path}/compile.gif', format='GIF', append_images=images, duration=1000/framerate, save_all=True, loop=1)
	if video:
		frameSize = (1600, 1200)
		out = cv2.VideoWriter(f'{path}/video_compile.avi',cv2.VideoWriter_fourcc(*'DIVX'), framerate, frameSize)
		lister = os.listdir(path)
		lister = [f for f in lister if f.endswith('.jpg')]
		if floatsort:
			lister = sorted(lister, key=lambda x: float(x.split('.jpg')[0]))
		for f in tqdm.tqdm(lister):
			img = cv2.imread(f'{path}/{f}')
			out.write(img)
		out.release()


def plotSpectraOverParameter(sortedSpectra, info, axis, borderAxis=(), specBorder=(), transpose=True, colBar=True, logZ=False, zlim=()):
	smallX, smallY, smallZ = make_small_ax_nm_z(sortedSpectra, info, axis, borderAxis, specBorder, zlim)
	label = 'z position (µm)' if axis == 4 else ''
	if transpose:
		plotX = smallY
		plotY = smallX
		plotZ = np.transpose(smallZ)
		plt.ylabel('wavelength (nm)')
		plt.xlabel(label)
	else:
		plotX = smallX
		plotY = smallY
		plotZ = smallZ
		plt.xlabel('wavelength (nm)')
		plt.ylabel(label)
	plotX -= (plotX[1] - plotX[0])/2
	plotY -= (plotY[1] - plotY[0])/2
	plotX = list(plotX) + [plotX[-1] + plotX[1] - plotX[0]]
	plotY = list(plotY) + [plotY[-1] + plotY[1] - plotY[0]]
	if logZ:
		plt.pcolormesh(plotX, plotY, np.log(plotZ))
	else:
		plt.pcolormesh(plotX, plotY, plotZ)
	if colBar:
		cbar = plt.colorbar()
		cbar.set_label('counts')
	plt.tight_layout()


def polarPlot(spectra, splitinfos, integrateNotFit=True, borders=(), background=True, color=None, normalize=False, rescale=False, ax=None, label=None):
	if ax is None:
		fig = plt.figure()
		ax = fig.add_subplot(projection='polar')
	if integrateNotFit:
		ints = getIntensities(spectra, borders, background)
	else:
		ints = getPeakIntensitiesFit(spectra, 'Voigt', fitBorders=borders)
	if rescale:
		ints -= min(ints)
	if normalize:
		ints /= max(ints)
	ax.plot((splitinfos[5] + 7.8) / 180 * 2 * np.pi, ints, 'o', color=color, label=label)
	return ax


# def plotPeakIntensitiesFit(spectra, peakKind='Gaussian', backgroundKind='Linear', fitBorders=(0,2000), xAxis=None, label=None):
# 	getPeakIntensitiesFit(spectra, peakKind='Gaussian', backgroundKind='Linear', fitBorders=(0,2000))
# 	plt.ylabel('PL intensity')
# 	if xAxis is None:
# 		xAxis = range(len(intensities))
# 	if label is None:
# 		plt.plot(xAxis, intensities)
# 	else:
# 		plt.plot(xAxis, intensities, label=label)


thisfile = 'C:/Users/od93yces/PycharmProjects/analysis_tools/spectrum_plotting.py'

stdColors = plt.rcParams['axes.prop_cycle'].by_key()['color']

if __name__ == '__main__':
	data, info, _ = loadLapSpectra(r"P:\He Zhu\confocal_analysis_stuff\example\contact_7_532nm_OD1_conf_40V")

	plotSpectraOverParameter(data, info, 0)
	plt.xlabel('voltage (V)')
	plt.tight_layout()
	# saveFigure(r"P:\He Zhu\confocal_analysis_stuff\example\test_image.pdf", emf=False)
	plt.show()