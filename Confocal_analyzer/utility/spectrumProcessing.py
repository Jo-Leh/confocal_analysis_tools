import numpy as np
import lmfit
import copy


def substituteCosmics(spectrum, diffVal=2):
	if len(spectrum) > 2:
		useSpec = np.transpose(spectrum)
	else:
		useSpec = spectrum
	spect = copy.deepcopy(useSpec)
	spec = spect[1]
	positions = []
	for i, v in enumerate(spec):
		if i == 0 or i == len(spec)-1:
			continue
		if v > diffVal * spec[i-1] and v > diffVal * spec[i+1]:
			spec[i] = (spec[i-1] + spec[i+1])/2
	return spect


def filterMultiple(spectra, diffVal=2):
	specs = []
	for s in spectra:
		specs.append(substituteCosmics(s, diffVal=diffVal))
	return np.array(specs)



def subtractConstantBackground(spectrum, startPos=0, endPos=0, value=0):
	shortenedSpectrum = spectrum[startPos:] if endPos <= startPos else spectrum[startPos:endPos]
	returnSpec = np.empty_like(shortenedSpectrum)
	returnSpec[:,0] = shortenedSpectrum[:,0]
	returnSpec[:,1] = shortenedSpectrum[:,1] - value
	return returnSpec

def subtractLinearBackground(spectrum, startPos=0, endPos=0, backgroundData=False):
	shortenedSpectrum = spectrum[startPos:] if endPos <= startPos else spectrum[startPos:endPos]
	returnSpec = np.empty_like(shortenedSpectrum)
	x_start = shortenedSpectrum[:, 0][0]
	x_end = shortenedSpectrum[:, 0][-1]
	y_start = shortenedSpectrum[:, 1][0]
	y_end = shortenedSpectrum[:, 1][-1]
	m = (y_end - y_start) / (x_end - x_start)
	x = shortenedSpectrum[:, 0]
	returnSpec[:,0] = x
	returnSpec[:,1] = shortenedSpectrum[:, 1] - (x - x_start) * m - y_start
	if backgroundData:
		return returnSpec, (m, y_start, shortenedSpectrum[:,0], (shortenedSpectrum - returnSpec)[:,1])
	return returnSpec

def spectrumIntegration(spectrum, startPos=0, endPos=0, offsetX=0, offsetY=0, scale=1, changedXY=False):
	x_full = spectrum[:,0] + offsetX
	y_full = spectrum[:,1] * scale + offsetY

	x = x_full[startPos:endPos] if endPos > startPos else x_full[startPos:]
	y = y_full[startPos:endPos] if endPos > startPos else y_full[startPos:]

	if changedXY:
		return np.trapz(y,x), x, y
	return np.trapz(y,x)

def peakFitting(spectrum, peakName='', backgroundName='', peakGuess=(1,1,1),  peakVary=(True,True,True), backgroundGuess=(0,1,1), backgroundVary=(True,True,True), labelResults=False, peakNumber=1, bounds=[]):
	if peakName == 'Gaussian':
		peak = lmfit.models.GaussianModel(prefix='peak_')
	elif peakName == 'Lorentzian':
		peak = lmfit.models.LorentzianModel(prefix='peak_')
	elif peakName == 'Voigt':
		peak = lmfit.models.VoigtModel(prefix='peak_')
	else:
		return
	if backgroundName == 'Constant':
		background = lmfit.models.ConstantModel(prefix='bg_')
	elif backgroundName == 'Linear':
		background = lmfit.models.LinearModel(prefix='bg_')
	elif backgroundName == 'Quadratic':
		background = lmfit.models.QuadraticModel(prefix='bg_')
	else:
		return

	params = lmfit.Parameters()
	params.update(background.make_params())
	params.update(peak.make_params())

	model = peak + background


	if peakNumber > 1:
		addPeaks = []
		for i in range(1, peakNumber):
			if peakName == 'Gaussian':
				p = lmfit.models.GaussianModel(prefix='p_{}_'.format(i))
			elif peakName == 'Lorentzian':
				p = lmfit.models.LorentzianModel(prefix='p_{}_'.format(i))
			elif peakName == 'Voigt':
				p = lmfit.models.VoigtModel(prefix='p_{}_'.format(i))
			else:
				return
			addPeaks.append(p)
			params.update(p.make_params())
			model += p



	if len(spectrum) == 2:
		x = spectrum[0]
		y = spectrum[1]
	else:
		x = spectrum[:,0]
		y = spectrum[:,1]

	if backgroundName == 'Constant':
		params['bg_c'].set(backgroundGuess[0], vary=backgroundVary[0])
	elif backgroundName == 'Linear':
		params['bg_intercept'].set(backgroundGuess[0], vary=backgroundVary[0])
		params['bg_slope'].set(backgroundGuess[1], vary=backgroundVary[1])
	else:
		params['bg_c'].set(backgroundGuess[0], vary=backgroundVary[0])
		params['bg_b'].set(backgroundGuess[1], vary=backgroundVary[1])
		params['bg_a'].set(backgroundGuess[2], vary=backgroundVary[2])
	if peakNumber > 1:
		for i in range(1, peakNumber):
			if len(bounds) >= i - 1:
				params['p_{}_center'.format(i)].set(peakGuess[i][0], vary=peakVary[0], min=bounds[i][0][0], max=bounds[i][0][1])
				params['p_{}_sigma'.format(i)].set(peakGuess[i][1], vary=peakVary[1], min=bounds[i][1][0], max=bounds[i][1][1])
				params['p_{}_amplitude'.format(i)].set(peakGuess[i][2], vary=peakVary[2], min=bounds[i][2][0], max=bounds[i][2][1])
			else:
				params['p_{}_center'.format(i)].set(peakGuess[i][0], vary=peakVary[0])
				params['p_{}_sigma'.format(i)].set(peakGuess[i][1], vary=peakVary[1])
				params['p_{}_amplitude'.format(i)].set(peakGuess[i][2], vary=peakVary[2])
		if len(bounds) > 0:
			params['peak_center'].set(peakGuess[0][0], vary=peakVary[0], min=bounds[0][0][0], max=bounds[0][0][1])
			params['peak_sigma'].set(peakGuess[0][1], vary=peakVary[1], min=bounds[0][1][0], max=bounds[0][1][1])
			params['peak_amplitude'].set(peakGuess[0][2], vary=peakVary[2], min=bounds[0][2][0], max=bounds[0][2][1])
		else:
			params['peak_center'].set(peakGuess[0][0], vary=peakVary[0])
			params['peak_sigma'].set(peakGuess[0][1], vary=peakVary[1])
			params['peak_amplitude'].set(peakGuess[0][2], min=0, vary=peakVary[2])
	else:
		params['peak_center'].set(peakGuess[0], vary=peakVary[0])
		params['peak_sigma'].set(peakGuess[1], vary=peakVary[1])
		params['peak_amplitude'].set(peakGuess[2], min=0, vary=peakVary[2])
	out = model.fit(y, params, x=x)

	if labelResults:
		peakResults = [out.best_values['peak_center'], out.best_values['peak_sigma'], out.best_values['peak_amplitude']]
		backgroundResults = [np.nan, np.nan, np.nan]
		if backgroundName == 'Constant':
			backgroundResults[0] = out.best_values['bg_c']
		elif backgroundName == 'Linear':
			backgroundResults[0] = out.best_values['bg_intercept']
			backgroundResults[1] = out.best_values['bg_slope']
		else:
			backgroundResults[0] = out.best_values['bg_c']
			backgroundResults[1] = out.best_values['bg_b']
			backgroundResults[2] = out.best_values['bg_a']
		return out, peakResults, backgroundResults
	return out

def diffSpec(spectra):
	gradSpec = np.empty_like(spectra)
	gradSpec[:,0] = spectra[:,0]
	gradSpec[:,1] = np.gradient(spectra[:,1], axis=0)
	return gradSpec


