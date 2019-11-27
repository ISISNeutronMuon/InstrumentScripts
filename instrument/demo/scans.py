from __future__ import print_function

import os
from math import exp, sqrt
from random import randint

import numpy as np

from general.scans.defaults import Defaults
from general.scans.detector import dae_periods
from general.scans.monoid import Average
from technique.reflectometry.refl_scans import ReflectometryScan
from general.scans.fit import Gaussian, Erf, DampedOscillator, Erf, TopHat, ExactPoints, CentreOfMass

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g


# pylint: disable=no-name-in-module
class DemoScan(Defaults):
    """
    Scan but with dummy data
    """

    # The block being scanned
    block = None

    # The spetra number of the monitor
    monitor_number = None

    # The spetra number of the detector
    detector_number = None

    @staticmethod
    @dae_periods()
    def detector(acc, **kwargs):
        """
        Perform a detector measurement
        Args:
            acc: accumulator between measurements
            **kwargs: arguments to do with time asked for
        Returns:
            accumulator
            result from the detector

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
        detector_spec = DemoScan.detector_specs[acc]
        monitor_spec = DemoScan.monitor_specs[acc]

        print("... finished measuring (det/mon: {}/{})".format(detector_spec, monitor_spec))
        return acc, Average(detector_spec, monitor_spec)

    @staticmethod
    def demo_scan(block_name, scan_from, scan_to, count, frames, monitor_number=2, detector_number=3, **kwargs):
        """
        Generalised scan command with extra parameters which produces Gaussian data
        :param block_name: pv name of the block to scan
        :param scan_from: scan from this value
        :param scan_to: scan to this value
        :param count: number of points to use
        :param frames: number of frames to take per point
        :param monitor_number: spectra number for the monitor
        :param detector_number: spectra number for the detector
        :return: scan results
        """

        points = np.linspace(scan_from, scan_to, num=count)
        centre = 0.0
        width = abs(scan_to - scan_from) / 3
        amp = 1000
        detector_specs = [amp * exp(-pow((point-centre)/width, 2)) for point in points]
        DemoScan.detector_specs = [ds + randint(-500, 500)/500.0 * sqrt(ds) for ds in detector_specs]
        DemoScan.monitor_specs = [amp] * len(DemoScan.detector_specs)
        DemoScan.block = block_name
        DemoScan.monitor_number = monitor_number
        DemoScan.detector_number = detector_number

        return DemoScan().scan(block_name, scan_from, scan_to, count=count, frames=frames, **kwargs)

    @staticmethod
    def log_file():
        """
        Returns: Name for the log file
        """
        from datetime import datetime
        now = datetime.now()
        return os.path.join("C:\\", "scripts", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            ReflectometryScan.block, now.year, now.month, now.day, now.hour, now.minute, now.second))


scan = DemoScan.demo_scan
