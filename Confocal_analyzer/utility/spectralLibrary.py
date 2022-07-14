import scipy.constants as const
import numpy as np
from scipy import signal

from Confocal_analyzer.utility import spectrumProcessing

fullLambdaDictionary = {
	'A1': 648.5,  # https://doi.org/10.1063/1.5045859
	'A2': 651.7,  # https://journals.aps.org/prb/pdf/10.1103/PhysRevB.80.245202
	'B1': 671.6,  # https://journals.aps.org/prb/pdf/10.1103/PhysRevB.80.245202
	'B2': 672.8,  # https://doi.org/10.1063/1.5045859
	'B3': 675.0,  # https://doi.org/10.1063/1.5045859
	'B4': 676.3,  # https://doi.org/10.1063/1.5045859
	'TS1': 768.8,  # https://doi.org/10.1063/1.5045859
	'TS1\'': 769.2,  # https://doi.org/10.1063/1.5045859
	'TS1\'\'': 768.7,  # https://doi.org/10.1063/1.5045859
	'TS2': 812.0,  # https://doi.org/10.1063/1.5045859
	'TS3': 813.3,  # https://doi.org/10.1063/1.5045859
	'TS3\'': 813.5,  # https://doi.org/10.1063/1.5045859
	'UD2': 1078.3,  # https://doi.org/10.1063/1.5045859
	'UD3': 914.1,  # https://doi.org/10.1063/1.5045859
	'UD3i': 913.3,  # https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204
	'UD3ii': 911.5,  # https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204
	'UD3iii': 910.4,  # https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204
	'UD3iv': 909.6,  # https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204
	'V1': 861.3,  # https://doi.org/10.1063/1.5045859
	'V1\'': 858.7,  # https://doi.org/10.1063/1.5045859
	'V2': 916.1,  # https://doi.org/10.1063/1.5045859
	'PL6': 1038.4,  # https://physics.aps.org/featured-article-pdf/10.1103/PhysRevLett.114.247603
	'diV hh': 1132.3,  # https://physics.aps.org/featured-article-pdf/10.1103/PhysRevLett.114.247603
	'diV kk': 1131.2,  # https://physics.aps.org/featured-article-pdf/10.1103/PhysRevLett.114.247603
	'NV kh': 1174.5,  # https://aip.scitation.org/doi/10.1063/1.5099327
	'NV hk': 1180.0,  # https://aip.scitation.org/doi/10.1063/1.5099327
	'NV- hh': 1223.3,  # https://aip.scitation.org/doi/10.1063/1.5099327
	'NV- kk': 1243.6,  # https://aip.scitation.org/doi/10.1063/1.5099327
}

fullSourceDictionary = {
	'A1': 'https://doi.org/10.1063/1.5045859',
	'A2': 'https://journals.aps.org/prb/pdf/10.1103/PhysRevB.80.245202',
	'B1': 'https://journals.aps.org/prb/pdf/10.1103/PhysRevB.80.245202',
	'B2': 'https://doi.org/10.1063/1.5045859',
	'B3': 'https://doi.org/10.1063/1.5045859',
	'B4': 'https://doi.org/10.1063/1.5045859',
	'TS1': 'https://doi.org/10.1063/1.5045859',
	'TS1\'': 'https://doi.org/10.1063/1.5045859',
	'TS1\'\'': 'https://doi.org/10.1063/1.5045859',
	'TS2': 'https://doi.org/10.1063/1.5045859',
	'TS3': 'https://doi.org/10.1063/1.5045859',
	'TS3\'': 'https://doi.org/10.1063/1.5045859',
	'UD2': 'https://doi.org/10.1063/1.5045859',
	'UD3': 'https://doi.org/10.1063/1.5045859',
	'UD3i': 'https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204',
	'UD3ii': 'https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204',
	'UD3iii': 'https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204',
	'UD3iv': 'https://journals.aps.org/prb/pdf/10.1103/PhysRevB.66.115204',
	'V1': 'https://doi.org/10.1063/1.5045859',
	'V1\'': 'https://doi.org/10.1063/1.5045859',
	'V2': 'https://doi.org/10.1063/1.5045859',
	'PL6': 'https://physics.aps.org/featured-article-pdf/10.1103/PhysRevLett.114.247603',
	'diV hh': 'https://physics.aps.org/featured-article-pdf/10.1103/PhysRevLett.114.247603',
	'diV kk': 'https://physics.aps.org/featured-article-pdf/10.1103/PhysRevLett.114.247603',
	'NV kh': 'https://aip.scitation.org/doi/10.1063/1.5099327',
	'NV hk': 'https://aip.scitation.org/doi/10.1063/1.5099327',
	'NV- hh': 'https://aip.scitation.org/doi/10.1063/1.5099327',
	'NV- kk': 'https://aip.scitation.org/doi/10.1063/1.5099327',
}

defectDictionary = {
	'A1': 'AB',
	'A2': 'AB',
	'B1': 'AB',
	'B2': 'AB',
	'B3': 'AB',
	'B4': 'AB',
	'TS1': 'TS',
	'TS1\'': 'TS',
	'TS1\'\'': 'TS',
	'TS2': 'TS',
	'TS3': 'TS',
	'TS3\'': 'TS',
	'UD2': 'VSi-VC',
	'UD3': 'UD3',
	'V1': 'VSi',
	'V1\'': 'VSi',
	'V2': 'VSi',
	'NV kh': 'NV',
	'NV hk': 'NV',
	'NV- hh': 'NV',
	'NV- kk': 'NV',
}

defectExplanations = {
	'AB': ('CSi-VC', 'carbon antisite'),
	'TS': ('unknown', 'unknwon'),
	'UD3': ('unknown', 'unknwon'),
	'VSi': ('VSi', 'Silicon vacancy'),
	'VSi-VC': ('VSi-VC', 'double vacancy'),
	'NV': ('NV', 'Nitrogen vacancz'),
}

fullEnergyDictionary = {}

for k, v in fullLambdaDictionary.items():
	energy = const.h * const.c / v * 1e9 / const.e
	fullEnergyDictionary.update({k: energy})

def energyeVFromWavelengthnm(wavelength):
	return const.h * const.c / wavelength * 1e9 / const.e

def getClosestByWavelength(wavelength):
	peakval = min(fullLambdaDictionary, key=lambda x: abs(x-wavelength))
	return list(fullLambdaDictionary.keys())[list(fullLambdaDictionary.values()).index(peakval)]

def getClosestByEnergy(ener):
	peakval = min(fullLambdaDictionary, key=lambda x: abs(x-ener))
	return list(fullLambdaDictionary.keys())[list(fullLambdaDictionary.values()).index(peakval)]

def recognisePeaks(spectrum, nrPeaks=1):
	subbedSpectrumY = spectrumProcessing.subtractLinearBackground(spectrum)
	peakPos, peakProps = signal.find_peaks(subbedSpectrumY[:,1], height=0)
	peakProminences = signal.peak_prominences(subbedSpectrumY[:,1], peakPos)[0]
	ziplist = zip(peakProminences, spectrum[peakPos, 0], spectrum[peakPos, 1])
	sortedPeaksAndHeight = [(x,y) for _,x,y in sorted(ziplist, key=lambda z: z[0], reverse=True)]
	return sortedPeaksAndHeight[:nrPeaks]

def labelPeak(wavelength, distance=5):
	roundedWave = np.round(wavelength, 1)
	roundedEnergy = energyeVFromWavelengthnm(roundedWave)
	dicVals = np.asarray(list(fullLambdaDictionary.values()))
	closest = np.argmin(np.abs(dicVals - roundedWave))
	value = dicVals[closest]
	enVal = energyeVFromWavelengthnm(value)
	deviation = abs(value - roundedWave)
	name = np.asarray(list(fullLambdaDictionary.keys()))[closest]
	if deviation == 0:
		return ' {:0.1f} nm: {:s}\n {:0.3f} eV'.format(roundedWave, name, roundedEnergy)
	elif deviation <= distance:
		return ' {:0.1f} nm: {:s} ({:0.1f})\n {:0.3f} eV ({:0.3f})'.format(roundedWave, name, value, roundedEnergy, enVal)
	else:
		return ' {:0.1f} nm\n {:0.3f} eV'.format(roundedWave, roundedEnergy)


if __name__ == '__main__':
	import pandas as pd
	lamb = pd.DataFrame(fullLambdaDictionary, index=['wavelength (nm)'])
	en = pd.DataFrame(fullEnergyDictionary, index=['energy (eV)'])
	src = pd.DataFrame(fullSourceDictionary, index=['source'])
	df = pd.concat([lamb, en, src])
	df2 = df.T
	df2.to_csv('spectral_lines.csv')


