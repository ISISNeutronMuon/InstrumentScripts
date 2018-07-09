if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import numpy as np

from Scans import *
from Scans.Monoid import Average, MonoidList, Polarisation
from Scans.Larmor import pol_measure
from Scans.Mocks import g as gen
from Scans.Mocks import lm


def echoscan_axis(axis, startval, endval, npoints, frms, rtitle, save=False):
    """
    Perform an echo scan on a given instrument parameter

    Parameters
    ==========
    axis
      The motor axis to scan, as a string.  You likely was "Echo_Coil_SP"
    startval
      The first value of the scan
    endval
      The last value of the scan
    npoints
      The number of points for the scan. This is one more than the number of steps
    frms
      The number of frames per spin state.  There are ten frames per second
    rtitle
      The title of the run.  This is important when the run is saved
    save
      If True, save the scan in the log.

    Returns
    =======
    The best fit for the center of the echo value.
    """
    gen.abort()

    currents = scan(axis, start=startval, stop=endval, count=npoints)

    gen.change(title=rtitle)
    result = currents.fit(PeakFit(0.3), frames=frms, detector=pol_measure)
    if save:
        gen.end()
    else:
        gen.abort()

    return (result["peak"], 0)



print(echoscan_axis(THETA, -3, 2, 26, 1, "Echo Scan"))
