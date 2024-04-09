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
from general.scans.fit import Gaussian, Erf, DampedOscillator, Erf, TopHat, ExactPoints, CentreOfMass
from general.scans.monoid import Polarisation, Average, MonoidList, Sum
from general.scans.motion import pv_motion
from general.scans.util import local_wrapper

# pylint: disable=no-name-in-module

def _profile_get_frames():
    return g.get_frames()

def _profile_waitfor_frames(frames):
    g.waitfor_frames(frames)
    
def _profile_get_period():
    return g.get_period()
    
def _profile_get_spectrum(spectrum, period):
    return g.get_spectrum(spectrum, period)
    
def _profile_pause():
    g.pause()
    
def _profile_resume():
    g.resume()
    
def _profile_average(spec1, spec2):
    return Average(spec1, spec2)
    
print("import")
class Surf(Defaults):
    """
    This class represents a scan of a block.
    """

    @staticmethod
    def _sum(monitor, low, high):
        time_steps = monitor["time"]
        time_low_index = 0

        for index, time in enumerate(time_steps):
            if low >= time:
                time_low_index = index
            if high > time:
                time_high_index = index
            
        return sum(monitor["signal"][time_low_index:time_high_index+1])

    
    @staticmethod
    @dae_periods()
    def detector(**kwargs):
        curr_frames = _profile_get_frames()
        
        print("Measuring")
        _profile_resume()
        curr_period = _profile_get_period()
        
        frames = kwargs["frames"]
        print("Waiting for frames: {} + {}".format(curr_frames, frames))
        _profile_waitfor_frames(curr_frames + frames)
        _profile_pause()

        monitor_spec = _profile_get_spectrum(2, curr_period)
        detector_spec = _profile_get_spectrum(3, curr_period)

        monitor_spec = Surf._sum(monitor_spec, 1050.0, 15500.0)
        detector_spec = Surf._sum(detector_spec, 1450.0, 16500.0)

        print("det/mon: {}/{}".format(detector_spec, monitor_spec))
        print("... finished measuring")
        average = Average(detector_spec, monitor_spec)
        return average

    @staticmethod
    def log_file():
        from datetime import datetime
        now = datetime.now()
        return os.path.join("U:\\", "SURF_IBEX_TEST", "scan_{}_{}_{}_{}_{}_{}.dat".format(
        now.year, now.month, now.day, now.hour, now.minute, now.second))


# For scanning with different monitor/detector spectra. Example use:
# scan("smrot", -0.5, 0.5, count=21, frames=500, detector=specific_spectra(1,3)        
def specific_spectra(monitor_number, detector_number=3, preconfig=lambda: None):
    @dae_periods(preconfig)
    def inner(**kwargs):
        print("Measuring")
        g.resume()
        frames = kwargs["frames"]
        curr_frames = g.get_frames()
        curr_period = g.get_period()
        
        print("Waiting for frames: {} + {}".format(curr_frames, frames))
        g.waitfor_frames(curr_frames + frames)
        g.pause()
        
        monitor_spec = g.get_spectrum(monitor_number, curr_period, False)
        detector_spec = g.get_spectrum(detector_number, curr_period, False)
        
        monitor_spec = Surf._sum(monitor_spec, 1050.0, 15500.0)
        detector_spec = Surf._sum(detector_spec, 1450.0, 16500.0)

        print("det/mon: {}/{}".format(detector_spec, monitor_spec))
        print("... finished measuring")
        average = Average(detector_spec, monitor_spec)
        return average
    return inner


scan = local_wrapper(Surf(), "scan")
