from __future__ import print_function
from technique.reflectometry.refl_scans import ReflectometryScan
from general.scans.fit import Gaussian, Erf, DampedOscillator, Erf, TopHat, ExactPoints, CentreOfMass

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g


scan = ReflectometryScan.reflectometry_scan
