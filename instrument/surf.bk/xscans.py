"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""
from __future__ import print_function
import os.path
import numpy as np
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g
from general.scans.defaults import Defaults
from general.scans.detector import dae_periods, specific_spectra
from general.scans.fit import DampedOscillator
from general.scans.monoid import Polarisation, Average, MonoidList
from general.scans.motion import pv_motion
from general.scans.util import local_wrapper
# pylint: disable=no-name-in-module
from instrument.larmor.sans import setup_dae_transmission, setup_dae_semsans
from instrument.larmor.sans import setup_dae_echoscan
from instrument.larmor.SESANSroutines import set_poleshoe_angle, theta_near
from .util import flipper1


def _trans_mode():
    """Setup the instrument for a simple transmission measurement."""
    setup_dae_transmission()
    g.cset(m4trans=0)
    g.waitfor_move()


class Larmor(Defaults):
    """
    This class represents the default functions for the Larmor instrument.
    """

    detector = specific_spectra([[4]], _trans_mode)

    @staticmethod
    def log_file():
        from datetime import datetime
        now = datetime.now()
        return "larmor_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def __repr__(self):
        return "Larmor()"


def get_user_dir():
    """Move to the current user directory"""
    base = r"U:/Users/"
    try:
        dirs = [[os.path.join(base, x, d)
                 for d in os.listdir(os.path.join(base, x))
                 if os.path.isdir(os.path.join(base, x, d))]
                for x in os.listdir(base)
                if os.path.isdir(os.path.join(base, x))]
        dirs = [x for x in dirs if x]
        result = max([max(x, key=os.path.getmtime)
                      for x in dirs],
                     key=os.path.getmtime)
        print("Setting path to {}".format(result))
        os.chdir(result)
    except OSError:
        print("U Drive not found.  Setting path to current directory")


get_user_dir()


@dae_periods()
def fast_pol_measure(**kwargs):
    """
    Get a single polarisation measurement
    """
    slices = [slice(222, 666), slice(222, 370), slice(370, 518),
              slice(518, 666)]

    i = g.get_period()

    g.change(period=i+1)
    g.waitfor_move()
    gfrm = g.get_frames()
    g.resume()
    g.waitfor(frames=gfrm+kwargs["frames"])
    g.pause()

    pols = [Average.zero() for _ in slices]
    for channel in [11, 12]:
        mon1 = g.get_spectrum(1, i+1)
        spec1 = g.get_spectrum(channel, i+1)
        for idx, slc in enumerate(slices):
            ups = Average(
                np.sum(spec1["signal"][slc])*100.0,
                np.sum(mon1["signal"])*100.0)
            pols[idx] += ups
    return MonoidList(pols)


def generic_pol(spectra, preconfig=lambda: None):
    """Create a polarised detector object over a list of spectra"""
    @dae_periods(preconfig, lambda x: 2*len(x))
    def inner_pol(**kwargs):
        """
        Get a single polarisation measurement
        """
        slices = [slice(222, 666), slice(222, 370), slice(370, 518),
                  slice(518, 666)]

        i = g.get_period()

        g.change(period=i+1)
        flipper1(1)
        g.waitfor_move()
        gfrm = g.get_frames()
        g.resume()
        g.waitfor(frames=gfrm+kwargs["frames"])
        g.pause()

        flipper1(0)
        g.change(period=i+2)
        gfrm = g.get_frames()
        g.resume()
        g.waitfor(frames=gfrm+kwargs["frames"])
        g.pause()

        pols = [Polarisation.zero() for _ in slices]
        for channel in spectra:
            mon1 = g.get_spectrum(1, i+1)
            spec1 = g.get_spectrum(channel, i+1)
            mon2 = g.get_spectrum(1, i+2)
            spec2 = g.get_spectrum(channel, i+2)
            for idx, slc in enumerate(slices):
                ups = Average(
                    np.sum(spec1["signal"][slc])*100.0,
                    np.sum(mon1["signal"])*100.0)
                down = Average(
                    np.sum(spec2["signal"][slc])*100.0,
                    np.sum(mon2["signal"])*100.0)
                pols[idx] += Polarisation(ups, down)
        return MonoidList(pols)
    return inner_pol


detector_trans = pv_motion("IN:LARMOR:MOT:MTD1501", "DetectorTranslation")

_lm = Larmor()
semsans_pol = generic_pol(range(40971, 41226+1), preconfig=setup_dae_semsans)
pol_measure = generic_pol([11, 12], preconfig=setup_dae_echoscan)

scan = local_wrapper(_lm, "scan")
ascan = local_wrapper(_lm, "ascan")
dscan = local_wrapper(_lm, "dscan")
rscan = local_wrapper(_lm, "rscan")

# Echo Tuning


def auto_tune(axis, **kwargs):
    """
    Perform an echo scan on a given instrument parameter, then set
    the instrument to echo.

    Parameters
    ==========
    axis
      The motor axis to scan, as a string.  You likely was "Echo_Coil_SP"
    startval
      The first value of the scan
    endval
      The last value of the scan
    npoints
      The number of points for the scan. This is one more than the
      number of steps
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
    g.cset(m4trans=200)
    g.waitfor_move()
    fit = scan(axis, fit=DampedOscillator, detector=pol_measure, **kwargs)
    axis(fit["center"])
    return True


def angle_and_tune(theta, scan_range=(5000, 7800), l2=1188, pts=37,
                   save=True, mhz=1):
    """Set the magnet angle and tune the instrument

    Parameters
    ==========
    theta : float
      The angle for the magnet
    scan_range : tuple
      The initial and final coil values.  The values should be in mA
    pts : int
      How many data points to measure
    save : bool
      Whether to save the run in the journal
    mhz : float
      The frequency for the flipping magnets
    """
    for retries in range(2):
        # l2=1188 is the best value for 1 MHz
        # l2=1179 is the best value for 0.5 MHz
        # set_poleshoe_angle(theta=theta,l2=l2)
        set_poleshoe_angle(theta=-theta, l2=l2, MHz=mhz)
        # set_poleshoe_angle(theta=theta,l2=1179)
        if theta_near(-theta):
            break

    # new_set_pos(2)
    auto_tune(Echo_Coil_SP, start=scan_range[0], stop=scan_range[1], count=pts,
              frames=50, title="Echo scan at {} degrees".format(theta),
              save=save)
