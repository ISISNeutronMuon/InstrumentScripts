from __future__ import print_function

import os

from general.scans.util import local_wrapper

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g


from general.scans.defaults import Defaults
from general.scans.detector import NormalisedIntensityDetector, create_spectra_definition


# pylint: disable=no-name-in-module
class CrispDefaultScan(Defaults):
    """
    This class represents a scan of a block. This is not a thread safe class.
    """

    _spectra_definitions = [create_spectra_definition(1, 1050.0, 15500.0),
                            create_spectra_definition(2, 1050.0, 15500.0),
                            create_spectra_definition(3, 1450.0, 16500.0)]
    detector = NormalisedIntensityDetector(default_monitor=2, default_detector=3,
                                           spectra_definitions=_spectra_definitions)

    def __init__(self):
        super(CrispDefaultScan, self).__init__()

    @staticmethod
    def log_file(info):
        """
        Returns the name of a unique log file where the scan data can be saved.
        Parameters:
            info: dictionary containing useful keys to help form paths. It may contain no keys at all.
                    possible keys are action_title - the name of the action requested
        Returns:
            Name for the log file
        """
        from datetime import datetime
        now = datetime.now()
        action_title = info.get("action_title", "unknown")
        return os.path.join("U:\\", "scripts", "TEST", "{}_{}_{}_{}_{}_{}_{}.dat".format(
            action_title, now.year, now.month, now.day, now.hour, now.minute, now.second))


_crisp = CrispDefaultScan()
scan = local_wrapper(_crisp, "scan")
ascan = local_wrapper(_crisp, "ascan")
dscan = local_wrapper(_crisp, "dscan")
rscan = local_wrapper(_crisp, "rscan")
populate = local_wrapper(_crisp, "populate")
last_scan = local_wrapper(_crisp, "last_scan")
