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
from general.scans.monoid import Average
from general.scans.util import local_wrapper
from timeit import default_timer as timer


# pylint: disable=no-name-in-module
class Crisp(Defaults):
    """
    This class represents a scan of a block.
    """

    @staticmethod
    def _sum(monitor, low, high):
        time_steps = monitor["time"]
        time_low_index = 0
        time_high_index = len(time_steps)

        for index, time in enumerate(time_steps):
            if low >= time:
                time_low_index = index
            if high > time:
                time_high_index = index
            
        return sum(monitor["signal"][time_low_index:time_high_index+1])
    
    @staticmethod
    @dae_periods()
    def detector(**kwargs):
        """
        Perform a detector measurement
        Args:
            **kwargs: arguments to do with time asked for

        Returns:

        """
        frames = kwargs["frames"]
        curr_frames = g.get_frames()
        final_frame_number = curr_frames + frames

        print("Measuring {} frames (until from {}) ... ".format(frames, final_frame_number))
        g.resume()
        g.waitfor_frames(final_frame_number)
        g.pause()

        non_zero_spectrum = 0
        while non_zero_spectrum < 5:  # 5 tries to get a non-None spectrum from the DAE
            # get spectrum in counts for both spectra
            monitor_spec = g.get_spectrum(2, g.get_period(), False)
            detector_spec = g.get_spectrum(3, g.get_period(), False)
            if monitor_spec is not None and detector_spec is not None:
                monitor_spec = Crisp._sum(monitor_spec, 1050.0, 15500.0)
                detector_spec = Crisp._sum(detector_spec, 1450.0, 16500.0)
                if monitor_spec > 0.0 and detector_spec > 0.0:
                    break
                else:
                    non_zero_spectrum += 1
                    print("Spectrum as zero, retry")
        print("... finished measuring (det/mon: {}/{})".format(detector_spec, monitor_spec))
        return Average(detector_spec, monitor_spec)

    @staticmethod
    def log_file():
        """
        Returns: Name for the log file
        """
        axis = "Scan"
        from datetime import datetime
        now = datetime.now()
        return os.path.join("U:\\", "Users", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            axis, now.year, now.month, now.day, now.hour, now.minute, now.second))


def specific_spectra(monitor_number, detector_number=3, preconfig=lambda: None):
    """
    For scanning with different monitor/detector spectra. Example use:
        scan("smrot", -0.5, 0.5, count=21, frames=500, detector=specific_spectra(1,3)

    Args:
        monitor_number: the montior number to use
        detector_number: detecor number to use
        preconfig:

    Returns:

    """
    @dae_periods(preconfig)
    def _inner(**kwargs):
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
        while non_zero_spectrum < 5:  # 5 tries of a non-None spectrum
            # get spectrum in counts for botg spectra
            monitor_spec = g.get_spectrum(monitor_number, g.get_period(), False)
            detector_spec = g.get_spectrum(detector_number, g.get_period(), False)
            if monitor_spec is not None and detector_spec is not None:
                
                monitor_spec = Crisp._sum(monitor_spec, 1050.0, 15500.0)
                detector_spec = Crisp._sum(detector_spec, 1450.0, 16500.0)
                if monitor_spec > 0.0 and detector_spec > 0.0:
                    break
                else:
                    non_zero_spectrum += 1
        print("det/mon: {}/{}".format(detector_spec, monitor_spec))
        print("... finished measuring")
        return Average(detector_spec, monitor_spec)
    return _inner


scan = local_wrapper(Crisp(), "scan")
