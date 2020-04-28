from __future__ import print_function

import os
from math import exp, sqrt
from random import randint

from general.scans.monoid import Average
from general.scans.util import local_wrapper, get_points

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

    def __call__(self, scan, mon_num=None, det_num=None, **kwargs):
        super(DemoDetector, self).__call__(scan, mon_num, det_num, **kwargs)

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


_demo = DemoDefaultScan()
scan = local_wrapper(_demo, "scan")
ascan = local_wrapper(_demo, "ascan")
dscan = local_wrapper(_demo, "dscan")
rscan = local_wrapper(_demo, "rscan")
populate = local_wrapper(_demo, "populate")
last_scan = local_wrapper(_demo, "last_scan")
