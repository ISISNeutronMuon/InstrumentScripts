"""Default class and utilities for Zoom

All the scanning code specific to the Zoom instrument is
contained in this module

"""
from __future__ import print_function
from datetime import datetime
from general.scans.defaults import Defaults
from general.scans.detector import specific_spectra
from general.scans.util import local_wrapper


def zoom_monitor(spectrum):
    """A generating function for detectors for monitor spectra"""
    return specific_spectra([[spectrum]])


class Zoom(Defaults):
    """
    This class represents the default functions for the Zoom instrument.
    """

    detector = specific_spectra([[4]])

    @staticmethod
    def log_file():
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
populate = local_wrapper(_zm, "populate")

print("Remember to populate")
monitor1 = zoom_monitor(1)
monitor2 = zoom_monitor(2)
monitor3 = zoom_monitor(3)
monitor4 = zoom_monitor(4)
monitor5 = zoom_monitor(5)
