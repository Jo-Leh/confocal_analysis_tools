import numpy as np
import re

otherHeadline = r'\s*(.*)\s*(.*)'



def loadLAPFile(filename):
	with open(filename, 'r') as f:
		headline = f.readline()
	data = np.loadtxt(filename, skiprows=1)
	if '\t' in headline:
		headstrings = headline.split('\t')
	else:
		whitespaceSplit = headline.split('  ')
		headstrings = []
		for l in whitespaceSplit:
			if len(l) > 0:
				headstrings.append(l)
	info = {}
	for i, name in enumerate(headstrings):
		if name.endswith('\n'):
			name = name[:-1]
		if name.startswith('<'):
			name = name[1:]
		if name.endswith('>'):
			name = name[:-1]
		info.update({name: data[:,i]})
	return info

def dictToLAPfile(filename, dataDict:dict):
	keys = list(dataDict.keys())
	data = np.empty((len(dataDict[keys[0]]), len(keys)))
	header = ''
	for i, k in enumerate(keys):
		header += k
		if i < len(keys) - 1:
			header += '\t'
		data[:,i] = dataDict[k]
	np.savetxt(filename, data, header=header, comments='')


if __name__ == '__main__':
	a = loadLAPFile('C:/Users/od93yces/Data/confocal_LAP_measurements/CH_3/odmr_test/a_000.txt')
	pass