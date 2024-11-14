"""The base module for the Sans2d beamline

Using a wildcard import will pull in most of the interesting
commands for this instrument."""

# pylint: disable=wildcard-import
from instrument.sans2d.sans import *  # noqa: F401, F403
from instrument.sans2d.scans import *  # noqa: F401, F403
from general.scans.detector import specific_spectra  # noqa: F401
from general.scans.fit import *  # noqa: F401, F403
