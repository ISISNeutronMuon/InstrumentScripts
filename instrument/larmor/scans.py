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
from general.scans.monoid import Polarisation, Average, MonoidList
from general.scans.motion import pv_motion
from general.scans.util import local_wrapper
from instrument.larmor.sans import setup_dae_transmission


def _trans_mode():
    """Setup the instrument for a simple transmission measurement."""
    setup_dae_transmission()
    g.cset(m4trans=0)
    g.waitfor_move()


class Larmor(Defaults):
    """
    This class represents the default functions for the Larmor instrument.
    """

    @staticmethod
    @dae_periods(_trans_mode)
    def detector(**kwargs):
        local_kwargs = {}
        if "frames" in kwargs:
            local_kwargs["frames"] = kwargs["frames"] + g.get_frames()
        if "uamps" in kwargs:
            local_kwargs["uamps"] = kwargs["uamps"] + g.get_uamps()
        g.resume()

        g.waitfor(**local_kwargs)
        g.pause()
        temp = sum(g.get_spectrum(4, period=g.get_period())["signal"])*100
        base = sum(g.get_spectrum(1, period=g.get_period())["signal"])*100
        return Average(temp, count=base)

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


@dae_periods(lm.setuplarmor_echoscan, lambda x: 2*len(x))
def pol_measure(**kwargs):
    """
    Get a single polarisation measurement
    """
    slices = [slice(222, 666), slice(222, 370), slice(370, 518),
              slice(518, 666)]

    i = g.get_period()

    g.change(period=i+1)
    lm.flipper1(1)
    g.waitfor_move()
    gfrm = g.get_frames()
    g.resume()
    g.waitfor(frames=gfrm+kwargs["frames"])
    g.pause()

    lm.flipper1(0)
    g.change(period=i+2)
    gfrm = g.get_frames()
    g.resume()
    g.waitfor(frames=gfrm+kwargs["frames"])
    g.pause()

    pols = [Polarisation.zero() for _ in slices]
    for channel in [11, 12]:
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

detector_trans = pv_motion("IN:LARMOR:MOT:MTD1501", "DetectorTranslation")

_lm = Larmor()
scan = local_wrapper(_lm, "scan")
ascan = local_wrapper(_lm, "ascan")
dscan = local_wrapper(_lm, "dscan")
rscan = local_wrapper(_lm, "rscan")
