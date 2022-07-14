import matplotlib.pyplot as plt
import numpy as np
import os

from subprocess import call


dataRoot = 'C:/Users/od93yces/Data/'
figureRoot = 'C:/Users/od93yces/Documents/Figures/'

confocalRoot = dataRoot + 'confocal_measurements/'
confocalLapRoot = dataRoot + 'confocal_LAP_measurements/'

stdColors = plt.rcParams['axes.prop_cycle'].by_key()['color']


def hallprobeIV(lapMeas, logPlot=True):
	# if logPlot:
	# 	plt.subplot(i,2, 1)
	plt.figure(1)
	plt.xlabel('voltage (V)')
	plt.ylabel('current (A)')
	plt.plot(lapMeas['Agilent:Channel1:Voltage'], lapMeas['Agilent:Channel1:Current'])
	if logPlot:
		plt.figure(2)
		plt.xlabel('voltage (V)')
		plt.ylabel('logarithmic current (A)')
		plt.plot(lapMeas['Agilent:Channel1:Voltage'], np.abs(lapMeas['Agilent:Channel1:Current']))
		plt.semilogy()



def saveFigure(name:str, emf=True, skipSave=False, callingFileSav='', jpeg=True):
	if skipSave:
		return
	os.makedirs(os.path.dirname(figureRoot + name), exist_ok=True)
	if name.endswith('.pdf'):
		if ':' in name:
			file = name
		else:
			file = figureRoot + name
		plt.savefig(file)
		if emf:
			call(["C:/Program Files/Inkscape/inkscape.exe", "--file", file, "--export-emf", file[:-4] + ".emf", "--without-gui"])
		if jpeg:
			plt.savefig(file)
	else:
		try:
			plt.savefig(figureRoot + name, dpi=250)
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
