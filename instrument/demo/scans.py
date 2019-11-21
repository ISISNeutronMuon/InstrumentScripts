"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""

from __future__ import print_function
import os.path
from math import exp
from random import randint

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
class Demo(Defaults):
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

        if acc is None:
            acc = 0
        else:
            acc += 1
        detector_spec = Demo.detector_specs[acc]
        monitor_spec = Demo.monitor_specs[acc]

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
        return os.path.join("C:\\", "scripts", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            Demo.block, now.year, now.month, now.day, now.hour, now.minute, now.second))

def demo_scan(block, scan_from, scan_to, count, frames, monitor_number=2, detector_number=3):
    demo = Demo()
    points = np.linspace(scan_from, scan_to, num=count)
    centre = 0.0
    width = abs(scan_to - scan_from) * 3
    amp = 1000
    Demo.detector_specs = [amp * exp(-pow((point-centre), 2)/width) + randint(amp)/100 for point in points]
    Demo.monitor_specs = [1] * len(Demo.detector_specs)
    Demo.block = block
    Demo.monitor_number = monitor_number
    Demo.detector_number = detector_number

    demo.scan(block, scan_from, scan_to, count=count, frames=frames)


scan = demo_scan
