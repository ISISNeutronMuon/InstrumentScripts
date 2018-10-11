"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""
from __future__ import print_function
import numpy as np
from .util import make_scan
from .defaults import Defaults
from .detector import dae_periods
from .motion import populate
from .mocks import g


class MockInstrument(Defaults):
    """
    This class represents a fake instrument that can be
    used for testing purposes.
    """

    scan_count = 0

    @staticmethod
    @dae_periods()
    def detector(**kwargs):
        print("Taking a count at theta=%0.2f and two theta=%0.2f" %
              (g.cget("Theta")["value"], g.cget("Two_Theta")["value"]))
        return (1+np.cos(g.cget("Theta")["value"])) * \
            np.sqrt(g.cget("Theta")["value"]) + \
            g.cget("Two_Theta")["value"] ** 2 + \
            0.05 * np.random.rand()

    def log_file(self):
        self.scan_count += 1
        return "mock_scan_{:02}.dat".format(self.scan_count)


populate()
scan = make_scan(MockInstrument())
