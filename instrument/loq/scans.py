"""Default class and utilities for LOQ

All the scanning code specific to the LOQ instrument is
contained in this module

"""
from __future__ import print_function
from datetime import datetime
from general.scans.defaults import Defaults
from general.scans.detector import specific_spectra
from general.scans.util import local_wrapper


class LOQ(Defaults):
    """
    This class represents the default functions for the Zoom instrument.
    """

    detector = specific_spectra([[4]])

    @staticmethod
    def log_file():
        now = datetime.now()
        return "U:/loq_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def __repr__(self):
        return "LOQ()"


_loq = LOQ()
scan = local_wrapper(_loq, "scan")
ascan = local_wrapper(_loq, "ascan")
dscan = local_wrapper(_loq, "dscan")
rscan = local_wrapper(_loq, "rscan")
print("Remember to populate")
