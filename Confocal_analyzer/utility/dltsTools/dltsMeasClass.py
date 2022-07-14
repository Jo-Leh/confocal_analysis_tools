import numpy as np
import pandas as pd
import re

from copy import deepcopy
from scipy import integrate

from scipy.signal import savgol_filter
from scipy.interpolate import UnivariateSpline
from scipy.optimize import fmin

class OD_DLTS_Transient:
    def __init__(self, file, normSignal=True, shiftTime=True):
        df = pd.read_csv(file, delimiter='\t')
        match = re.search(r'^.*?_([-+eE\d.]+)_Vr_([-+eE\d.]+)_Vp_([-+eE\d.]+).txt', file)
        if match is None:
            match = re.search(r'^.*?_([-+eE\d.]+).txt', file)
            if match is not None:
                self.T = float(match.group(1))
            else:
                self.T = None
            self.Vr = None
            self.Vp = None
        else:
            self.T = float(match.group(1))
            self.Vr = float(match.group(2))
            self.Vp = float(match.group(3))
        if 'TT-Countrate:Channel0' in df.columns:
            df['signal'] = df['TT-Countrate:Channel0'] + df['TT-Countrate:Channel1']
            zeroPos = df[df['Time (s)'] == 0].index
            singleTransients = []
            for i, p in enumerate(zeroPos):
                if i > 0:
                    singleTransients.append(df.loc[zeroPos[i-1]:p-1])
            singleTransients.append(df.loc[zeroPos[-1]:])
            beforeTransients = []
            beforeLen = np.inf
            afterTransients = []
            afterLen = np.inf
            for d in singleTransients:
                pulsePos = d[d['TT-Countrate:Channel2'] == 1].index
                if len(pulsePos) != 2:
                    continue
                else:
                    pulseEnd = pulsePos[1]
                beforeTrans = np.array(d.loc[:pulseEnd][['signal', 'Time (s)']])
                afterTrans = np.array(d.loc[pulseEnd:][['signal', 'Time (s)']])
                if len(afterTrans) < afterLen:
                    afterLen = len(afterTrans)
                if len(beforeTrans) < beforeLen:
                    beforeLen = len(beforeTrans)
                beforeTransients.append(beforeTrans)
                afterTransients.append(afterTrans)
            for i, t in enumerate(beforeTransients):
                beforeTransients[i] = t[-beforeLen:]
                afterTransients[i] = afterTransients[i][:afterLen]
            beforeTransient = np.average(beforeTransients, 0)
            afterTransient = np.average(afterTransients, 0)
            self.fileName = file
            self.name = file.split('/')[-1]
            self.avgTransient = np.concatenate((beforeTransient, afterTransient))
            self.time = self.avgTransient[:,1]
            self.signalRaw = self.avgTransient[:,0]
            self.normSignal = normSignal
            if normSignal and max(self.avgTransient[:,0] > 0):
                self.signal = self.avgTransient[:,0] / np.average(self.avgTransient[:,0])
            else:
                self.signal = deepcopy(self.signalRaw)
            self.pulseEndArg = beforeLen
            if shiftTime:
                self.time -= self.time[beforeLen]
            self.pulseEnd = self.time[beforeLen]
            self.smoothed = savgol_filter(self.signal, window_length=51, polyorder=2)
            self.windowSize = 51
            self.polyorder = 2
            self.timeRaw = None
        else:
            self.time = np.asarray(df['Time (s)'])
            self.signal = np.asarray(df['signal'])
            self.smoothed = np.asarray(df['signal'])
            self.timeRaw = None
            self.signalRaw = None
            self.windowSize = 1
            self.polyorder = 1
            self.pulseEnd = 0
            self.pulseEndArg = np.argmin(np.abs(self.time))
        # self.smoothed = UnivariateSpline(self.time, self.signal, k=2)
        self.corrAfter = {}
        self.normalizations = {}
        self.corrAfterNormed = {}
        self.corrBefore = {}
        self.corrBeforeNormed = {}
        self.currentNorm = None

    def changeBinning(self, binning=1):
        if self.signalRaw is None:
            self.signalRaw = deepcopy(self.signal)
        if self.timeRaw is None:
            self.timeRaw = deepcopy(self.time)
        mid = np.where(self.timeRaw == 0)[0][0]
        skipStart = mid % binning
        if binning < 2:
            self.time = self.timeRaw
            self.signal = self.signalRaw
        else:
            self.signal = []
            self.time = []
            n = int((mid - skipStart) / binning)
            self.pulseEndArg = n-1
            for i in range(n):
                self.signal.append(np.average(self.signalRaw[(skipStart+i*binning):(skipStart+(i+1)*binning)]))
                self.time.append(np.average(self.timeRaw[(skipStart+i*binning):(skipStart+(i+1)*binning)]))
            half2 = len(self.signalRaw) - mid - 1
            skipEnd = half2 % binning
            n = int((half2 - skipEnd) / binning)
            for i in range(n):
                self.signal.append(np.average(self.signalRaw[(mid+i*binning):(mid+(i+1)*binning)]))
                self.time.append(np.average(self.timeRaw[(mid+i*binning):(mid+(i+1)*binning)]))
            self.signal = np.asarray(self.signal)
            self.time = np.asarray(self.time)
        if self.normSignal:
            self.signal = self.signal / np.average(self.signal)
        self.resmooth(self.windowSize, self.polyorder)



    def resmooth(self, window=51, polyorder=2, savgol=True):
        self.windowSize = window
        self.polyorder = polyorder
        if savgol:
            self.smoothed = savgol_filter(self.signal, window_length=window, polyorder=polyorder)
        else:
            spline = UnivariateSpline(self.time, self.signal, k=polyorder, s=window)
            self.smoothed = spline(self.time)

    def calcTau(self, startpos, endpos):
        self.corrAfter = {'temperature': self.T,
                          'a1Tw2': a1Tw2(self.time, self.smoothed, startpos, endpos),
                          'a1Tw4': a1Tw4(self.time, self.smoothed, startpos, endpos),
                          'a1Tw8': a1Tw8(self.time, self.smoothed, startpos, endpos),
                          'a1Tw16': a1Tw16(self.time, self.smoothed, startpos, endpos),
                          'a1Tw32': a1Tw32(self.time, self.smoothed, startpos, endpos),
                          'a1H': a1H(self.time, self.smoothed, startpos, endpos),
                          'b1': b1(self.time, self.smoothed, startpos, endpos),
                          'b2': b2(self.time, self.smoothed, startpos, endpos),
                          'b4': b4(self.time, self.smoothed, startpos, endpos),
                          'b1Tw2': b1Tw2(self.time, self.smoothed, startpos, endpos),
                          'b1Tw4': b1Tw4(self.time, self.smoothed, startpos, endpos),
                          'b1Tw8': b1Tw8(self.time, self.smoothed, startpos, endpos),
                          'b1Tw16': b1Tw16(self.time, self.smoothed, startpos, endpos),
                          'b1Tw32': b1Tw32(self.time, self.smoothed, startpos, endpos),
                          'gs4': gs4(self.time, self.smoothed, startpos, endpos),
                          'gs6': gs6(self.time, self.smoothed, startpos, endpos)}


    def normalize(self, points, startpos):
        return {'a1Tw2': calcNorm(a1Tw2, points, self.time[1] - self.time[0], self.time[startpos]),
              'a1Tw4': calcNorm(a1Tw4, points, self.time[1] - self.time[0], self.time[startpos]),
              'a1Tw8': calcNorm(a1Tw8, points, self.time[1] - self.time[0], self.time[startpos]),
              'a1Tw16': calcNorm(a1Tw16, points, self.time[1] - self.time[0], self.time[startpos]),
              'a1Tw32': calcNorm(a1Tw32, points, self.time[1] - self.time[0], self.time[startpos]),
              'a1H': calcNorm(a1H, points, self.time[1] - self.time[0], self.time[startpos]),
              'b1': calcNorm(b1, points, self.time[1] - self.time[0], self.time[startpos]),
              'b2': calcNorm(b2, points, self.time[1] - self.time[0], self.time[startpos]),
              'b4': calcNorm(b4, points, self.time[1] - self.time[0], self.time[startpos]),
              'b1Tw2': calcNorm(b1Tw2, points, self.time[1] - self.time[0], self.time[startpos]),
              'b1Tw4': calcNorm(b1Tw4, points, self.time[1] - self.time[0], self.time[startpos]),
              'b1Tw8': calcNorm(b1Tw8, points, self.time[1] - self.time[0], self.time[startpos]),
              'b1Tw16': calcNorm(b1Tw16, points, self.time[1] - self.time[0], self.time[startpos]),
              'b1Tw32': calcNorm(b1Tw32, points, self.time[1] - self.time[0], self.time[startpos]),
              'gs4': calcNorm(gs4, points, self.time[1] - self.time[0], self.time[startpos]),
              'gs6': calcNorm(gs6, points, self.time[1] - self.time[0], self.time[startpos])}


    def calcCorrelationsAfter(self, startpos, endpos, norm=True, smooth=True):
        if endpos > startpos:
            points = endpos - startpos
        else:
            points = len(self.smoothed)
        if type(norm) is dict:
            self.normalizations.update({'{}_{}'.format(points, startpos): norm})
            self.currentNorm = self.normalizations['{}_{}'.format(points, startpos)]
        elif norm:
            if not '{}_{}'.format(points, startpos) in self.normalizations:
                self.normalizations.update({'{}_{}'.format(points, startpos): self.normalize(points, startpos)})
            self.currentNorm = self.normalizations['{}_{}'.format(points, startpos)]
        if smooth:
            signal = self.smoothed
        else:
            signal = self.signal
        self.corrAfter = {'temperature': self.T,
                          'Vr': self.Vr,
                          'Vp': self.Vp,
                          'a1Tw2': a1Tw2(self.time, signal, startpos, endpos),
                          'a1Tw4': a1Tw4(self.time, signal, startpos, endpos),
                          'a1Tw8': a1Tw8(self.time, signal, startpos, endpos),
                          'a1Tw16': a1Tw16(self.time, signal, startpos, endpos),
                          'a1Tw32': a1Tw32(self.time, signal, startpos, endpos),
                          'a1H': a1H(self.time, signal, startpos, endpos),
                          'b1': b1(self.time, signal, startpos, endpos),
                          'b2': b2(self.time, signal, startpos, endpos),
                          'b4': b4(self.time, signal, startpos, endpos),
                          'b1Tw2': b1Tw2(self.time, signal, startpos, endpos),
                          'b1Tw4': b1Tw4(self.time, signal, startpos, endpos),
                          'b1Tw8': b1Tw8(self.time, signal, startpos, endpos),
                          'b1Tw16': b1Tw16(self.time, signal, startpos, endpos),
                          'b1Tw32': b1Tw32(self.time, signal, startpos, endpos),
                          'gs4': gs4(self.time, signal, startpos, endpos),
                          'gs6': gs6(self.time, signal, startpos, endpos)}
        if '{}_{}'.format(points, startpos) in self.normalizations:
            norms = self.normalizations['{}_{}'.format(points, startpos)]
            self.corrAfterNormed = {}
            for k in self.corrAfter:
                if k not in ['temperature', 'Vr', 'Vp']:
                    self.corrAfterNormed.update({k: self.corrAfter[k] * norms[k][1]})
                else:
                    self.corrAfterNormed.update({k: self.corrAfter[k]})

    def calcCorrelationsBefore(self, startpos, endpos, norm=True, smooth=True):
        if endpos > startpos:
            points = endpos - startpos
        else:
            points = len(self.smoothed)
        if type(norm) is dict:
            self.normalizations.update({'{}_{}'.format(points, startpos): norm})
            self.currentNorm = self.normalizations['{}_{}'.format(points, startpos)]
        elif norm:
            if not '{}_{}'.format(points, startpos) in self.normalizations:
                self.normalizations.update({'{}_{}'.format(points, startpos): self.normalize(points, startpos)})
            self.currentNorm = self.normalizations['{}_{}'.format(points, startpos)]
        if smooth:
            signal = self.smoothed
        else:
            signal = self.signal
        self.corrBefore = {'temperature': self.T,
                          'Vr': self.Vr,
                          'Vp': self.Vp,
                          'a1Tw2_before': a1Tw2(self.time, signal, startpos, endpos),
                          'a1Tw4_before': a1Tw4(self.time, signal, startpos, endpos),
                          'a1Tw8_before': a1Tw8(self.time, signal, startpos, endpos),
                          'a1Tw16_before': a1Tw16(self.time, signal, startpos, endpos),
                          'a1Tw32_before': a1Tw32(self.time, signal, startpos, endpos),
                          'a1H_before': a1H(self.time, signal, startpos, endpos),
                          'b1_before': b1(self.time, signal, startpos, endpos),
                          'b2_before': b2(self.time, signal, startpos, endpos),
                          'b4_before': b4(self.time, signal, startpos, endpos),
                          'b1Tw2_before': b1Tw2(self.time, signal, startpos, endpos),
                          'b1Tw4_before': b1Tw4(self.time, signal, startpos, endpos),
                          'b1Tw8_before': b1Tw8(self.time, signal, startpos, endpos),
                          'b1Tw16_before': b1Tw16(self.time, signal, startpos, endpos),
                          'b1Tw32_before': b1Tw32(self.time, signal, startpos, endpos),
                          'gs4_before': gs4(self.time, signal, startpos, endpos),
                          'gs6_before': gs6(self.time, signal, startpos, endpos)}
        if '{}_{}'.format(points, startpos) in self.normalizations:
            norms = self.normalizations['{}_{}'.format(points, startpos)]
            self.corrBeforeNormed = {}
            for k in self.corrBefore:
                if k not in ['temperature', 'Vr', 'Vp']:
                    self.corrBeforeNormed.update({k: self.corrBefore[k] * norms[k[:-7]][1]})
                else:
                    self.corrBeforeNormed.update({k: self.corrBefore[k]})

        # print(self.corrBefore)


correlationList = ['a1Tw2', 'a1Tw4', 'a1Tw8', 'a1Tw16', 'a1Tw32', 'a1H', 'b1', 'b2', 'b4', 'b1Tw2', 'b1Tw4', 'b1Tw8', 'b1Tw16', 'b1Tw32', 'gs4', 'gs6']

correlationListBefore = []
for i in correlationList:
    correlationListBefore.append(i + '_before')


def a1H(time, signal, startpos=0, endpos=0):
    if endpos == 0:
        endpos = len(time)
    N = endpos - startpos
    dt = time[1] - time[0]
    Tw = time[endpos-1] - time[startpos]
    DLTS = 0.5*dt/Tw*np.cos(4*np.pi*(time[startpos + int(N/2)]-time[startpos])/Tw)*signal[startpos + int(N/2)]
    for j in range(int(N/2)+1, N-1):
        DLTS += dt/Tw*np.cos(4*np.pi*(time[j+startpos]-time[startpos])/Tw)*signal[j+startpos]
    DLTS += 0.5*dt/Tw*np.cos(4*np.pi*(time[N-1+startpos]-time[startpos])/Tw)*signal[N-1+startpos]
    return DLTS

def a1Twx(time, signal, x, startpos=0, endpos=0):
    if endpos == 0:
        endpos = len(time)
    N = endpos - startpos
    dt = time[1] - time[0]
    Tw = time[endpos-1] - time[startpos]
    DLTS = 0.5*dt/Tw*np.cos(x*2*np.pi*(time[startpos]-time[startpos])/Tw)*signal[startpos]
    for j in range(1, int(N/x)):
        DLTS += dt/Tw*np.cos(2*x*np.pi*(time[j+startpos]-time[startpos])/Tw)*signal[j+startpos]
    DLTS += 0.5 * dt/Tw*np.cos(2*x*np.pi*(time[int(N/x)+startpos]-time[startpos])/Tw)*signal[int(N/x)+startpos]
    return DLTS

def a1Tw2(time, signal, startpos=0, endpos=0):
    return a1Twx(time, signal, 2, startpos, endpos)

def a1Tw4(time, signal, startpos=0, endpos=0):
    return a1Twx(time, signal, 4, startpos, endpos)

def a1Tw8(time, signal, startpos=0, endpos=0):
    return a1Twx(time, signal, 8, startpos, endpos)

def a1Tw16(time, signal, startpos=0, endpos=0):
    return a1Twx(time, signal, 16, startpos, endpos)

def a1Tw32(time, signal, startpos=0, endpos=0):
    return a1Twx(time, signal, 32, startpos, endpos)

def bxTwy(time, signal, x, y=1, startpos=0, endpos=0):
    if endpos == 0:
        endpos = len(time)
    N = endpos - startpos
    dt = time[1] - time[0]
    Tw = time[endpos-1] - time[startpos]
    DLTS = 0.5*dt/Tw*np.sin(2*x*y*np.pi*(time[startpos]-time[startpos])/Tw)*signal[startpos]
    if y == 1:
        ender = N-1
    else:
        ender = int(N/y)
    for j in range(1, ender):
        DLTS += dt/Tw*np.sin(2*x*y*np.pi*(time[j+startpos]-time[startpos])/Tw)*signal[j+startpos]
    DLTS += 0.5*dt/Tw*np.sin(2*x*y*np.pi*(time[startpos+ender]-time[startpos])/Tw)*signal[startpos+ender]
    return DLTS

def b1(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 1, 1, startpos, endpos)

def b2(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 2, 1, startpos, endpos)

def b4(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 4, 1, startpos, endpos)

def b1Tw2(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 1, 2, startpos, endpos)

def b1Tw4(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 1, 4, startpos, endpos)

def b1Tw8(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 1, 8, startpos, endpos)

def b1Tw16(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 1, 16, startpos, endpos)

def b1Tw32(time, signal, startpos=0, endpos=0):
    return bxTwy(time, signal, 1, 32, startpos, endpos)

def gs4(time, signal, startpos=0, endpos=0):
    if endpos == 0:
        endpos = len(time)
    N = endpos - startpos - 1
    dt = time[1] - time[0]
    Tw = time[endpos-1] - time[startpos]
    DLTS = 0
    for j in range(0, N):
        if j/N < 0.25:
            gs = -1
        elif j/N < 0.5:
            gs = 25
        elif j/N < 0.75:
            gs = -48
        else:
            gs = 24
        DLTS += gs * dt / Tw * signal[startpos+j]
    return DLTS

def gs6(time, signal, startpos=0, endpos=0):
    if endpos == 0:
        endpos = len(time)
    N = int((endpos - startpos)/6) * 6
    dt = time[1] - time[0]
    Tw = time[startpos+N-1] - time[startpos]
    DLTS = 0
    for j in range(0, N):
        if j/N < 1/6:
            gs = 1
        elif j/N < 2/6:
            gs = -97
        elif j/N < 3/6:
            gs = 1002
        elif j/N < 4/6:
            gs = -2526
        elif j/N < 5/6:
            gs = 2430
        else:
            gs = -810
        DLTS += gs * dt / Tw * signal[startpos+j]
    return DLTS

def calcNorm(func, points, dt, t0):
    minimi = fmin(lambda x: simulateDLTS(func, points, dt, t0, x), 1e-5, ftol=1e-8, xtol=1e-8, maxiter=100, maxfun=1000, full_output=True)
    return minimi[0]
    norm = -1 / minimi[1]
    return tauMax, norm

def simulateDLTS(func, points, dt, t0, xval):
    time = t0 + np.linspace(0, dt*points, num=points+1)
    signal = np.exp(time / -xval)
    return -func(time, signal)



def dId(t, tau, emission=False):
    if emission:
        return 1 - np.exp(-t / tau)
    return np.exp(-t / tau)


def axTwyFunc(tau, t0, Tw, x, y, emission=False):
    func = lambda t: x*y/Tw * dId(t, tau, emission) * np.cos(2*np.pi * x * y * (t-t0)/Tw)
    res = integrate.quad(func, t0, Tw/y)[0]
    return res

def a1func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 1, 1, emission)

def a2func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 2, 1, emission)

def a4func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 4, 1, emission)

def a1Tw2func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 1, 2, emission)

def a1Tw4func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 1, 4, emission)

def a1Tw8func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 1, 8, emission)

def a1Tw16func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 1, 16, emission)

def a1Tw32func(tau, t0, Tw, emission=False):
    return axTwyFunc(tau, t0, Tw, 1, 32, emission)


def b1func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 1, 1, emission)

def b2func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 2, 1, emission)

def b4func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 4, 1, emission)

def b1Tw2func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 1, 2, emission)

def b1Tw4func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 1, 4, emission)

def b1Tw8func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 1, 8, emission)

def b1Tw16func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 1, 16, emission)

def b1Tw32func(tau, t0, Tw, emission=False):
    return bxTwyFunc(tau, t0, Tw, 1, 32, emission)

def bxTwyFunc(tau, t0, Tw, x, y, emission=False):
    func = lambda t: x*y/Tw * dId(t, tau, emission) * np.sin(2 * np.pi * x * y * (t-t0)/Tw)
    res = integrate.quad(func, t0, Tw/y)[0]
    return res

def a1Hfunc(tau, t0, Tw, emission=False):
    return 0

def gs4func(tau, t0, Tw, emission=False):
    return 0

def gs6func(tau, t0, Tw, emission=False):
    return 0


corrFuncList = [a1Tw2func, a1Tw4func, a1Tw8func, a1Tw16func, a1Tw32func, a1Hfunc, b1func, b2func, b4func, b1Tw2func, b1Tw4func, b1Tw8func, b1Tw16func, b1Tw32func, gs4func, gs6func]

if __name__ == '__main__':
    # tr = OD_DLTS_Transient(r"\\confocal1\LAP Measurements Data\Johannes\dlts\p2-5\2021-05-10\tempSweep_test_05_delay_pulses_675nm_OD1_750LP\Datafile_005\OD-DLTS1_001_.txt")
    # tr.normalize(512, 0)
    print(calcNorm(b1, 512, 1.024/512, 8e-3)/1.024)
