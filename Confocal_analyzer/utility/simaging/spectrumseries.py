# -*- coding: utf-8 -*-
import logging
import os
import re
from pathlib import Path
import numpy as np

from tqdm import tqdm

import Confocal_analyzer.utility.simaging.api as sapi

logger = logging.Logger(__name__)

class SpectrumSeries:
    """ Represents a series of spectra. """
    def __init__(self, directory):
        self.__dir = Path(os.path.abspath(directory))
        self.spectra = []
        self.X = []
        self.Y = []
        self.Z = []
        self.Hz = []
        self.V = []
        self.R = []
        self.piezo = []
        self.stepper = []
        self.temps = []
        self.__readFiles(self.__dir)

    def __readFiles(self, directory):
        logger.info("Searching for files: %s", directory)
        for file in tqdm(directory.glob("*.*"), position=0):
            match = re.search(r"^.*?_X([-+eE\d.]+)_Y([-+eE\d.]+).*\..+", file.name)
            if 'scan' in file.name:
                match = re.search(r"^scan_([-+eE\d.]+)_([-+eE\d.]+).*\..+", file.name)
            if 'V' in file.name:
                match = re.search(r"^.*?_X([-+eE\d.]+)_Y([-+eE\d.]+).*_V([-+eE\d.]+).*\..+", file.name)
                # if match is not None:
                #     print("V before end")
                if match is None:
                    match = re.search(r"^.*?_X([-+eE\d.]+)_Y([-+eE\d.]+)_([-+eE\d.]+)V.*\..+", file.name)
            if 'Hz' in file.name:
                match = re.search(r"^.*?_X([-+eE\d.]+)_Y([-+eE\d.]+)_Hz([-+eE\d.]+).*\..+", file.name)
            if match is not None:
                data = sapi.readspectrum(str(file))

                X = float(match.group(1))
                Y = float(match.group(2))

                if 'V' in file.name:
                    V = float(match.group(3))
                else:
                    V = 0.0
                if 'Hz' in file.name:
                    Hz = float(match.group(3))
                else:
                    Hz = 0.0
                self.spectra.append((file, (V, X, Y, Hz, 0), data))
            else:
                mZ = re.search(r"^.*?_z([-+eE\d.]+).*\.+", file.name)
                mX = re.search(r"^.*?_X([-+eE\d.]+).*\.+", file.name)
                mY = re.search(r"^.*?_Y([-+eE\d.]+).*\.+", file.name)
                mV = re.search(r"^.*?_V([-+eE\d.]+).*\.+", file.name)
                mHz = re.search(r"^.*?_Hz([-+eE\d.]+).*\.+", file.name)
                mR = re.search(r"^.*?_R([-+eE\d.]+).*\.+", file.name)
                mP = re.search(r"^.*?_piezoV([-+eE\d.]+).*\.+", file.name)
                mS = re.search(r"^.*?_stepper([-+eE\d.]+).*\.+", file.name)
                mT = re.search(r"^.*?_([-+eE\d.]+)K.*\.+", file.name)
                viable = False
                if mZ is None:
                    mZ = re.search(r"^.*?_Z([-+eE\d.]+).*\.+", file.name)
                    if mZ is None:
                        Z = 0
                    else:
                        Z = float(mZ.group(1))
                        viable = True
                else:
                    Z = float(mZ.group(1))
                    viable = True
                if mX is None:
                    mX = re.search(r"^.*?_x([-+eE\d.]+).*\.+", file.name)
                    # print(mX)
                    if mX is None:
                        X = 0
                    else:
                        X = float(mX.group(1))
                        viable = True
                else:
                    X = float(mX.group(1))
                    viable = True
                if mY is None:
                    mY = re.search(r"^.*?_y([-+eE\d.]+).*\.+", file.name)
                    if mY is None:
                        Y = 0
                    else:
                        Y = float(mY.group(1))
                        viable = True
                else:
                    Y = float(mY.group(1))
                    viable = True
                if mV is None:
                    mV = re.search(r"^.*?_([-+eE\d.]+)V.*\.+", file.name)
                    if mV is None:
                        mV = re.search(r"^.*?_V_([-+eE\d.]+).*\.+", file.name)
                        if mV is None:
                            V = 0
                        else:
                            V = float(mV.group(1))
                            viable = True
                    else:
                        V = float(mV.group(1))
                        viable = True
                else:
                    V = float(mV.group(1))
                    viable = True
                if mHz is None:
                    Hz = 0
                else:
                    Hz = float(mHz.group(1))
                    viable = True
                if mR is None:
                    R = 0
                else:
                    R = float(mR.group(1))
                    viable = True
                if mP is None:
                    mP = re.search(r"^.*?([-+eE\d.]+)piezoV.*\.+", file.name)
                    if mP is None:
                        mP = re.search(r"^.*?piezo([-+eE\d.]+).*\.+", file.name)
                        if mP is None:
                            P = 0
                        else:
                            P = float(mP.group(1))
                            viable = True
                    else:
                        P = float(mP.group(1))
                        viable = True
                else:
                    P = float(mP.group(1))
                    viable = True
                if mS is None:
                    mS = re.search(r"^.*?([-+eE\d.]+)stepper.*\.+", file.name)
                    if mS is None:
                        S = 0
                    else:
                        S = float(mS.group(1))
                        viable = True
                else:
                    S = float(mS.group(1))
                    viable = True
                if mT is None:
                    T = 0
                else:
                    T = float(mT.group(1))
                    viable = True
                if viable:
                    try:
                        data = sapi.readspectrum(str(file))
                        self.spectra.append((file, (V, X, Y, Hz, Z, R, P, S, T), data))
                        self.X.append(X)
                        self.Y.append(Y)
                        self.Z.append(Z)
                        self.V.append(V)
                        self.Hz.append(Hz)
                        self.R.append(R)
                        self.piezo.append(P)
                        self.stepper.append(S)
                        self.temps.append(T)
                    except:
                        pass

    def get_spectra(self):
        X = len(list(set(self.X)))
        Y = len(list(set(self.Y)))
        Z = len(list(set(self.Z)))
        Hz = len(list(set(self.Hz)))
        V = len(list(set(self.V)))
        R = len(list(set(self.R)))
        P = len(list(set(self.piezo)))
        S = len(list(set(self.stepper)))
        T = len(list(set(self.temps)))
        if X == Y == len(self.spectra):
            Y = 1
        return self.spectra, (Hz, V, X, Y, Z, R, P, S, T)

    def __getitem__(self, index):
        return self.spectra[index][2]

    def getSpectralMaps(self, binsize):
        """ calculate bins for wavelength (include endpoint!) """
        wlrange = (np.amin(self.spectra[0][2].spectrum[:, 0]),
                   np.amax(self.spectra[0][2].spectrum[:, 0]))
        #posrangeX = (min([x[1][0] for x in self.spectra]),
        #             max([x[1][0] for x in self.spectra]))
        #posrangeY = (min([x[1][1] for x in self.spectra]),
        #             max([x[1][1] for x in self.spectra]))
        #wlbins = np.append(np.arange(wlrange[0], wlrange[1], binsize), wlrange[1])
        wlbins = np.arange(wlrange[0], wlrange[1], binsize)
        posbinsX = np.unique([x[1][0] for x in self.spectra])
        posbinsY = np.unique([x[1][1] for x in self.spectra])
        posbinsX += (posbinsX[1]-posbinsX[0])/2
        posbinsY += (posbinsY[1]-posbinsY[0])/2
        maps = np.empty((len(wlbins)-1, len(posbinsX), len(posbinsY)))
        specindices = np.empty((len(posbinsX), len(posbinsY)), dtype=int)
        # create maps
        for i, sp in enumerate(self.spectra):
            # interpolate spectra to avoid histogram artifacts
            xdat = np.linspace(wlrange[0], wlrange[1], 100*len(wlbins))
            ydat = np.interp(xdat, sp[2].spectrum[:,0], sp[2].spectrum[:,1])
            # histogram spectra
            hist = np.histogram(xdat, bins=wlbins, weights=ydat)
            # calculate positions
            xpos = int(np.clip(np.digitize(sp[1][0], posbinsX), 0, len(posbinsX)-1))
            ypos = int(np.clip(np.digitize(sp[1][1], posbinsY), 0, len(posbinsY)-1))
            # save histogram to map
            maps[:, xpos, ypos] = hist[0]
            specindices[xpos, ypos] = i
        return dict([("maps", maps), ("indices", specindices), ("wlbins", wlbins),
                     ("posbinsX", posbinsX), ("posbinsY", posbinsY)])

    def getSpectralMap(self, wlcenter, binsize):
        """ calculate single spectral map """
        posbinsX = np.unique([x[1][0] for x in self.spectra])
        posbinsY = np.unique([x[1][1] for x in self.spectra])
        posbinsX += (posbinsX[1]-posbinsX[0])/2
        posbinsY += (posbinsY[1]-posbinsY[0])/2
        wldat = self.spectra[0][2].spectrum[:,0]
        mask = (wldat > wlcenter - binsize/2) & (wldat < wlcenter + binsize/2)
        specmap = np.empty((len(posbinsX), len(posbinsY)))
        specindices = np.empty((len(posbinsX), len(posbinsY)), dtype=int)
        for i, sp in enumerate(self.spectra):
            ydat = sp[2].spectrum[mask,1]
            # calculate positions
            xpos = int(np.clip(np.digitize(sp[1][0], posbinsX), 0, len(posbinsX)-1))
            ypos = int(np.clip(np.digitize(sp[1][1], posbinsY), 0, len(posbinsY)-1))
            # save histogram to map
            specmap[xpos, ypos] = sum(ydat)
            specindices[xpos, ypos] = i
        return dict([("map", specmap), ("indices", specindices), ("wlcenter", wlcenter),
                     ("binsize", binsize), ("posbinsX", posbinsX), ("posbinsY", posbinsY)])

    def getSpectralRange(self):
        """ retruns wavelength range """
        return np.amin(self.spectra[0][2].spectrum[:, 0]), np.amax(self.spectra[0][2].spectrum[:, 0])