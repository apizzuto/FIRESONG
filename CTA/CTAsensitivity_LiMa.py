#!/usr/bin/python
#
from __future__ import division
import re
import numpy as np
import math
import EBL
import argparse

def LiMa17(n_sig, n_bg, a):    

    n_on = n_sig + n_bg
    n_off = n_bg/a

    if (n_sig==0 or n_bg==0 or n_on==0):
        return 0
    
    if (n_on < 0 or a <=0):
        return -1
    
    l = n_on * math.log(n_on/(n_on + n_off) * (a+1)/a)
    m = n_off * math.log((a+1)* n_off/(n_on+n_off))
    if (l + m < 0):
        return -1
    else:
        return math.sqrt((l+m)*2)
    
def Significance(fluxnorm, redshift, obsTime, bckname, areaname, options):
# units: fluxnor = GeV/(cm^2.s), obsTime = h

    eblname = 'EBL_Gilmore.txt'

    ebl = EBL.EBL(eblname)

    bckg = np.loadtxt(bckname) # units: Hz
    background = 0
    for i in range(0,len(bckg)):
        background = background + bckg[i][2] * 3600 * obsTime
    # ->>> This results in  7885.17828094 counts in the 5 hour search
    # ->>> This results in 44411.1408094 counts in the 50 hour search

    # for more than one Off region (typical: 3 or 5 Off)
    alpha = 1 # 1 off

    EffArea = np.loadtxt(areaname)

    spectrum = np.empty([80,1])
    energy = np.empty([80,1])
    area = np.empty([80,1])
    delta = np.empty([80,1])

    results = []
    signal = 0
    eventduration = 3600 * obsTime # hours to seconds, time in which the siganl is integrated, in case of stable sources eventduration = observation time
# in case of transients eventduration needs to be adjusted to the transient duration and different kinds of delays
    if options.Transient == True:
            # neutrino may be emitted randomly during the transient event
        eventduration = np.random.rand()*options.timescale*(1+redshift)
            # delay due to alert generation and reposition of telescopes
        delay = (20.+np.random.rand()*60.)+(20.+np.random.rand()*30.)
        eventduration = eventduration - delay
        if (eventduration > 3600 * obsTime):
            eventduration = 3600 * obsTime
        if eventduration < 0:
            eventduration = 0.  

    results.append(eventduration)
    
# HACK ALERT!!!!! I integrate only the first 77 entries, to ensure the energy is 100 TeV or lower
# The EBL attenuation is not available above 100 TeV
    for i in range(0,39):
    #   Generate spectrum as a numpy array
    #   Units: 1/(TeV.cm^2.s)
        energy[i] = EffArea[i][0] # TeV
        area[i] = EffArea[i][1] # m^2
        spectrum[i] = fluxnorm * 1e-7 * math.pow(energy[i]/100., -options.index) * math.exp(-ebl.TAU(energy[i],redshift))
        # 1/(TeV.cm^2.s) = GeV/cm^2.s * TeV/1e3GeV * (1e2 TeV)^-2 * ebl -> 1e-7
        lowlog = math.log10(energy[i])-0.025
        hilog = math.log10(energy[i])+0.025
        # Delta is binwidth
        delta[i] = math.pow(10,hilog)-math.pow(10,lowlog)  # TeV  
        # 10,000 to convert to cm^2
        signal = signal + spectrum[i] * area[i] * 10000 * delta[i] * eventduration
        # N_sig = N_sig + 1/(TeV.cm^2.s) * m^2 * cm^2/m^2 * TeV * s
    
    sign = LiMa17(signal[0], background, alpha)
    results.append(sign)
    
    sign_eq5 = (signal/math.sqrt(background))[0]
    results.append(sign_eq5)
    #if (sign >= 5.0) or (sign_eq5 >= 5.0):
    #    print (signal, background, alpha, sign_eq5, sign)
#    print (results)
#    print (results[0],' ',results[1])
    return results

