import numpy as np
import lmfit

def lorentz(x):
	return 1 / (1 + x**2)

# Magnetic imaging with an ensemble of nitrogen vacancy-centers in diamond (M. Chipaux et al.)
def multiODMRLorentz(x, y0, middlepoints, contrasts, distances, linewidths):
	if not len(middlepoints) == len(contrasts):
		print('not the same number of contrasts and peaks!!!')
		return np.nan
	intSum = 0
	for i, m in enumerate(middlepoints):
		intSum += contrasts[i] * (lorentz((x - m - distances[i]/2) / linewidths[i]) + lorentz(x - m + distances[i]/2) / linewidths[i])
	return y0 * (1 - intSum)

def lorentzPeak(x, intensity, mid, linewidth):
	return intensity * lorentz((x - mid) / linewidth)

def splittedLorentz(x, intensities, mids, linewidths, distances, nPeaks=2):
	lors = []
	try:
		len(distances)
	except:
		distances = [distances]
	try:
		len(intensities)
	except:
		intensities = [intensities]
	try:
		len(linewidths)
	except:
		linewidths = [linewidths]
	try:
		len(mids)
	except:
		mids = [mids]
	if nPeaks % 2 == 0:
		for i in range(nPeaks // 2):
			lors.append(lorentzPeak(x, intensities[i], mids[i] - distances[i]/2, linewidths[i]))
			lors.append(lorentzPeak(x, intensities[i], mids[i] + distances[i]/2, linewidths[i]))
	else:
		lors.append(lorentzPeak(x, intensities[0], mids[0], linewidths[0]))
		for i in range((nPeaks - 1) // 2):
			lors.append(lorentzPeak(x, intensities[i+1], mids[i+1] - distances[i]/2, linewidths[i+1]))
			lors.append(lorentzPeak(x, intensities[i+1], mids[i+1] + distances[i]/2, linewidths[i+1]))
	# lor1 = lorentzPeak(x, intensity, mid - distance/2, linewidth)
	# lor2 = lorentzPeak(x, intensity, mid + distance/2, linewidth)
	return sum(lors)

def splittedODMRLorentz(x, y0=1, contrast=0.1, mid=2.87e9, linewidth=3e6, distance=5e6, byKeyWord=None):
	if byKeyWord is not None:
		y0 = byKeyWord['y0']
		contrast = byKeyWord['contrast']
		mid = byKeyWord['mid']
		linewidth = byKeyWord['linewidth']
		distance = byKeyWord['distance']
	return y0 * (1 - splittedLorentz(x, contrast, mid, linewidth, distance))

def splittedAddLorentz(x, contrast=0.1, mid=2.87e9, linewidth=3e6, distance=5e6):
	return -1 * splittedLorentz(x, contrast, mid, linewidth, distance)

def singleODMRLorentz(x, y0=1, contrast=0.1, mid=2.87e9, linewidth=3e6):
	return y0 * (1 - splittedLorentz(x, contrast, mid, linewidth, 0, 1))

def singleLorentzPeak(x, y0=0, contrast=0.1, mid=2.87e9, linewidth=3e6):
	return y0 + splittedLorentz(x, contrast, mid, linewidth, 0, 1)

def splittedLorentzPeak(x, y0=0, contrast=0.1, mid=2.87e9, linewidth=3e6, distance=5e6):
	return y0 + splittedLorentz(x, contrast, mid, linewidth, distance)


def multipleFit(xdata, ydata, contrasts, mids, linewidths, distances, y0=1, n=2, vary=None, bounds=None, type='dip'):
	updVary = updBound = False
	if vary is None:
		vary = {}
		updVary = True
	if bounds is None:
		bounds = {}
		updBound = True
	if type == 'peak':
		if n % 2 == 0:
			fitmodel = lmfit.model.Model(splittedLorentzPeak, prefix='p0_')
		else:
			fitmodel = lmfit.model.Model(singleLorentzPeak, prefix='p0_')
	else:
		if n % 2 == 0:
			fitmodel = lmfit.model.Model(splittedODMRLorentz, prefix='p0_')
		else:
			fitmodel = lmfit.model.Model(singleODMRLorentz, prefix='p0_')
	for i in range(n // 2):
		if not 'p{}_contrast'.format(i) in vary:
			vary.update({'p{}_contrast'.format(i): True})
		if not 'p{}_mid'.format(i) in vary:
			vary.update({'p{}_mid'.format(i): True})
		if not 'p{}_linewidth'.format(i) in vary:
			vary.update({'p{}_linewidth'.format(i): True})
		if not 'p{}_distance'.format(i) in vary:
			vary.update({'p{}_distance'.format(i): True})
		if not 'p{}_y0'.format(i) in vary:
			vary.update({'p{}_y0'.format(i): True})
		if not 'p{}_contrast'.format(i) in bounds:
			bounds.update({'p{}_contrast'.format(i): (0, np.inf)})
		if not 'p{}_mid'.format(i) in bounds:
			bounds.update({'p{}_mid'.format(i): (0, 4e9)})
		if not 'p{}_linewidth'.format(i) in bounds:
			bounds.update({'p{}_linewidth'.format(i): (0, np.inf)})
		if not 'p{}_distance'.format(i) in bounds:
			bounds.update({'p{}_distance'.format(i): (0, np.inf)})
		if i == 0:
			continue
		if type == 'peak':
			fitmodel += lmfit.model.Model(splittedLorentz, prefix='p{}_'.format(i))
		else:
			fitmodel += lmfit.model.Model(splittedAddLorentz, prefix='p{}_'.format(i))
	params = fitmodel.make_params()
	try:
		len(distances)
	except:
		distances = [distances]
	try:
		len(contrasts)
	except:
		contrasts = [contrasts]
	try:
		len(mids)
	except:
		mids = [mids]
	try:
		len(linewidths)
	except:
		linewidths = [linewidths]
	for i in range(n // 2):
		params['p{}_contrast'.format(i)].set(contrasts[i], vary=vary['p{}_contrast'.format(i)], min=bounds['p{}_contrast'.format(i)][0], max=bounds['p{}_contrast'.format(i)][1])
		params['p{}_mid'.format(i)].set(mids[i], vary=vary['p{}_mid'.format(i)], min=bounds['p{}_mid'.format(i)][0], max=bounds['p{}_mid'.format(i)][1])
		params['p{}_linewidth'.format(i)].set(linewidths[i], vary=vary['p{}_linewidth'.format(i)], min=bounds['p{}_linewidth'.format(i)][0], max=bounds['p{}_linewidth'.format(i)][1])
		if i == 0:
			params['p{}_y0'.format(i)].set(y0, vary=vary['p{}_y0'.format(i)])
		if i > 0 or n % 2 == 0:
			params['p{}_distance'.format(i)].set(distances[i], vary=vary['p{}_distance'.format(i)], min=bounds['p{}_distance'.format(i)][0], max=bounds['p{}_distance'.format(i)][1])
	result = fitmodel.fit(ydata, x=xdata, params=params)
	return result


def splittedODMRFit(xdata, ydata, contrast, mid, linewidth, distance, vary=None, bounds=None):
	fitmodel = lmfit.model.Model(splittedODMRLorentz)
	params = fitmodel.make_params()
	if vary is None:
		vary = {}
	if bounds is None:
		bounds = {}
	for p in params.keys():
		if p not in vary:
			vary.update({p: True})
		if p not in bounds:
			bounds.update({p: (-np.inf, np.inf)})
	params['contrast'].set(contrast, vary=vary['contrast'], min=bounds['contrast'][0], max=bounds['contrast'][1])
	params['mid'].set(mid, vary=vary['mid'], min=bounds['mid'][0], max=bounds['mid'][1])
	params['linewidth'].set(linewidth, vary=vary['linewidth'], min=bounds['linewidth'][0], max=bounds['linewidth'][1])
	params['distance'].set(distance, vary=vary['distance'], min=bounds['distance'][0], max=bounds['distance'][1])
	result = fitmodel.fit(ydata, x=xdata, params=params)
	return result

