from __future__ import print_function

import os
from math import exp, sqrt
from random import randint

from general.scans.monoid import Average
from general.scans.util import get_points

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g

from general.scans.defaults import Defaults
from general.scans.detector import NormalisedIntensityDetector, create_spectra_definition


class DemoDetector(NormalisedIntensityDetector):
    """
    Detector routine which call underlying routine then replaces the result with demo data, a guassian
    fitting into the window of scanning.
    """

    def __call__(self, scan, monitor_number=None, detector_number=None, **kwargs):
        super(DemoDetector, self).__call__(scan, monitor_number, detector_number, **kwargs)

        points = get_points(None, **kwargs)
        centre = 0.0
        width = abs(points[0] - points[-1]) / 3
        amp = 1000
        detector_specs = [amp * exp(-pow((point-centre)/width, 2)) for point in points]
        self.detector_specs = [ds + randint(-500, 500)/500.0 * sqrt(ds) for ds in detector_specs]
        self.monitor_specs = [amp] * len(points)

        return self

    def detector_measurement(self, acc, **kwargs):
        super(DemoDetector, self).detector_measurement(acc, **kwargs)
        if acc is None:
            acc = 0
        else:
            acc += 1
        detector_spec = self.detector_specs[acc]
        monitor_spec = self.monitor_specs[acc]
        return acc, Average(detector_spec, monitor_spec)


# pylint: disable=no-name-in-module
class DemoDefaultScan(Defaults):
    """
    Default class exposing scan functionality to the user. Has a default demo detector routine allowing it
     to produce demonstatrion data.
    """

    _spectra_definitions = [create_spectra_definition(1, 100.0, 900.0),
                            create_spectra_definition(2, 900.0, 1500.0),
                            create_spectra_definition(3, 1000.0, 1650.0)]
    detector = DemoDetector(default_monitor=2, default_detector=3,
                            spectra_definitions=_spectra_definitions)

    def __init__(self):
        super(DemoDefaultScan, self).__init__()

    @staticmethod
    def log_file(info):
        """
        Parameters
        ----------
            info
              dictionary containing useful keys to help form paths. It may contain no keys at all.
                    possible keys are action_title - the name of the action requested
        Returns
        -------
            Name for the log file
        """
        from datetime import datetime
        now = datetime.now()
        action_title = info.get("action_title", "unknown")
        return os.path.join("C:\\", "scripts", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            action_title, now.year, now.month, now.day, now.hour, now.minute, now.second))

    def scan(self, motion, start=None, stop=None, count=None, frames=None, detector_number=None, monitor_number=None, **kwargs):
        """
        Scan a motion.

        Parameters
        ----------
        motion
            motion to scan, usually a block
        start
            value to start from; if None must be specified in a different way
        stop
            value to stop at; if None must be specified in a different way
        count
            number of points; if None must be specified in a different way
        frames
            number of frames to count for; None either use a different measurement method or define the scan don't
            perform it
        detector_number
            the detector spectra number; None use the default
        monitor_number
            the monitor spectra number; None use the default
        kwargs
            various other options consistent with the scan library, common options are:
            fit - produce a fit using this type of fit e.g. Gaussian, CentreOfMass, TopHat
            before - A relative starting position for the scan.
            after - A relative ending position for the scan
            gaps - The number of steps to take
            stride - The approximate step size.  The scan may shrink this step size to ensure that the final point is
                still included in the scan.
            detector - Choose how to measure the dependent variable in the scan.  A set of these will have already been
                defined by your instrument scientist.  If you need something ad hoc, then check the documentation on
                specific_spectra for more details

        Returns
        -------
            the scan, or if fitted the fit

        Examples
        --------
        Scan theta from -0.5 to 0.5 with 11 steps and counting 100 frames using default detector and monitors
        >>> scan("THETA", -0.5, 0.5, 11, frames=100)
        """
        return super().scan(motion, start=start, stop=stop, count=count, frames=frames, detector_number=detector_number,
                            monitor_number=monitor_number, **kwargs)


_scan_instance = DemoDefaultScan()
scan = _scan_instance.scan
ascan = _scan_instance.ascan
dscan = _scan_instance.dscan
rscan = _scan_instance.rscan
populate = _scan_instance.populate
last_scan = _scan_instance.last_scan
