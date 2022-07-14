import numpy as np

import Confocal_analyzer.utility.odmr_tools.recognizeLAPMeasFile as loadLAP

def avgAndStdDev(vals):
	if type(vals) is list:
		vals = np.asarray(vals)
	n = len(vals)
	if n == 0:
		return 0, 0
	avg = vals.mean()
	sq = sum((vals - avg)**2)
	return avg, np.sqrt(1/n * sq)


class MeasurementClass:
	def __init__(self, dataSet):
		xCoorsRed = []
		yCoorsRed = []
		Volts = []
		Frequs = []
		self.data = dataSet

		for i in range(0, np.shape(self.data)[0]):
			xCoorsRed.append(self.data[i][1][1])
			yCoorsRed.append(self.data[i][1][2])
			Volts.append(self.data[i][1][0])
			Frequs.append(self.data[i][1][3])

		self.xCoors = sorted(list(set(xCoorsRed)))
		self.yCoors = sorted(list(set(yCoorsRed)))
		self.voltages = sorted(list(set(Volts)))
		self.frequencies = sorted(list(set(Frequs)))

		self.nrXpos = len(self.xCoors)
		self.nrYpos = len(self.yCoors)
		self.nrVoltages = len(self.voltages)
		self.nrFrequencies = len(self.frequencies)
		#########END

		self.lambda_min = self.data[0][2].spectrum[:, 0][0]
		self.lambda_max = self.data[0][2].spectrum[:, 0][-1]


class OdmrMeasurement:
	def __init__(self, info, peakOrDip=None):
		if type(info) is str:
			info = loadLAP.loadLAPFile(info)
		for key, value in info.items():
			if key == 'Time:Elapsed' or key == 'Time (s)':
				self.time = value
			elif key == 'TIC:In 1':
				self.temperature = value
			elif key == 'RF-Power:ConvertedPower' or key == 'RF-Power (dBm)':
				self.reflectedPower = value
		try:
			self.countRate0 = info['TTCountrate:Channel0']
			self.lockIn = False
		except:
			try:
				self.countRate0 = info['Countrate0 (1/s)']
				self.lockIn = False
			except:
				self.countRate0 = info['lockIn:X']
				self.lockIn = True
		try:
			self.countRate1 = info['TTCountrate:Channel1']
		except:
			try:
				self.countRate1 = info['Countrate1 (1/s)']
			except:
				self.countRate1 = info['lockIn:Y']
		try:
			self.frequency = info['SG380:Frequency']
		except:
			try:
				self.frequency = info['Frequency (Hz)']
			except:
				self.frequency = info['piezo:Value']
		self.countsUp0, self.countsUp1, self.countsDown0, self.countsDown1 = [None]*4
		self.errorsUp0, self.errorsUp1, self.errorsDown0, self.errorsDown1 = [None] * 4
		self.avgErrors0, self.avgErrors1 = [None] * 2
		self.upSweeps0 = []
		self.downSweeps0 = []
		self.upSweeps1 = []
		self.downSweeps1 = []
		self.upSweepTimes = []
		self.downSweepTimes = []
		self.sigUp0 = self.sigUp1 = self.sigAvgUp = self.sigDown0 = self.sigDown1 = self.sigAvgDown = None
		self.signal0 = self.signal1 = self.sigError0 = self.sigError1 = self.sigAvg = self.sigAvgError = None
		self.sweepwiseUp0 = self.sweepwiseUp1 = self.sweepwiseDown0 = self.sweepwiseDown1 = None
		self.sweepwiseUpAvg = self.sweepwiseDownAvg = self.sweepwise0 = self.sweepwise1 = self.sweepwiseAvg = None
		self.sigAvgPercent = None
		try:
			self.lockInR = info['lockIn:R']
		except:
			self.lockInR = None
		if 'SwitchState' in info.keys():
			self.switchStates = info['SwitchState']
			self.filterFrequ, self.avgPercent0, self.avgPercent1 = self.simpleLockInMeas()
			self.sigAvgPercent = (self.avgPercent0 + self.avgPercent1) / 2
		else:
			self.filterFrequ, self.avgCounts0, self.avgCounts1 = self.makeAverage()
			self.getODMRinP(dipOrPeak=peakOrDip)
		try:
			self.getSweepTimePos()
		except:
			print('no time-data found')

	def simpleLockInMeas(self):
		m = np.where(self.frequency == max(self.frequency))[0][0] + 2
		if m == 1:
			m = np.where(self.frequency == min(self.frequency))[0][0] + 2
		frequs = self.frequency[:m:2]
		counts0 = np.zeros_like(frequs)
		counts1 = np.zeros_like(frequs)
		self.avgErrors0 = np.zeros_like(frequs)
		self.avgErrors1 = np.zeros_like(frequs)
		# self.countsUp0 = np.zeros_like(frequs)
		# self.countsUp1 = np.zeros_like(frequs)
		# self.countsDown0 = np.zeros_like(frequs)
		# self.countsDown1 = np.zeros_like(frequs)
		# self.errorsUp0 = np.zeros_like(frequs)
		# self.errorsUp1 = np.zeros_like(frequs)
		# self.errorsDown0 = np.zeros_like(frequs)
		# self.errorsDown1 = np.zeros_like(frequs)
		for i, f in enumerate(frequs):
			# valsUp0 = []
			# valsDown0 = []
			vals0_0 = []
			vals0_1 = []
			# valsUp1 = []
			# valsDown1 = []
			vals1_0 = []
			vals1_1 = []
			positions = np.where(self.frequency == f)
			for p in positions[0]:
				# counts0[i] += self.countRate0[p] / len(positions[0])
				# counts1[i] += self.countRate1[p] / len(positions[0])
				if self.switchStates[p] == 0:
					vals0_0.append(self.countRate0[p])
					vals1_0.append(self.countRate1[p])
				else:
					vals0_1.append(self.countRate0[p])
					vals1_1.append(self.countRate1[p])
				# if p == 0 or (self.frequency[p-1] < self.frequency[p]) or (self.frequency[p] == f and self.frequency[p-1] == f and self.frequency[p-2] > f):
				# 	# self.countsUp0[i] += self.countRate0[p]
				# 	# self.countsUp1[i] += self.countRate1[p]
				# 	valsUp0.append(self.countRate0[p])
				# 	valsUp1.append(self.countRate1[p])
				# else:
				# 	valsDown0.append(self.countRate0[p])
				# 	valsDown1.append(self.countRate1[p])
			vals0_0 = np.array(vals0_0)
			vals1_0 = np.array(vals1_0)
			vals0_1 = np.array(vals0_1)
			vals1_1 = np.array(vals1_1)
			vals0 = vals0_0 / vals0_1
			vals1 = vals1_0 / vals1_1
			counts0[i], self.avgErrors0[i] = avgAndStdDev(np.asarray(vals0))
			counts1[i], self.avgErrors1[i] = avgAndStdDev(np.asarray(vals1))
			# self.countsUp0[i], self.errorsUp0[i] = avgAndStdDev(np.asarray(valsUp0))
			# self.countsUp1[i], self.errorsUp1[i] = avgAndStdDev(np.asarray(valsUp1))
			# self.countsDown0[i], self.errorsDown0[i] = avgAndStdDev(np.asarray(valsDown0))
			# self.countsDown1[i], self.errorsDown1[i] = avgAndStdDev(np.asarray(valsDown1))
			# self.countsUp0[i] /= nUp if nUp > 0 else 1
			# self.countsUp1[i] /= nUp if nUp > 0 else 1
			# self.countsDown0[i] /= nDown if nDown > 0 else 1
			# self.countsDown1[i] /= nDown if nDown > 0 else 1
		return frequs, counts0, counts1


	def getODMRinP(self, dipOrPeak=None):
		m0 = max(self.avgCounts0) if max(self.avgCounts0) > 0 else 1
		m1 = max(self.avgCounts1) if max(self.avgCounts1) > 0 else 1
		self.signal0 = self.avgCounts0 / m0
		self.signal1 = self.avgCounts1 / m1
		self.sigError0 = self.avgErrors0 / m0
		self.sigError1 = self.avgErrors1 / m1
		self.sigAvg = (self.signal0 + self.signal1) / 2
		self.sigAvgError = (self.sigError0 + self.sigError1) / 2

		u0 = max(self.countsUp0)
		u1 = max(self.countsUp1)
		d0 = max(self.countsDown0)
		d1 = max(self.countsDown1)
		if u0 > 0:
			self.sigUp0 = self.countsUp0 / u0
			self.sigUp1 = self.countsUp1 / u1
			self.sigAvgUp = (self.sigUp0 + self.sigUp1) / 2
		if d0 > 0:
			self.sigDown0 = self.countsDown0 / d0
			self.sigDown1 = self.countsDown1 / d1
			self.sigAvgDown = (self.sigDown0 + self.sigDown1) / 2
		if dipOrPeak is None:
			mid = (max(self.sigAvg) + min(self.sigAvg)) / 2
			nAbove = len(np.where(self.sigAvg > mid)[0])
			nBelow = len(np.where(self.sigAvg < mid)[0])
			peak = True if nBelow > nAbove else False
		elif dipOrPeak == 'peak':
			peak = True
		else:
			peak = False
		if peak:
			self.sigAvgPercent = self.sigAvg - min(self.sigAvg)
		else:
			self.sigAvgPercent = -1 * (self.sigAvg - max(self.sigAvg))


	def makeSweepwiseSignal(self):
		if self.sweepwiseAvg is not None:
			return
		upSweeps, downSweeps = self.measesFromSingleSweeps()
		print(len(upSweeps))
		upSignals0 = upSweeps[0].signal0
		upSignals1 = upSweeps[0].signal1
		downSignals0 = downSweeps[0].signal0
		downSignals1 = downSweeps[0].signal1
		upBroke = 0
		downBroke = 0
		for i in range(1, len(upSweeps)):
			if len(upSweeps[i].signal0) == len(upSignals0):
				upSignals0 += upSweeps[i].signal0
				upSignals1 += upSweeps[i].signal1
			else:
				upBroke += 1
			if i < len(downSweeps):
				if len(downSweeps[i].signal0) == len(downSignals0):
					downSignals0 += downSweeps[i].signal0
					downSignals1 += downSweeps[i].signal1
				else:
					downBroke += 1
		self.sweepwiseUp0 = upSignals0 / (len(upSweeps) - upBroke)
		self.sweepwiseUp1 = upSignals1 / (len(upSweeps) - upBroke)
		self.sweepwiseDown0 = downSignals0 / (len(downSweeps) - downBroke)
		self.sweepwiseDown1 = downSignals1 / (len(downSweeps) - downBroke)
		self.sweepwiseUpAvg = (self.sweepwiseUp0 + self.sweepwiseUp1) / 2
		self.sweepwiseDownAvg = (self.sweepwiseDown0 + self.sweepwiseDown1) / 2
		self.sweepwise0 = (self.sweepwiseUp0 + self.sweepwiseDown0) / 2
		self.sweepwise1 = (self.sweepwiseUp1 + self.sweepwiseDown1) / 2
		self.sweepwiseAvg = (self.sweepwise0 + self.sweepwise1) / 2


	def shortenFrequ(self, lower=0, upper=np.inf):
		partUp = np.where(lower <= self.frequency)
		frequUp = self.frequency[partUp]
		c0Up = self.countRate0[partUp]
		c1Up = self.countRate1[partUp]
		part = np.where(frequUp <= upper)
		info = {}
		info.update({'SG380:Frequency': frequUp[part]})
		info.update({'TTCountrate:Channel0': c0Up[part]})
		info.update({'TTCountrate:Channel1': c1Up[part]})
		try:
			time = self.time[partUp]
			info.update({'Time:Elapsed': time[part]})
		except:
			print('no time information in original data')
		try:
			power = self.reflectedPower[partUp]
			info.update({'RF-Power:ConvertedPower': power[part]})
		except:
			print('no RF-Power information in original data')
		return OdmrMeasurement(info)

	def getSweepTimePos(self):
		if self.frequency[0] == max(self.frequency):
			return
		m = np.where(self.frequency == max(self.frequency))[0][0] + 1
		nSweeps = int(len(self.frequency) / m)
		skips = 0
		for i in range(nSweeps):
			start = i * m + skips
			if i == nSweeps:
				if not (len(self.frequency) - skips) % m > 1:
					break
				stop = -1
			else:
				stop = (i + 1) * m + skips
			frequs = self.frequency[start:stop]
			f0 = frequs[0]
			if len(np.where(frequs == min(self.frequency))[0]) > 1:
				skips += 1
				start += 1
			if f0 == min(self.frequency):
				self.upSweepTimes.append(self.time[start])
			elif f0 == max(self.frequency):
				self.downSweepTimes.append(self.time[start])
			else:
				raise('could not recognize sweep for time!')

	def measesFromSingleSweeps(self):
		up = []
		down = []
		m = np.where(self.frequency == max(self.frequency))[0][0] + 1
		numberOfSweeps = int(len(self.frequency) / m)
		skips = 0
		for i in range(numberOfSweeps + 1):
			start = i * m + skips
			if i == numberOfSweeps:
				if not (len(self.frequency) - skips) % m > 1:
					break
				stop = -1
			else:
				stop = (i + 1) * m + skips
			if stop - start < m:
				break
			frequs = self.frequency[start:stop]
			f0 = frequs[0]
			if len(np.where(frequs == min(self.frequency))[0]) > 1:
				skips += 1
				start += 1
				if stop > 0:
					stop += 1
				f0 = self.frequency[start]
			info = {}
			info.update({'TTCountrate:Channel0': self.countRate0[start:stop]})
			info.update({'TTCountrate:Channel1': self.countRate1[start:stop]})
			info.update({'SG380:Frequency': self.frequency[start:stop]})
			try:
				info.update({'Time:Elapsed': self.time[start:stop]})
			except:
				print('no time information in original sweep')
			try:
				info.update({'RF-Power:ConvertedPower': self.reflectedPower[start:stop]})
			except:
				print('no RF-Power information in original sweep')
			if f0 == min(self.frequency):
				up.append(OdmrMeasurement(info))
			elif f0 == max(self.frequency):
				down.append(OdmrMeasurement(info))
			else:
				print('could not recognize sweep!')
		return up, down


	def makeAverage(self):
		m = np.where(self.frequency == max(self.frequency))[0][0] + 1
		if m == 1:
			m = np.where(self.frequency == min(self.frequency))[0][0] + 1
		# numberOfSweeps = int(len(self.frequency) / m)
		# skips = 0
		# for i in range(numberOfSweeps + 1):
		# 	start = i * m + skips
		# 	if i == numberOfSweeps:
		# 		if not (len(self.frequency) - skips) % m > 1:
		# 			break
		# 		stop = -1
		# 	else:
		# 		stop = (i + 1) * m + skips
		# 	frequs = self.frequency[start:stop]
		# 	f0 = frequs[0]
		# 	if len(np.where(frequs == min(self.frequency))[0]) > 1:
		# 		skips += 1
		# 		start += 1
		# 		if stop > 0:
		# 			stop += 1
		# 		f0 = self.frequency[start]
		# 	if f0 == min(self.frequency):
		# 		self.upSweeps0.append(self.countRate0[start:stop])
		# 		self.upSweeps1.append(self.countRate1[start:stop])
		# 	elif f0 == max(self.frequency):
		# 		self.downSweeps0.append(self.countRate0[start:stop])
		# 		self.downSweeps1.append(self.countRate1[start:stop])
		# 	else:
		# 		print('could not recognize sweep first!')
		frequs = self.frequency[:m]
		counts0 = np.zeros_like(frequs)
		counts1 = np.zeros_like(frequs)
		self.lockInRavg = np.zeros_like(frequs)
		self.lockInError = np.zeros_like(frequs)
		self.signedRavg = np.zeros_like(frequs)
		self.signedRavgErrors = np.zeros_like(frequs)
		self.avgErrors0 = np.zeros_like(frequs)
		self.avgErrors1 = np.zeros_like(frequs)
		self.countsUp0 = np.zeros_like(frequs)
		self.countsUp1 = np.zeros_like(frequs)
		self.countsDown0 = np.zeros_like(frequs)
		self.countsDown1 = np.zeros_like(frequs)
		self.errorsUp0 = np.zeros_like(frequs)
		self.errorsUp1 = np.zeros_like(frequs)
		self.errorsDown0 = np.zeros_like(frequs)
		self.errorsDown1 = np.zeros_like(frequs)
		if self.lockIn:
			signedR = np.zeros_like(self.countRate0)
			p1 = np.where(np.abs(self.countRate0) >= np.abs(self.countRate1))
			signedR[p1] = np.sign(self.countRate0[p1]) * np.sqrt(self.countRate0[p1]**2 + self.countRate1[p1]**2)
			p2 = np.where(np.abs(self.countRate0) < np.abs(self.countRate1))
			signedR[p2] = np.sign(self.countRate1[p2]) * np.sqrt(self.countRate0[p2]**2 + self.countRate1[p2]**2)
		for i, f in enumerate(frequs):
			valsUp0 = []
			valsDown0 = []
			vals0 = []
			valsUp1 = []
			valsDown1 = []
			vals1 = []
			valsR = []
			valsRsign = []
			positions = np.where(self.frequency == f)
			for p in positions[0]:
				# counts0[i] += self.countRate0[p] / len(positions[0])
				# counts1[i] += self.countRate1[p] / len(positions[0])
				vals0.append(self.countRate0[p])
				vals1.append(self.countRate1[p])
				if self.lockInR is not None:
					valsR.append(self.lockInR[p])
				if self.lockIn:
					valsRsign.append(signedR[p])
				if p == 0 or (self.frequency[p-1] < self.frequency[p]) or (self.frequency[p] == f and self.frequency[p-1] == f and self.frequency[p-2] > f):
					# self.countsUp0[i] += self.countRate0[p]
					# self.countsUp1[i] += self.countRate1[p]
					valsUp0.append(self.countRate0[p])
					valsUp1.append(self.countRate1[p])
				else:
					valsDown0.append(self.countRate0[p])
					valsDown1.append(self.countRate1[p])
			if self.lockInR is not None:
				self.lockInRavg[i], self.lockInError[i] = avgAndStdDev(np.asarray(valsR))
			if self.lockIn:
				self.signedRavg[i], self.signedRavgErrors[i] = avgAndStdDev(np.asarray(valsRsign))
			counts0[i], self.avgErrors0[i] = avgAndStdDev(np.asarray(vals0))
			counts1[i], self.avgErrors1[i] = avgAndStdDev(np.asarray(vals1))
			self.countsUp0[i], self.errorsUp0[i] = avgAndStdDev(np.asarray(valsUp0))
			self.countsUp1[i], self.errorsUp1[i] = avgAndStdDev(np.asarray(valsUp1))
			self.countsDown0[i], self.errorsDown0[i] = avgAndStdDev(np.asarray(valsDown0))
			self.countsDown1[i], self.errorsDown1[i] = avgAndStdDev(np.asarray(valsDown1))
			# self.countsUp0[i] /= nUp if nUp > 0 else 1
			# self.countsUp1[i] /= nUp if nUp > 0 else 1
			# self.countsDown0[i] /= nDown if nDown > 0 else 1
			# self.countsDown1[i] /= nDown if nDown > 0 else 1
		return frequs, counts0, counts1