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
        curr_frames = g.get_frames()
        print("frame count: {}".format(curr_frames))
        print("Measuring")
        g.waitfor_move()
        g.waitfor_time(1)
        g.resume()
        frames = kwargs["frames"]

        
        g.waitfor_frames(curr_frames + frames)
        g.pause()
        g.waitfor_time(1)
        non_zero_spectrum = 0 
        while non_zero_spectrum < 5: # 5 tries of a non-None spectrum
            # get spectrum in counts for botg spectra
            monitor_spec = g.get_spectrum(2, g.get_period(), False)
            detector_spec = g.get_spectrum(3, g.get_period(), False)
            if monitor_spec is not None and detector_spec is not None:
                
                monitor_spec = Surf._sum(monitor_spec, 1050.0, 15500.0)
                detector_spec = Surf._sum(detector_spec, 1450.0, 16500.0)
                if monitor_spec > 0.0 and detector_spec > 0.0:
                     break
                else:
                    non_zero_spectrum +=1
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
        curr_frames = g.get_frames()
        print("frame count: {}".format(curr_frames))
        print("Measuring")
        g.waitfor_move()
        g.waitfor_time(1)
        g.resume()
        frames = kwargs["frames"]

        
        g.waitfor_frames(curr_frames + frames)
        g.pause()
        g.waitfor_time(1)
        non_zero_spectrum = 0 
        while non_zero_spectrum < 5: # 5 tries of a non-None spectrum
            # get spectrum in counts for botg spectra
            monitor_spec = g.get_spectrum(monitor_number, g.get_period(), False)
            detector_spec = g.get_spectrum(detector_number, g.get_period(), False)
            if monitor_spec is not None and  detector_spec is not None:
                
                monitor_spec = Surf._sum(monitor_spec, 1050.0, 15500.0)
                detector_spec = Surf._sum(detector_spec, 1450.0, 16500.0)
                if monitor_spec > 0.0 and detector_spec > 0.0:
                     break
                else:
                    non_zero_spectrum +=1
        print("det/mon: {}/{}".format(detector_spec, monitor_spec))
        print("... finished measuring")
        return Average(detector_spec, monitor_spec)
    return inner


scan = local_wrapper(Surf(), "scan")
