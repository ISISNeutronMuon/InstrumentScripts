"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""
from __future__ import print_function, division, unicode_literals

from general.scans.scans import ContinuousScan

try:
    from contextlib import contextmanager
except ImportError:
    from contextlib2 import contextmanager  # Python 2

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g
from general.scans.defaults import Defaults
from general.scans.motion import BlockMotion, Motion
from general.scans.util import local_wrapper


class LoqSampleChanger(Defaults):
    """
    This class represents the default functions for the Larmor instrument.
    """

    def detector(*args, **kwargs):
        return g.cget("intensity")["value"]

    @staticmethod
    def log_file():
        from datetime import datetime
        now = datetime.now()
        return "loq_sample_changer_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    def scan(self, motion, start=None, stop=None, speed=None, time=None, **kwargs):

        if start is not None:
            kwargs["start"] = start
        if stop is not None:
            kwargs["stop"] = stop

        if isinstance(motion, Motion):
            pass
        elif isinstance(motion, str):
            motion = BlockMotion(motion)
        else:
            raise TypeError(
                "Cannot run scan on axis {}. Try a string or a motion "
                "object instead.  It's also possible that you may "
                "need to rerun populate() to recreate your motion "
                "axes.".format(motion))

        motion.require(start)
        motion.require(stop)

        scn = ContinuousScan(motion, start, stop, speed, self)
        return scn

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)


axis = BlockMotion("axis")

_loq_sample_changer = LoqSampleChanger()
scan = local_wrapper(_loq_sample_changer, "scan")
ascan = local_wrapper(_loq_sample_changer, "ascan")
dscan = local_wrapper(_loq_sample_changer, "dscan")
rscan = local_wrapper(_loq_sample_changer, "rscan")
