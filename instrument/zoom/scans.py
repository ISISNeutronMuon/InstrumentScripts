"""Default class and utilities for Zoom

All the scanning code specific to the Zoom instrument is
contained in this module

"""
from __future__ import print_function
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    g = None
from general.scans.defaults import Defaults
from general.scans.detector import specific_spectra
from general.scans.motion import populate
from general.scans.util import local_wrapper


class Zoom(Defaults):
    """
    This class represents the default functions for the Zoom instrument.
    """

    detector = specific_spectra([[4]])

    @staticmethod
    def log_file():
        from datetime import datetime
        now = datetime.now()
        return "U:/zoom_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def __repr__(self):
        return "Zoom()"


_zm = Zoom()
scan = local_wrapper(_zm, "scan")
ascan = local_wrapper(_zm, "ascan")
dscan = local_wrapper(_zm, "dscan")
rscan = local_wrapper(_zm, "rscan")
populate()
monitor2 = specific_spectra([[2]])
monitor3 = specific_spectra([[3]])
monitor4 = specific_spectra([[4]])
