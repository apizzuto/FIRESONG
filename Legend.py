#!/usr/bin/python
# Authors: Chris Tung
#          Ignacio Taboada
#

# General imports
# from __future__ import division
import argparse
# Numpy / Scipy
import numpy as np
# Firesong code
from Evolution import get_LEvolution
from input_output import output_writer, print_config_LEGEND, get_outputdir
from sampling import InverseCDF


def legend_simulation(outputdir,
                      filename='LEGEND.out',
                      L_Evolution="HA2014BL",
                      zmin=0.0005,
                      zmax=10.,
                      bins=10000,
                      fluxnorm=0.9e-8,
                      index=2.13,
                      emin=1e4,
                      emax=1e7,
                      lmin=38,
                      lmax=48,
                      seed=None,
                      zNEAR=-1):

    LE_model = get_LEvolution(L_Evolution, lmin, lmax)

    N_sample = int(LE_model.Nsources(zmax))

    delta_gamma = 2 - index
    print_config_LEGEND(L_Evolution, lmin, lmax, N_sample)

    ##################################################
    #        Simulation starts here
    ##################################################

    rng = np.random.RandomState(seed)

    # Prepare CDF for redshift generation
    redshift_bins = np.arange(zmin, zmax, zmax / float(bins))
    RedshiftPDF = [LE_model.RedshiftDistribution(redshift_bins[i])
                   for i in range(0, len(redshift_bins))]
    invCDF = InverseCDF(redshift_bins, RedshiftPDF)

    # Prepare a luminosity CDF as a function of redshift
    luminosity_bins = np.arange(lmin, lmax, (lmax - lmin) / 1000.)
    LE_model.L_CDF(redshift_bins, luminosity_bins)

    out = output_writer(outputdir, filename)

    # Generate redshift
    zs = invCDF(rng.uniform(low=0.0, high=1.0, size=N_sample))
    # Generate luminosity as function of z
    lumis = LE_model.Luminosity_Sampling(zs)
    if np.ndim(lumis) < 1:
        lumis = np.array([lumis] * N_sample)
    # Calculate the flux of each source
    fluxes = LE_model.Lumi2Flux(lumis, index, emin, emax, zs)
    # Random declination over the entire sky
    sinDecs = rng.uniform(-1, 1, size=N_sample)
    declins = np.degrees(np.arcsin(sinDecs))
    TotalFlux = np.sum(fluxes)

    # Write out
    out.write(declins, zs, fluxes)
    out.finish(TotalFlux)

    print("Actual diffuse flux simulated :")
    log = "E^2 dNdE = {TotalFlux} (E/100 TeV)^({delta_gamma}) [GeV/cm^2.s.sr]"
    print(log.format(**locals()))


if __name__ == "__main__":
    outputdir = get_outputdir()

    # Process command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', action='store', dest='filename',
                        default='Legend.out', help='Output filename')
    parser.add_argument("--Levolution", action="store",
                        dest="Evolution", default='HA2014BL',
                        help="Source evolution options:  HA2014BL")
    parser.add_argument("--timescale", action='store',
                        dest='timescale', type=float,
                        default=1000.,
                        help='time scale of transient sources, default is 1000sec.')
    parser.add_argument("--zmax", action="store", type=float,
                        dest="zmax", default=10.,
                        help="Highest redshift to be simulated")
    parser.add_argument("--fluxnorm", action="store", dest='fluxnorm',
                        type=float, default=1.01e-8,
                        help="Astrophysical neutrino flux normalization A on E^2 dN/dE = A (E/100 TeV)^(-index+2) GeV/cm^2.s.sr")
    parser.add_argument("--index", action="store", dest='index',
                        type=float, default=2.19,
                        help="Astrophysical neutrino spectral index on E^2 dN/dE = A (E/100 TeV)^(-index+2) GeV/cm^2.s.sr")
    parser.add_argument("--zNEAR", action="store", dest="zNEAR",
                        type=float, default=-1,
                        help="Write down a sepaarate file for sources closer than specified redshift. If nothing is specfied, no file is written.")
    options = parser.parse_args()

    legend_simulation(outputdir,
                      filename=options.filename,
                      L_Evolution=options.Evolution,
                      zmax=options.zmax,
                      fluxnorm=options.fluxnorm,
                      index=options.index,
                      zNEAR=options.zNEAR)
