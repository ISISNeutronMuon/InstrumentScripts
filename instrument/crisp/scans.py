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

    block = None
    monitor_number = None
    detector_number = None

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
    def detector(acc, **kwargs):
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
            monitor_spec = g.get_spectrum(Crisp.monitor_number, g.get_period(), False)
            detector_spec = g.get_spectrum(Crisp.detector_number, g.get_period(), False)
            if monitor_spec is not None and detector_spec is not None:
                monitor_spec = Crisp._sum(monitor_spec, 1050.0, 15500.0)
                detector_spec = Crisp._sum(detector_spec, 1450.0, 16500.0)
                if monitor_spec > 0.0 and detector_spec > 0.0:
                    break
                else:
                    non_zero_spectrum += 1
                    print("Spectrum as zero, retry")

        if acc is None:
            acc = 0
        else:
            acc += 1
        detector_spec = Crisp.detector_specs[acc]
        monitor_spec = Crisp.monitor_specs[acc]

        print("... finished measuring (det/mon: {}/{})".format(detector_spec, monitor_spec))
        return acc, Average(detector_spec, monitor_spec)

    @staticmethod
    def log_file():
        """
        Returns: Name for the log file
        """
        axis = "Scan"
        from datetime import datetime
        now = datetime.now()
        return os.path.join("U:\\", "scripts", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            Crisp.block, now.year, now.month, now.day, now.hour, now.minute, now.second))

def crisp_scan(block, scan_from, scan_to, count, frames, monitor_number=2, detector_number=3):
    crisp = Crisp()
    Crisp.detector_specs = [0, 1, 2, 1, 0]
    Crisp.monitor_specs = [1] * len(Crisp.detector_specs)
    Crisp.block = block
    Crisp.monitor_number = monitor_number
    Crisp.detector_number = detector_number

    crisp.scan(block, scan_from, scan_to, count=count, frames=frames)


scan = crisp_scan
