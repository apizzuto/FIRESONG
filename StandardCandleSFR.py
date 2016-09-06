#!/usr/bin/python

from __future__ import division
import numpy as np
import random
import math
import cosmolopy
from scipy.interpolate import UnivariateSpline
import argparse

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

# Plack 2015 parameters
cosmology = {'omega_M_0' : 0.308, 'omega_lambda_0' : 0.692, 'h' : 0.678}
cosmology = cosmolopy.distance.set_omega_k_0(cosmology) #Flat universe

#StarFormationHistory (SFR), from Hopkins and Beacom, unit = M_sun/yr/Mpc^3 
def StarFormationHistory(x):
    if x<0.30963:
        return math.pow(10,3.28*x-1.82)
    if (x>=0.30963)and(x<0.73878):
        return math.pow(10,-0.26*x-0.724)
    if x>=0.73878:
        return math.pow(10,-8.0*x+4.99)

def ObservedRate(z):
    return 4*np.pi*StarFormationHistory(np.log10(1+z))*cosmolopy.distance.diff_comoving_volume(z, **cosmology)

# Assuming Star formation rate evolution and Standard Candles results in
# 18,460,312 sources for a local source density of 1e-6 / Mpc3.
#
def NumberOfSourcesStandardCandleSFR(density):
    return int(18460312.*density/1e-6)

# Flux at redshift z=1 scaled according to density
# The output is in units of GeV/cm^2.s
# It assumes that the total desired diffuse flux is
#
# E^2 dN/dE = 1e-8 (E/100 TeV)^(-0.1) GeV/cm^2.s.sr
#
def Fluxz1StandardCandleSFT(density):
    return 2.20e-14*(1e-6/density)

#
# Process command line options
#
parser = argparse.ArgumentParser()
parser.add_argument('-o', action='store', dest='filename',
                    help='Output filename')
parser.add_argument('-d', action='store', dest='density', type=float,
                    help='Local neutrino source density [Mpc^3]')
parser.add_argument("-p", action="store_false",
                    dest="NoPSComparison", default=True,
                    help="Calculate detectable point sources")
options = parser.parse_args()
output = open(options.filename,"w")
N_sample = NumberOfSourcesStandardCandleSFR(options.density)
flux_z1 = Fluxz1StandardCandleSFT(options.density)

print ("##############################################################################")
print (color.BOLD + "FIRESONG initializing" + color.END)
print (color.BLUE + "Model: standard candle sources" + color.END)
print (color.BLUE + "Model: star formation evolution" + color.END)
print ("Uses neutrino diffuse flux: E^2 dN/dE = 1e-8 (E/100 TeV)^(-0.1) GeV/cm^2.s.sr")
print ("Local density of neutrino sources: " + str(options.density) + "/Mpc^3")
print ("Number of neutrinos sources in the Universe: " + str(N_sample))
print (color.BOLD + "FIRESONG initialization done" + color.END)

#Generate the bins of z
bins = np.arange(0, 10, 0.001)

#Generate the histogram
binmid = bins[:-1] + np.diff(bins)/2.
hist = [ObservedRate(binmid[i]) for i in range(0,len(binmid))]

#Generate the random number of z
cdf = np.cumsum(hist)
cdf = cdf / cdf[-1]
values = np.random.rand(N_sample)                     
value_bins = np.searchsorted(cdf, values)
random_from_cdf = binmid[value_bins]

# This is the number of events as a function of declination (Effective Area?)
def IceCubeResponse(sinDec):
    sinDecbin = np.array([-0.075,-0.025,0.025,0.075,0.125,0.175,0.225,0.275,0.325,0.375,0.425,0.475,0.525,0.575,0.625,0.675,0.725,0.775,0.825,0.875,0.925,0.975])
    response = np.array([105.896, 185.11, 177.775, 155.445, 133.492, 113.77, 99.8513, 87.4213, 76.7264, 63.8566, 57.6465, 48.2527, 44.1256, 34.2095, 30.4975, 25.8617, 22.4174, 19.0691, 15.683, 9.20381, 5.12658, 3.40891])
    spline = UnivariateSpline(sinDecbin,response)
    if sinDec>=-0.1 and sinDec<=1.:
        return spline(sinDec)
    else:
        return 0

#Standard Canle, all source has same lumionsity at z = 1.0, so we calculate the luminosity distance at z=1
dL1 = cosmolopy.distance.luminosity_distance(1.0, **cosmology)

#The idea is to put all calculations outside for loop
#Generate the declination
sinDec = np.random.rand(N_sample)
sinDec = sinDec*2. -1.
#Get z
z = random_from_cdf
#get luminosity distance at z
dL = cosmolopy.distance.luminosity_distance(z, **cosmology)
#get flux at z, the coefficient here should match the Total flux = 1e-8 Gev / cm^2 / s / sr
#for N_sample = 14921752, facctor is 2.13E-15
flux = flux_z1 * (dL1*dL1)/(dL*dL) 

#total flux
TotalFlux = np.sum(flux)

#Calculate the effectivearea at icecube for each source
EA = [0]*len(sinDec)
for i in range(0, len(sinDec)):
	EA[i] = IceCubeResponse(sinDec[i])

#Get mean no. of event due to each source
events = EA*flux/1e-8
#Get the number of event from poisson distribution
obs = np.random.poisson(events, (1, len(events)))

#Calculate the declination
declin = 180*np.arcsin(sinDec)/np.pi

### The following two lines may be a faster way to output the array, will save it for later
#finalset = zip(declin, z, flux, obs[0])
#np.savetxt(options.filename, finalset, delimiter=" ", fmt='%f, %f, %f, %i')

output.write("# FIRESONG Output description\n")
output.write("# Declination: degrees\n")
output.write("# Redshift\n")
output.write("# flux: E^2 dN/dE assuming (E/100 TeV)^(-0.1) GeV/cm^2.s.sr\n")
output.write("#     Note that as of 2016, IceCube can detect point sources of ~10^-9 in the\n")
output.write("#     qunits used here.\n")
output.write("# Observed: Number of >200 TeV neutrino events detected, using 6 year Diffuse effective area by Sebastian+Leif\n")
output.write("# declination     z      flux       observed" + "\n")

for i in range(0, len(random_from_cdf)):
	output.write(str(declin[i]) + " " + str(z[i]) + " " + str(flux[i]) + " " + str(obs[0][i]) + "\n")

print (color.BOLD + "RESULTS" + color.END)
print ('E^2 dNdE = ' + str(TotalFlux/(4*np.pi)))
output.write("# E^2 dNdE = " + str(TotalFlux/(4*np.pi)) + "\n")

################################
#Find out if there are sources that exceed IceCube's limit
#
if (options.NoPSComparison==False):
    fluxToPointSourceSentivity = flux / 1e-9
    detectable  = [i for i in fluxToPointSourceSentivity if i >= 1.]
    print detectable
    output.write("# Fluxes exceeding Point Source limits " + str(detectable) + "\n")

output.close()








