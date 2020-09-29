"""Default class and utilities for Zoom

All the scanning code specific to the Zoom instrument is
contained in this module

"""
from __future__ import print_function
from datetime import datetime
from general.scans.defaults import Defaults
from general.scans.detector import NormalisedIntensityDetector, create_spectra_definition
from general.scans.util import local_wrapper
from instrument.sans2d.sans import Sans2d
from genie_python import genie as g


DEFAULT_MONITOR = 2
DEFAULT_DETECTOR = 3


class Sans2d(Defaults):
    """
    This class represents the default functions for the Sans2d instrument.
    """

    detector = NormalisedIntensityDetector(
        default_monitor=DEFAULT_MONITOR,
        default_detector=DEFAULT_DETECTOR,
        spectra_definitions=[
            create_spectra_definition(1, 7000.0, 74000.0, "monitor1"),
            create_spectra_definition(2, 7000.0, 74000.0, "monitor2"),
            create_spectra_definition(3, 7000.0, 74000.0, "monitor3"),
            create_spectra_definition(4, 7000.0, 74000.0, "monitor4"),
            # Unused monitors for scanning
            # create_spectra_definition(5, 7000.0, 74000.0, "monitor5"),
            # create_spectra_definition(6, 7000.0, 74000.0, "monitor6"),
        ])

    def scan(self, motion, start=None, stop=None, step=None, frames=None,
             **kwargs):
        # Override scan so that we can do setup first
        mon = kwargs.get("monitor_number", DEFAULT_MONITOR)
        det = kwargs.get("detector_number", DEFAULT_DETECTOR)
        tubes = kwargs.get("use_tubes", False)

        if det == 3:
            # do_trans /large
            Sans2d().setup_trans()
            Sans2d().set_aperture("Large")
            g.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "IN", is_local=True)
        else:
            Sans2d().set_aperture("Large")
            g.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "OUT", is_local=True)

            if tubes:
                g.change_tables(
                    wiring="wiring_gastubes_01_hist.dat",
                    detector="detector_gastubes_01.dat",
                    spectra="spectra_scanning_auto.dat",
                )
            else:
                g.change_tables(
                    wiring="wiring_trans8.dat",
                    detector="detector_trans8.dat",
                    spectra="spectra_trans8.dat",
                )

        return super().scan(motion, start, stop, step, frames, **kwargs)

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
        return "U:/sans2d_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def __repr__(self):
        return "Sans2d()"


_sans2d = Sans2d()
scan = local_wrapper(_sans2d, "scan")
ascan = local_wrapper(_sans2d, "ascan")
dscan = local_wrapper(_sans2d, "dscan")
rscan = local_wrapper(_sans2d, "rscan")
last_scan = local_wrapper(_sans2d, "last_scan")

monitor1 = sans2d_monitor(1)
monitor2 = sans2d_monitor(2)
monitor3 = sans2d_monitor(3)
monitor4 = sans2d_monitor(4)
monitor5 = sans2d_monitor(5)
monitor6 = sans2d_monitor(6)
monitor7 = sans2d_monitor(7)
monitor8 = sans2d_monitor(8)
