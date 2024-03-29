"""Default class and utilities for Zoom

All the scanning code specific to the Zoom instrument is
contained in this module

"""
from __future__ import print_function
from datetime import datetime
from general.scans.defaults import Defaults
from general.scans.detector import specific_spectra
from general.scans.util import local_wrapper
# pylint: disable=no-name-in-module
from instrument.zoom.sans import setup_dae_transmission


def zoom_monitor(spectrum):
    """A generating function for detectors for monitor spectra"""
    return specific_spectra([[spectrum]], setup_dae_transmission)


class Zoom(Defaults):
    """
    This class represents the default functions for the Zoom instrument.
    """

    detector = specific_spectra([[4]], setup_dae_transmission)

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
        return "U:/zoom_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def __repr__(self):
        return "Zoom()"


_zm = Zoom()
scan = local_wrapper(_zm, "scan")
ascan = local_wrapper(_zm, "ascan")
dscan = local_wrapper(_zm, "dscan")
rscan = local_wrapper(_zm, "rscan")
last_scan = local_wrapper(_zm, "last_scan")

monitor1 = zoom_monitor(1)
monitor2 = zoom_monitor(2)
monitor3 = zoom_monitor(3)
monitor4 = zoom_monitor(4)
monitor5 = zoom_monitor(5)
