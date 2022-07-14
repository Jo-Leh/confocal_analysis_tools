import os
import numpy as np
from scipy.optimize import curve_fit as fit
import matplotlib.pyplot as plt
import matplotlib.cm as colMap
from matplotlib.offsetbox import AnchoredText

# import ODMR_analyzer.utility.odmr_tools.recognizeLAPMeasFile as loadLAP
import ODMR_analyzer.utility.measurement_class as meas_class
from ODMR_analyzer.utility.odmr_tools import analyseODMRFunctions
from calculationTools import fft
import analysis_tools.spectrum_plotting as specPlot



def rectToAmpAndPhase(number:complex):
	amp = np.sqrt(number.real**2 + number.imag**2)
	phase = 2 * np.arctan(number.imag / number.real)
	return amp, phase

def plotRFandFrequOverTime(data:meas_class.OdmrMeasurement):
	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.plot(data.time, data.reflectedPower)
	ax2 = ax.twinx()
	ax2.plot(data.time, data.frequency, color='r')

def plotRFPower(data:meas_class.OdmrMeasurement, fig=0, label=None):
	plt.figure(fig)
	plt.plot(data.frequency, data.reflectedPower, label=label)

def FFT(x_data, y_data, half=False, addN=0, subtractOffset=False):
	if subtractOffset:
		fi = fit(lambda x, c: c, x_data, y_data)
		y = y_data - fi[0][0]
	else:
		y = y_data
	x = x_data
	n = len(x) + addN
	fftY = np.fft.fft(y, n)
	dt = x[1] - x[0]
	fftX = np.fft.fftfreq(n, dt)
	if half:
		return fftX[:n//2], fftY[:n//2]
	return fftX, fftY

def inverseFFT(x, y, half=False):
	ifftY = np.fft.ifft(y)
	n = len(x)
	dt = np.abs(x[1] - x[0])
	ifftX = np.linspace(0, 1/dt, n)
	if half:
		return ifftX[:len(ifftX)//2], ifftY[:len(ifftY)//2]
	return ifftX, ifftY

def plotODMRSignal(data:meas_class.OdmrMeasurement, colors=(), errors=False, labels=('',''), averageAPDs=True, dotNotLine=False, splitUpDown=False, shifter=0, addax=None, ax1_ax2_fig=(None, None, None), inPercent=False, frequScale='Hz'):
	if ax1_ax2_fig[0] is None:
		fig, ax1 = plt.subplots()
	else:
		ax1 = ax1_ax2_fig[0]
		fig = ax1_ax2_fig[2]
	ls = 'o' if dotNotLine else '-'
	if dotNotLine and splitUpDown:
		ls = '^'
	ls2 = 'x' if dotNotLine else '--'
	if len(colors) == 0:
		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
	if frequScale is 'Hz':
		frequScaling = 1
	elif frequScale == 'MHz':
		frequScaling = 1e-6
	elif frequScale == 'GHz':
		frequScaling = 1e-9
	else:
		raise Exception('Not a valid frequency scale!')
	if inPercent:
		ax1.plot(frequScaling * data.filterFrequ, 100 * (data.sigAvgPercent + shifter), ls, color=colors[0], label=labels[0], markersize=3)
	else:
		if splitUpDown:
			if not averageAPDs:
				ax1.plot(frequScaling * data.filterFrequ, data.sigUp0 + shifter, ls, color=colors[0], label=labels[0], markersize=3)
				ax1.plot(frequScaling * data.filterFrequ, data.sigUp1 + shifter, ls, color=colors[1], label=labels[1])
				ax1.plot(frequScaling * data.filterFrequ, data.sigDown0 + shifter, ls2, color=colors[0], label=labels[0], markersize=3)
				ax1.plot(frequScaling * data.filterFrequ, data.sigDown1 + shifter, ls2, color=colors[1], label=labels[1])
			else:
				ax1.plot(frequScaling * data.filterFrequ, data.sigAvgUp + shifter, ls, color=colors[0], label=labels[0], markersize=3)
				if len(colors) > 1:
					ax1.plot(frequScaling * data.filterFrequ, data.sigAvgDown + shifter, ls2, color=colors[1], label=labels[1], markersize=3)
				else:
					ax1.plot(frequScaling * data.filterFrequ, data.sigAvgDown + shifter, ls2, color=colors[0], label=labels[0], markersize=3)
		else:
			if not averageAPDs:
				ax1.plot(frequScaling * data.filterFrequ, data.signal0 + shifter, ls, color=colors[0], label=labels[0], markersize=3)
				ax1.plot(frequScaling * data.filterFrequ, data.signal1 + shifter, ls, color=colors[1], label=labels[1])
			else:
				ax1.plot(frequScaling * data.filterFrequ, data.sigAvg + shifter, ls, color=colors[0], label=labels[0], markersize=3)
			if errors:
				ax1.plot(frequScaling * data.filterFrequ, data.signal0 + shifter + data.sigError0 + shifter, '--', color=colors[0])
				ax1.plot(frequScaling * data.filterFrequ, data.signal0 + shifter - data.sigError0 + shifter, '--', color=colors[0])
				if not averageAPDs:
					ax1.plot(frequScaling * data.filterFrequ, data.signal1 + shifter + data.sigError1 + shifter, '--', color=colors[1])
					ax1.plot(frequScaling * data.filterFrequ, data.signal1 + shifter - data.sigError1 + shifter, '--', color=colors[1])
	if len(labels[0]) > 0:
		ax1.legend()
	ax1.set_xlabel('frequency ({})'.format(frequScale))
	if inPercent:
		ax1.set_ylabel('ODMR-signal (%)')
	else:
		ax1.set_ylabel('contrast (a.u.)')
	fig.set_tight_layout(True)
	if addax is not None:
		if ax1_ax2_fig[1] is None:
			ax2 = ax1.twinx()
		else:
			ax2 = ax1_ax2_fig[1]
		ax2.plot(data.frequency, data.__dict__[addax], color=colors[2])
		ax2.set_ylabel(addax)
		return ax1, ax2, fig
	return ax1, None, fig
	# plt.show()

def loadODMRFile(file):
	return meas_class.OdmrMeasurement(file)

def plotODMR(data:meas_class.OdmrMeasurement, colors=(), averaging=False, errors=False, labels=('', '')):
	if len(colors) == 0:
		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
	if averaging:
		plt.plot(data.filterFrequ, data.avgCounts0, color=colors[0], label=labels[0])
		plt.plot(data.filterFrequ, data.avgCounts1, color=colors[1], label=labels[1])
		if errors:
			plt.plot(data.filterFrequ, data.avgCounts0 + data.avgErrors0, '--', color=colors[0])
			plt.plot(data.filterFrequ, data.avgCounts0 - data.avgErrors0, '--', color=colors[0])
			plt.plot(data.filterFrequ, data.avgCounts1 + data.avgErrors1, '--', color=colors[1])
			plt.plot(data.filterFrequ, data.avgCounts1 - data.avgErrors1, '--', color=colors[1])
	else:
		plt.plot(data.frequency, data.countRate0, color=colors[0], label=labels[0])
		plt.plot(data.frequency, data.countRate1, color=colors[1], label=labels[1])
	if len(labels[0]) > 0:
		plt.legend()
	plt.xlabel('Frequency (Hz)')
	plt.ylabel('countrate (1/s)')
	plt.tight_layout()

def printValueDic(valueDic:dict):
	for key, val in valueDic.items():
		print('{}:\t{:.3E}'.format(key, val))

def loaddBmSweep(folder):
	if not folder.endswith('/'):
		folder += '/'
	files = []
	dBms = []
	for f in os.listdir(folder):
		dBms.append(float(f.split('dBm')[0]))
		files.append(f)
	fList = [x for y,x in sorted(zip(dBms, files))]
	datList = []
	for f in fList:
		datList.append(loadODMRFile(folder + f))
	return datList, sorted(dBms)

def plotODMRfit(xVals, fitVals, color, frequScale='Hz', n=2, inPercent=False, shifter=0):
	contrasts = []
	mids = []
	linewidths = []
	distances = []
	for k in fitVals.keys():
		if k.endswith('contrast'):
			contrasts.append(fitVals[k])
		if k.endswith('mid'):
			mids.append(fitVals[k])
		if k.endswith('linewidth'):
			linewidths.append(fitVals[k])
		if k.endswith('distance'):
			distances.append(fitVals[k])
	if frequScale == 'Hz':
		frequScaling = 1
	elif frequScale == 'MHz':
		frequScaling = 1e-6
	elif frequScale == 'GHz':
		frequScaling = 1e-9
	else:
		raise Exception('"{}" is not a valid frequency scale!'.format(frequScale))
	if inPercent:
		func = lambda x: fitVals['p0_y0'] + analyseODMRFunctions.splittedLorentz(x, contrasts, mids, linewidths, distances, n)
	else:
		func = lambda x: fitVals['p0_y0'] * (1 - analyseODMRFunctions.splittedLorentz(x, contrasts, mids, linewidths, distances, n))
	testfunc = lambda x: fitVals['p0_y0'] + analyseODMRFunctions.splittedLorentz(x, 2e-3, mids, linewidths, distances, n)
	percenter = 100 if inPercent else 1
	plt.plot(frequScaling * xVals, percenter * (func(xVals) + shifter), color=color)
	# plt.plot(frequScaling * xVals, percenter * testfunc(xVals), color=color)



def getSplittedColormap(nTot, name):
	return [colMap.get_cmap(name)(x) for x in np.linspace(0, 1, nTot)]



thisfile = 'C:/Users/od93yces/PycharmProjects/analysis_tools/odmr_plotting.py'
stdColors = plt.rcParams['axes.prop_cycle'].by_key()['color']
fiveColorHeat = getSplittedColormap(5, 'coolwarm')
fiveColorHeat.append('t')

if __name__ == "__main__":
	files30dBm = [r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\CH-03\2020-09-07_VSi\2020-09-07_areaD_pos2_RT_671nm_OD1_900LP_dBm_A_loop_1sAvg_very_precise\-30dBm_0A_sweep_000.txt",
		r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\CH-03\2020-09-07_VSi\2020-09-07_areaD_pos2_RT_671nm_OD1_900LP_dBm_A_loop_1sAvg_very_precise\-30dBm_0.2A_sweep.txt",
		r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\CH-03\2020-09-07_VSi\2020-09-07_areaD_pos2_RT_671nm_OD1_900LP_dBm_A_loop_1sAvg_very_precise\-30dBm_0.4A_sweep.txt"]
	labels = ['no field', '200 mA', '400 mA', '']

	cols = stdColors

	# bounds = {'p0_contrast': (-np.inf, 0)}
	axes_fig = None
	for i, f in enumerate(files30dBm):
		data = loadODMRFile(f)
		fit = analyseODMRFunctions.multipleFit(data.filterFrequ, data.sigAvgPercent, 2e-3, 70e6, 2e6, 5e6, y0=0, type='peak')
		print(fit.best_values)
		y0 = fit.best_values['p0_y0']
		if axes_fig is None:
			axes_fig = plotODMRSignal(data, colors=(cols[i], cols[i + 1]), labels=labels[i:], dotNotLine=True, inPercent=True, frequScale='MHz', shifter=-y0)
		else:
			plotODMRSignal(data, ax1_ax2_fig=axes_fig, colors=(cols[i], cols[i + 1]), labels=labels[i:], dotNotLine=True, inPercent=True, frequScale='MHz', shifter=-y0)
		plotODMRfit(data.filterFrequ, fit.best_values, cols[i], frequScale='MHz', inPercent=True, shifter=-y0)
	plt.show()
	# axes_fig[2].tight_layout()
	# plotFunc.saveFigure('ODMR/CH-03/2020-09-07_areaD_-30dBm_900LP_671nm_OD2total_inPercent.pdf')
	# bounds = {'contrast': (0, np.inf),
	# 		  'mid': (0, np.inf),
	# 		  'linewidth': (0, np.inf),
	# 		  'distance': (0, np.inf)}

	# f0 = r"\\confocal1\LAP Measurements Data\Johannes\ODMR\saarbruecken_diamond\2020-07-01_RT_OD2_572LP_850SP_-20dBm_no_field\ODMR_sweep_000.txt"
	# f_1 = r"\\confocal1\LAP Measurements Data\Johannes\ODMR\saarbruecken_diamond\2020-07-01_RT_OD2_572LP_850SP_-20dBm_-100mA\ODMR_sweep.txt"
	# f_2 = r"\\confocal1\LAP Measurements Data\Johannes\ODMR\saarbruecken_diamond\2020-07-01_RT_OD2_572LP_850SP_-20dBm_-250mA\ODMR_sweep.txt"
	# f1 = r"\\confocal1\LAP Measurements Data\Johannes\ODMR\saarbruecken_diamond\2020-07-01_RT_OD2_572LP_850SP_-20dBm_100mA\ODMR_sweep.txt"
	# f2 = r"\\confocal1\LAP Measurements Data\Johannes\ODMR\saarbruecken_diamond\2020-07-01_RT_OD2_572LP_850SP_-20dBm_250mA\ODMR_sweep.txt"
	# d0 = loadODMRFile(f0)
	# d1 = loadODMRFile(f1)
	# d2 = loadODMRFile(f2)
	# d_1 = loadODMRFile(f_1)
	# d_2 = loadODMRFile(f_2)
	# ax1ax2fig = plotODMRSignal(d_2, dotNotLine=False, colors=fiveColorHeat[0:], labels=('-250 mA', ''))
	# plotODMRSignal(d_1, dotNotLine=False, ax1_ax2_fig=ax1ax2fig, colors=fiveColorHeat[1:], labels=('-100 mA', ''))
	# plotODMRSignal(d0, dotNotLine=False, ax1_ax2_fig=ax1ax2fig, colors=fiveColorHeat[2:], labels=('no field', ''))
	# plotODMRSignal(d1, dotNotLine=False, ax1_ax2_fig=ax1ax2fig, colors=fiveColorHeat[3:], labels=('100 mA', ''))
	# plotODMRSignal(d2, dotNotLine=False, ax1_ax2_fig=ax1ax2fig, colors=fiveColorHeat[4:], labels=('250 mA', ''))
	#
	# specPlot.saveFigure('ODMR/saarbruecken_diamond/2020-07-01_full_field_comparison.pdf', callingFileSav=thisfile)
	# out = analyseODMRFunctions.multipleFit(d1.filterFrequ, d1.sigAvg, [5e-3, 5e-3], [2.87e9, 2.87e9], [1e6, 1e6], [4e6, 8e6], 4, vary={'p0_mid':False, 'p1_mid':False})
	# out = analyseODMRFunctions.multipleFit(d1.filterFrequ, d1.sigAvg, 5e-3, 2.87e9, 3e6, 5e6, 2)
	# vals = out.best_values
	# plotODMRfit(d1.filterFrequ, vals, stdColors[0], 4)
	# plt.plot(dat.filterFrequ, analyseODMRFunctions.splittedODMRLorentz(x=dat.filterFrequ, byKeyWord=vals), color=colors[1])
	# printValueDic(vals)

	# measBasePath = 'C:/Users/od93yces/Data/confocal_LAP_measurements/ODMR/'
	# measpath = measBasePath + 'CH_3/2020-02-27_750nmLP_850nmSP_635nm_OD1/'
	# path = 'C:/Users/od93yces/Data/confocal_LAP_measurements/ODMR/saarbruecken_diamond/2020-02-26_P_sweeps_30_to_10'
	# d = 'C:/Users/od93yces/Data/confocal_LAP_measurements/ODMR/saarbruecken_diamond/2020-02-25_pos_1_OD3_warmed_up_narrow/ODMR_sweep.txt'
	#
	# dnew = 'C:/Users/od93yces/Data/confocal_LAP_measurements/ODMR/saarbruecken_diamond/2020-03-18_inside_cryo_OD3_572LP_refocused/5dBm_sweep.txt'
	# dold = 'C:/Users/od93yces/Data/confocal_LAP_measurements/ODMR/saarbruecken_diamond/2020-02-26_P_sweeps_30_to_10/-20dBm_sweep.txt'
	#
	# colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
	#
	# off = r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\saarbruecken_diamond\2020-05-15_magnet_test\2020-05-15_RT_no_cryo_magnet_532nm_OD2_572LP_850SP_-20dBm_lf_RF_OFF\ODMR_sweep.txt"
	# on20 = r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\saarbruecken_diamond\2020-05-15_magnet_test\2020-05-15_RT_no_cryo_magnet_532nm_OD2_572LP_850SP_-20dBm_lf\ODMR_sweep.txt"
	# on15 = r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\saarbruecken_diamond\2020-05-15_magnet_test\2020-05-15_RT_no_cryo_magnet_532nm_OD2_572LP_850SP_-15dBm_lf\ODMR_sweep_001.txt"
	#
	# dat = loadODMRFile(off)
	# axFig = plotODMRSignal(dat, averageAPDs=True, dotNotLine=True, colors=[colors[0]], labels=['RF off'])
	#
	# dat = loadODMRFile(on20)
	# plotODMRSignal(dat, averageAPDs=True, dotNotLine=True, colors=[colors[1]], labels=['$P_{in} = -20$ dBm'], ax1_ax2_fig=axFig)
	# out = analyseODMRFunctions.splittedODMRFit(dat.filterFrequ, dat.sigAvg, 0.01, 1.4e9, 1e8, 2e8, bounds=bounds)
	# vals = out.best_values
	# plt.plot(dat.filterFrequ, analyseODMRFunctions.splittedODMRLorentz(x=dat.filterFrequ, byKeyWord=vals), color=colors[1])
	# printValueDic(vals)
	#
	# f = r"C:\Users\od93yces\Data\confocal_LAP_measurements\ODMR\CH-03\2020-05-12_TS_closer\2020-05-12_areaA_4K_635nm_OD1_-5dBm_750LP_850SP_rf_1680_1800\countrate_temperature.txt"
	# d = loadODMRFile(f)
	# plotRFPower(d)
	# dat = loadODMRFile(on15)
	# plotODMRSignal(dat, averageAPDs=True, dotNotLine=True, colors=[colors[2]], labels=['$P_{in} = -15$ dBm'], ax1_ax2_fig=axFig)
	# out = analyseODMRFunctions.splittedODMRFit(dat.filterFrequ, dat.sigAvg, 0.01, 1.4e9, 1e8, 2e8, bounds=bounds)
	# vals = out.best_values
	# plt.plot(dat.filterFrequ, analyseODMRFunctions.splittedODMRLorentz(x=dat.filterFrequ, byKeyWord=vals), color=colors[2])
	# printValueDic(vals)
	#
	# specPlot.saveFigure('ODMR/saarbruecken_diamond/2020-05-15_magnet.pdf')
	# text = 'middle: {:.3E} Hz\nlinewidth: {:.3E} Hz\ndistance: {:.3E} Hz'.format(vals['mid'], vals['linewidth'], vals['distance'])
	# plt.annotate(text, (0.65, 0.05), xycoords='axes fraction')

	# ax1_ax2_fig = plotODMRSignal(t1, averageAPDs=True, colors=[colors[0]], labels=['focus 1'])
	# plotODMRSignal(t2, averageAPDs=True, ax1_ax2_fig=ax1_ax2_fig, colors=[colors[1]], labels=['focus 2'])
	# plotODMRSignal(h, averageAPDs=True, ax1_ax2_fig=ax1_ax2_fig, colors=[colors[2]], labels=['focus 2, faster meas'])
	# plotODMRSignal(b, averageAPDs=True, ax1_ax2_fig=ax1_ax2_fig, colors=[colors[3]], labels=['focus 3'])
	# specPlot.saveFigure('ODMR/CH_03/2020-04-22_TS_broken_diff_focus.pdf')

	# dat0 = loadODMRFile(d0)
	# dat1 = loadODMRFile(d1)
	# dat2 = loadODMRFile(d2)

	# plotODMRSignal(dat, averageAPDs=True, dotNotLine=False, colors=[colors[0], colors[1]], labels=['up-sweep', 'down-sweep'], splitUpDown=True)
	# plotODMRSignal(dat1, averageAPDs=True, dotNotLine=True, colors=[colors[1]], labels=['position 1'])
	# plotODMRSignal(dat2, averageAPDs=True, dotNotLine=True, colors=[colors[2]], labels=['position 2'])

	# specPlot.saveFigure('ODMR/CH_03/2020-04-21_VSi_test_4K_upDownComp_pos3.pdf', callingFileSav=thisfile)


	# dat = loadODMRFile(dold)
	# plotODMRSignal(dat, averageAPDs=True, dotNotLine=True, colors=[colors[0]], labels=['old setup'])
	# out = analyseODMRFunctions.splittedODMRFit(dat.filterFrequ, dat.sigAvg, 0.1, 2.87e9, 5e6, 4e6)
	# vals = out.best_values
	# plt.plot(dat.filterFrequ, analyseODMRFunctions.splittedODMRLorentz(x=dat.filterFrequ, byKeyWord=vals), color=colors[0])
	# printValueDic(vals)
	#
	# dat = loadODMRFile(dnew)
	# plotODMRSignal(dat, averageAPDs=True, dotNotLine=True, colors=[colors[1]], labels=['inside cryo'])
	# out = analyseODMRFunctions.splittedODMRFit(dat.filterFrequ, dat.sigAvg, 0.1, 2.87e9, 5e6, 4e6)
	# vals = out.best_values
	# plt.plot(dat.filterFrequ, analyseODMRFunctions.splittedODMRLorentz(x=dat.filterFrequ, byKeyWord=vals), color=colors[1])
	# printValueDic(vals)
	# # text = 'middle: {:.3E} Hz\nlinewidth: {:.3E} Hz\ndistance: {:.3E} Hz'.format(vals['mid'], vals['linewidth'], vals['distance'])
	# # plt.annotate(text, (0.65, 0.05), xycoords='axes fraction')
	# plt.xlim(2.848e9, 2.892e9)
	# plt.tight_layout()
	# specPlot.saveFigure('ODMR/saarbruecken_diamond/2020-03-18_inside_cryo_vs_old_setup.pdf')


	# data, dbms = loaddBmSweep(path)
	#
	# for i, dat in enumerate(data):
	# 	plt.figure(i)
	# 	plotODMRSignal(dat, averageAPDs=True, dotNotLine=True)
	# 	out = analyseODMRFunctions.splittedODMRFit(dat.filterFrequ, dat.sigAvg, 0.1, 2.87e9, 5e6, 4e6)
	# 	vals = out.best_values
	# 	plt.plot(dat.filterFrequ, analyseODMRFunctions.splittedODMRLorentz(x=dat.filterFrequ, byKeyWord=vals), color='r')
	# 	print(dbms[i])
	# 	printValueDic(vals)
	# 	print('')
	# 	text = 'middle: {:.3E} Hz\nlinewidth: {:.3E} Hz\ndistance: {:.3E} Hz'.format(vals['mid'], vals['linewidth'], vals['distance'])
	# 	plt.annotate(text, (0.65, 0.05), xycoords='axes fraction')
	# 	plt.tight_layout()
	# 	specPlot.saveFigure('ODMR/saarbruecken_diamond/2020-02-26_P_sweep_{}dBm.pdf'.format(dbms[i]))
	# 	# plt.show()



	# d1 = measpath + '2020-02-06_defect_1_OD1_RF_on_wider_range/countrate_000.txt'
	# d2 = measpath + '2020-02-07_ODMR_defect_1/countrate_001.txt'
	# ds = [d1, d2]
	# basecolors = plt.rcParams['axes.prop_cycle'].by_key()['color']
	# cols1 = basecolors[0:2]
	# cols2 = basecolors[2:4]
	# cols = [cols1, cols2]
	# labs = [['A - 1', 'A - 2'], ['B - 1', 'B - 2']]
	# for i, d in enumerate(ds):
	# 	dat = loadODMRFile(d).shortenFrequ(2e9,2.5e9)
	# 	upSweeps, downSweeps = dat.measesFromSingleSweeps()
	# 	for sweep in upSweeps:
	# 		plt.figure(0)
	# 		plt.plot(sweep.time, sweep.countRate0, color=cols1[i])
	# 		plt.figure(1)
	# 		frequ, vals = FFT(sweep.time, sweep.countRate0, half=True, subtractOffset=False)
	# 		plt.plot(frequ[1:], rectToAmpAndPhase(vals[1:])[0], color=cols1[i])
	# 		plt.figure(2)
	# 		time, vals = inverseFFT(sweep.filterFrequ, sweep.countRate0, half=True)
	# 		plt.plot(time[1:], rectToAmpAndPhase(vals[1:])[0], color=cols1[i])
	# 		# print(sweep.time[-1] - sweep.time[0])
	# 	for sweep in downSweeps:
	# 		plt.figure(0)
	# 		plt.plot(sweep.time, sweep.countRate0, color=cols1[i])
	# 		plt.figure(1)
	# 		frequ, vals = FFT(sweep.time, sweep.countRate0, half=True, subtractOffset=False)
	# 		plt.plot(frequ[1:], rectToAmpAndPhase(vals[1:])[0], color=cols1[i])
	# 		plt.figure(2)
	# 		time, vals = inverseFFT(sweep.filterFrequ, sweep.countRate0, half=True)
	# 		plt.plot(time[1:], rectToAmpAndPhase(vals[1:])[0], color=cols1[i])
	# 		# print(sweep.time[-1] - sweep.time[0])
	# 		# plt.figure(2)
	# 		# time, counts = inverseFFT(frequ, vals)
	# 		# plt.plot(time, counts)
	#
	# plt.figure(1)
	# plt.xlabel('frequency (Hz)')
	# plt.ylabel('FFT(countrate)')
	# # plt.title('fourier-transform: countrate(measurement-time)')
	# plt.xlim(0, 0.22)
	# plt.tight_layout()
	# specPlot.saveFigure('NV_nanodiamonds/2020-02-06_XY_hand_stage/defects_AB_APD1_fourier_time_small.pdf')
	#
	# plt.figure(2)
	# plt.xlabel('time (s)')
	# plt.ylabel('FFT(countrate)')
	# # plt.title('fourier-transform: countrate(excitation-frequency)')
	# plt.xlim(0, 6e-8)
	# plt.tight_layout()
	# specPlot.saveFigure('NV_nanodiamonds/2020-02-06_XY_hand_stage/defects_AB_APD1_fourier_frequency_small.pdf')

	# plt.semilogx()
	# plt.figure(0)
	# plotODMR(dat, averaging=False, errors=False, colors=cols[i], labels=labs[i])
	# plt.figure(1)
	# plotODMR(dat, averaging=True, errors=False, colors=cols[i], labels=labs[i])
	# plt.figure(2)
	# plotODMRSignal(dat, errors=False, colors=cols[i], labels=labs[i])
	# plt.figure(3)
	# if i == 0:
	# 	plotODMRSignal(dat.shortenFrequ(2.9e9, 3.2e9), errors=False, colors=cols[i], labels=labs[i])

	# plt.figure(0)
	# specPlot.saveFigure('NV_nanodiamonds/XY_hand_stage/defects_AB_raw.pdf')
	# plt.figure(1)
	# specPlot.saveFigure('NV_nanodiamonds/XY_hand_stage/defects_AB_avg.pdf')
	# plt.figure(2)
	# specPlot.saveFigure('NV_nanodiamonds/XY_hand_stage/defects_AB_signal.pdf')
	# plt.figure(3)
	# specPlot.saveFigure('NV_nanodiamonds/XY_hand_stage/defect_A_signal_small.pdf')

	# d3 = measpath + '2020-01-24_ODMR_defect_3/countrate.txt'
	# d4 = measpath + '2020-01-24_ODMR_defect_4/countrate_002.txt'
	# d5 = measpath + '2020-01-24_ODMR_defect_5/countrate_000.txt'
	# d6 = measpath + '2020-01-24_ODMR_defect_6_further_from_wire/countrate_000.txt'
	# d61 = measpath + '2020-01-24_ODMR_defect_6_comparison_no_RF/countrate.txt'
	# d62 = measpath + '2020-01-24_ODMR_defect_6_again_with_RF/countrate.txt'
	#
	# ds = [d3, d4, d6]
	# meases = []
	# colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
	# names = ['3', '4', '6']
	# for i, d in enumerate(ds):
	# 	odmrFile = loadODMRFile(d)
	# 	plotSignal(odmrFile.countsUp0, odmrFile.filterFrequ, label=names[i], color=colors[i])
	# 	plotSignal(odmrFile.countsDown0, odmrFile.filterFrequ, ls='--', color=colors[i])
	#
	# specPlot.saveFigure('nanodiamond_NV/odmr_defects_3_4_6.pdf')


	# measpath = measBasePath + 'CH_3/'
	#
	# # files = ['odmr_test/a_000.txt',
	# # 		 'odmr_test_2/a_001.txt',
	# # 		 'odmr_test_ref/a.txt',
	# # 		 'odmr_test_ref_2/a.txt',
	# # 		 'odmr_test_3/a.txt',
	# # 		 'odmr_test_3_ref/a.txt']
	# #
	# # data = []
	# #
	# # for i, f in enumerate(files):
	# # 	data.append(np.loadtxt(measpath + f, skiprows=1))
	# # 	plotSignal(data[i][:,1], data[i][:,2], label=i)
	#
	#
	# measpath = measBasePath + 'ODMR/NV/2019-11-14_RT_confocal_OD1_532nm_f575L_f850S_0-1s_RF7/countrate.txt'
	# data = loadODMRFile(measpath)
	# plotODMR(data, False)
	# # plotODMR(data)
	# # data = np.loadtxt(measpath, skiprows=2)
	# # ax = plt.subplot()
	# # ax.ticklabel_format(axis='both', style='sci', scilimits=(-2,4), useOffset=False)
	# # ax.plot(data[:,0], data[:,2])
	# # ax.plot(data[:,0], data[:,3])
	# # ax.set_xlabel('time (s)')
	# # ax.set_ylabel('countrate (1/s)')
	#
	# # ax2 = plt.twinx(ax)
	# # ax2.ticklabel_format(axis='both', style='sci', scilimits=(-2,4), useOffset=False)
	# # ax2.plot(data[:,0], data[:,3], color='green')
	# # ax2.set_ylabel('power (W)')
	#
	# # avg0 = np.mean(data[:,1])
	# # avg1 = np.mean(data[:,2])
	# # avgP = np.mean(data[:,3])
	# #
	# # axAvg = plt.subplot()
	# # axAvg.ticklabel_format(axis='both', style='sci', scilimits=(-2,4), useOffset=False)
	# # axAvg.plot(data[:,0], data[:,1] - avg0)
	# # axAvg.plot(data[:,0], data[:,2] - avg1)
	# # axAvg.set_xlabel('time (s)')
	# # axAvg.set_ylabel('countrate (1/s)')
	# #
	# # axAvg2 = plt.twinx(axAvg)
	# # axAvg2.ticklabel_format(axis='both', style='sci', scilimits=(-2,4), useOffset=False)
	# # axAvg2.plot(data[:,0], data[:,3] - avgP, color='green')
	# # axAvg2.set_ylabel('power (W)')




	plt.show()
	plt.close('all')
