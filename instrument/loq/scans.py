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
last_scan = local_wrapper(_loq, "last_scan")
