import numpy as np
import matplotlib.pyplot as plt
import os
import sys

from analysis_tools.spectrum_plotting import saveFigure


def plotSParameter(data, label=None, dBtoQuotient=False, cali=False, op=None, short=None):
	if dBtoQuotient:
		plotData = dBToDezimalPart(data[:,1])
		plt.ylabel('S-Parameter (P1/P2)')
	else:
		plotData = data[:,1]
		plt.ylabel('S-Parameter (dB)')
	if label is None:
		plt.plot(data[:,0] * 1e-9, plotData)
	else:
		plt.plot(data[:,0] * 1e-9, plotData, label=label)
		plt.legend()
	plt.xlabel('frequency (GHz)')
	plt.grid(True)
	plt.tight_layout()

def sParameterFromFilename(files):
	if type(files) is dict:
		s11 = {}
		s12 = {}
		s21 = {}
		s22 = {}
		for fName, fVal in files.items():
			if 'S11' in fName:
				s11.update({fName:fVal})
			if 'S12' in fName:
				s12.update({fName:fVal})
			if 'S21' in fName:
				s21.update({fName:fVal})
			if 'S22' in fName:
				s22.update({fName:fVal})
	else:
		s11 = []
		s12 = []
		s21 = []
		s22 = []
		for f in files:
			if 'S11' in f:
				s11.append(f)
			if 'S12' in f:
				s12.append(f)
			if 'S21' in f:
				s21.append(f)
			if 'S22' in f:
				s22.append(f)
	return s11, s12, s21, s22

def nameUntilS(filename):
	return filename[:filename.find('_S')].lower()

def dBToDezimalPart(dB):
	return 10**(dB/10)

def dezimalToDB(dez):
	return 10 * np.log10(dez)

def calibrate(data, s, reflection=True):
	openC = dBToDezimalPart(data['DISCONNECTED_{}'.format(s)][:,1])
	shortC = dBToDezimalPart(data['SHORT_{}'.format(s)][:,1])
	for n, val in data.items():
		if reflection:
			val[:,1] = (dBToDezimalPart(val[:,1]) - shortC)/(openC - shortC)
		else:
			val[:,1] = (dBToDezimalPart(val[:,1]) - openC)/(shortC - openC)

def getLosses(reflection, transmission, dB=True):
	losses = np.empty_like(reflection)
	if dB:
		ref = dBToDezimalPart(reflection[:,1])
		trans = dBToDezimalPart(transmission[:,1])
	else:
		ref = reflection[:,1]
		trans = transmission[:,1]
	losses[:,0] = reflection[:,0]
	losses[:,1] = dezimalToDB(1 - ref - trans) if dB else 1 - ref - trans
	return losses

def subtractCableLosses(cableLoss, losses, number=1, dB=True):
	carrierLoss = np.empty_like(cableLoss)
	if dB:
		cab = dBToDezimalPart(cableLoss[:,1])
		lo = dBToDezimalPart(losses[:,1])
	else:
		cab = cableLoss[:,1]
		lo = losses[:,1]
	carrierLoss[:,0] = cableLoss[:,0]
	carrierLoss[:,1] = dezimalToDB(lo - cab * number) if dB else lo - cab * number
	return carrierLoss


skipsav = False
thisFile = os.path.realpath(__file__)

if __name__ == '__main__':
	mainfolder = 'C:/Users/od93yces/Data/network_analyzer/'
	folder = mainfolder + 'sma_platine_gross/'
	figureFolder = 'network_analyzer/sma_pcb_big/'
	files = {}
	for file in os.listdir(folder):
		if not os.path.isfile(folder + file):
			continue
		files.update({file[:-4]: np.loadtxt(folder + file, skiprows=3, delimiter=', ')})

	s11, s12, s21, s22 = sParameterFromFilename(files)

	tests = [#'open_completely',
			 #'open_n_adapter',
			 # 'short_one',
			 'short_two_cables',
			 'open_carrier',
			 'bonded']
	labels = ['connection cables', 'open pcb', 'bonded pcb']

	plotDez = True

	for i, n in enumerate(tests):
		for s, val in s11.items():
			name = nameUntilS(s)
			if name.startswith(n):
				refl1 = val
				# plt.figure(11)
				# plotSParameter(val, n, dBtoQuotient=plotDez)
		# for s, val in s22.items():
		# 	name = nameUntilS(s)
		# 	if name.startswith(n):
		# 		refl2 = val
		# 		# plt.figure(22)
		# 		# plotSParameter(val, n, dBtoQuotient=plotDez)
		for s, val in s21.items():
			name = nameUntilS(s)
			if name.startswith(n):
				tran1 = val
				# plt.figure(21)
				# plotSParameter(val, n, dBtoQuotient=plotDez)
		# for s, val in s12.items():
		# 	name = nameUntilS(s)
		# 	if name.startswith(n):
		# 		tran2 = val
		# 		# plt.figure(12)
		# 		# plotSParameter(val, n, dBtoQuotient=plotDez)

		loss1 = getLosses(refl1, tran1)
		# loss2 = getLosses(refl2, tran2)

		plt.figure(1)
		plt.title('losses, port 1')
		plt.tight_layout()
		plotSParameter(loss1, labels[i], dBtoQuotient=False)

		saveFigure(figureFolder + 'new_loss_overview.pdf', callingFileSav=thisFile)
		# plt.figure(2)
		# plt.title('losses port 2')
		# plt.tight_layout()
		# plotSParameter(loss2, n, dBtoQuotient=plotDez)

		# if n == 'short_one':
		# 	plt.figure(1)
		# 	doubleLoss1 = np.empty_like(loss1)
		# 	doubleLoss1[:,0] = loss1[:,0]
		# 	doubleLoss1[:,1] = dezimalToDB(dBToDezimalPart(loss1[:,1]) * 2)
		# 	plotSParameter(doubleLoss1, n + ' * 2', dBtoQuotient=plotDez)
		#
		# 	plt.figure(2)
		# 	doubleLoss2 = np.empty_like(loss2)
		# 	doubleLoss2[:,0] = loss2[:,0]
		# 	doubleLoss2[:,1] = dezimalToDB(dBToDezimalPart(loss2[:,1]) * 2)
		# 	plotSParameter(doubleLoss2, n + ' * 2', dBtoQuotient=plotDez)

	# plt.figure(11)
	# plt.title('S11')
	# plt.tight_layout()
	#
	# plt.figure(22)
	# plt.title('S22')
	# plt.tight_layout()
	#
	# plt.figure(21)
	# plt.title('S21')
	# plt.tight_layout()
	#
	# plt.figure(12)
	# plt.title('S12')
	# plt.tight_layout()

	plt.show()
