"""Default Scans setup

"""

from __future__ import print_function
import os.path
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g
from general.scans.defaults import Defaults
from general.scans.detector import dae_periods
from general.scans.monoid import Average


# pylint: disable=no-name-in-module
class ReflectometryScan(Defaults):
    """
    This class represents a scan of a block. This is not a thread safe class.
    """

    # The block being scanned
    block = None

    # The spectra number of the monitor
    monitor_number = None

    # The spectra number of the detector
    detector_number = None

    @staticmethod
    def _sum(spectra, low, high):
        """
        Sum up a given spectra between the low(inclusive) and high(exclusive) limits
        :param spectra: spectra dictionary
        :param low: smallest time to include in calculation
        :param high: largest time to include in the calculation
        :return: sum of the counts
        """
        time_steps = spectra["time"]
        time_low_index = 0
        time_high_index = len(time_steps)

        for index, time in enumerate(time_steps):
            if low >= time:
                time_low_index = index
            if high > time:
                time_high_index = index
            
        return sum(spectra["signal"][time_low_index:time_high_index + 1])
    
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

        print("Measuring {} frames (until frame {}) ... ".format(frames, final_frame_number))
        g.resume()
        g.waitfor_frames(final_frame_number)
        g.pause()

        detector_spec_sum = 0
        monitor_spec_sum = 0
        non_zero_spectrum = 0

        while non_zero_spectrum < 5:  # 5 tries to get a non-None spectrum from the DAE
            # get spectrum in counts for both spectra
            monitor_spec = g.get_spectrum(ReflectometryScan.monitor_number, g.get_period(), False)
            detector_spec = g.get_spectrum(ReflectometryScan.detector_number, g.get_period(), False)
            if monitor_spec is not None and detector_spec is not None:
                monitor_spec_sum = ReflectometryScan._sum(monitor_spec, 1050.0, 15500.0)
                detector_spec_sum = ReflectometryScan._sum(detector_spec, 1450.0, 16500.0)
                if monitor_spec_sum > 0.0 and detector_spec_sum > 0.0:
                    break
                else:
                    non_zero_spectrum += 1
                    print("Spectrum as zero, retry")

        print("... finished measuring (det/mon: {}/{})".format(detector_spec_sum, monitor_spec_sum))
        return acc, Average(detector_spec_sum, monitor_spec_sum)

    @staticmethod
    def log_file():
        """
        Returns: Name for the log file
        """
        from datetime import datetime
        now = datetime.now()
        return os.path.join("U:\\", "scripts", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            ReflectometryScan.block, now.year, now.month, now.day, now.hour, now.minute, now.second))

    @staticmethod
    def reflectometry_scan(block, scan_from, scan_to, count, frames, monitor_number=2, detector_number=3, **kwargs):
        """
        Generalised scan command with extra parameters
        :param block: pv name of the block to scan
        :param scan_from: scan from this value
        :param scan_to: scan to this value
        :param count: number of points to use
        :param frames: number of frames to take per point
        :param monitor_number: spectra number for the monitor
        :param detector_number: spectra number for the detector
        :param kwargs: other keyword argument passed to scan e.g.
            fit: getting scan to perform a fit at the same time
        :return: scan results
        """
        refl_scan = ReflectometryScan()
        ReflectometryScan.block = block
        ReflectometryScan.monitor_number = monitor_number
        ReflectometryScan.detector_number = detector_number

        return refl_scan.scan(block, scan_from, scan_to, count=count, frames=frames, **kwargs)
