"""Default class and utilities for Zoom

All the scanning code specific to the Zoom instrument is
contained in this module

"""
from __future__ import print_function
from datetime import datetime
import os
from general.scans.defaults import Defaults
from general.scans.detector import NormalisedIntensityDetector, create_spectra_definition
from general.scans.util import local_wrapper
from instrument.sans2d.sans import Sans2d as Sans2d_sans
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
            create_spectra_definition(1, 7000.0, 74000.0),# "monitor1"),
            create_spectra_definition(2, 7000.0, 74000.0),# "monitor2"),
            create_spectra_definition(3, 7000.0, 74000.0),# "monitor3"),
            create_spectra_definition(4, 7000.0, 74000.0),# "monitor4"), optional name field causing errors
            # Unused monitors for scanning
            # create_spectra_definition(5, 7000.0, 74000.0, "monitor5"),
            # create_spectra_definition(6, 7000.0, 74000.0, "monitor6"),
        ])

    def scan(self, motion, start=None, stop=None, step=None, frames=None, aperture="Large",
             **kwargs):
        # Override scan so that we can do setup first

        # The name of this keyword arg must match __call__ in NormalisedIntensityDetector
        det = kwargs.get("det", DEFAULT_DETECTOR)

        if det == 3:
            Sans2d_sans().setup_trans()
            Sans2d_sans().set_aperture(aperture)
            g.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "IN", is_local=True)
        else:
            Sans2d_sans().set_aperture(aperture)
            g.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "OUT", is_local=True)

            g.change_tables(
                wiring="wiring_trans8.dat",
                detector="detector_trans8.dat",
                spectra="spectra_trans8.dat",
            )

        save = kwargs.get("save")
        # Changing Scan().plot() to allow custom log names would be very involved, so a workaround:
        if save:
            # First find the newest dat file in U:/
            base_dir = "U:/"
            prev_newest_log = max([os.path.join(base_dir,log_name)
                             for log_name in os.listdir(base_dir)
                             if log_name.endswith('.dat')])

            # Then run the scan as normal, which hopefully will add a new log file
            result = super().scan(motion, start, stop, step, frames, **kwargs)

            # Make sure our file will stay as a dat, and add a _ at the start
            save = '_' + save
            if not save.endswith(".dat"):
                save += ".dat"

            # Find the newest dat again
            newest_log = max([os.path.join(base_dir,log_name)
                              for log_name in os.listdir(base_dir)
                              if log_name.endswith('.dat')])

            # Make the new file name, the old scan file + desired name
            desired_name = os.path.join(base_dir, newest_log[:-4]+save)

            # Only if a new file has been made, rename the file
            if prev_newest_log != newest_log:
                os.rename(newest_log, desired_name)

            # And return
            return result

        # If no save name was requested, carry on as normal
        else:
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
