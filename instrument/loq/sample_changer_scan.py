"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""
from __future__ import print_function, division, unicode_literals
from datetime import datetime

from general.scans.detector import BlockDetector
from general.scans.scans import ContinuousScan, ContinuousMove

from general.scans.defaults import Defaults
from general.scans.motion import BlockMotion, Motion
from general.scans.util import local_wrapper


class LoqSampleChanger(Defaults):
    """
    This class represents the default functions for the Loq instrument.
    """
    detector = BlockDetector("changer_scan_intensity",
                             "Diode Intensity")

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
        return "loq_sample_changer_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def scan(self, motion, centre=None, size=None, time=None, iterations=1):
        """
        Scans an axis continuously about a centre point with a given move
         size and move time. Optionally, performs more than one iteration.

         Args:
            motion: the axis to move. Either a motion object or str to use an
                    IBEX block. Note, the block must point at AXIS:MTR rather
                    than just AXIS.
            centre: the centre point of the scan
            size: the total amplitude of the scan
            time: the time for a scan to move to a position and back again
            iterations (optional): the number of times to repeat the moves

        """
        self.create_fig()
        # pylint: disable=arguments-differ
        if isinstance(motion, str):
            motion = BlockMotion(motion, "mm")
        elif isinstance(motion, Motion):
            pass
        else:
            raise TypeError("Cannot run scan on axis {}. Argument should be "
                            "either a Motion object or an IBEX block name."
                            .format(motion))

        if centre is None:
            raise TypeError("Scan centre must be provided")

        if size is None or size <= 0:
            raise TypeError("Move size not provided or invalid")

        if time is None or time <= 0:
            raise TypeError("Scan time not provided or invalid")

        time_single_direction = time / 2.0

        speed = size / time_single_direction

        start = centre + size / 2.0
        stop = centre - size / 2.0

        # pylint: disable=redefined-outer-name
        scan = ContinuousScan(motion, [], self)

        for _ in range(iterations):
            scan += ContinuousScan(
                motion, [ContinuousMove(start, stop, speed)], self).and_back

        return scan

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)


axis = BlockMotion("sample_changer_scan_axis", "mm")

_loq_sample_changer = LoqSampleChanger()

scan = local_wrapper(_loq_sample_changer, "scan")
ascan = local_wrapper(_loq_sample_changer, "ascan")
dscan = local_wrapper(_loq_sample_changer, "dscan")
rscan = local_wrapper(_loq_sample_changer, "rscan")
