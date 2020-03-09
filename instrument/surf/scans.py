"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""

from __future__ import print_function
from technique.reflectometry.refl_scans import ReflectometryScan
from general.scans.fit import Gaussian, Erf, DampedOscillator, Erf, TopHat, ExactPoints, CentreOfMass

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g


scan = ReflectometryScan.reflectometry_scan
