"""The base module for the Larmor beamline

Using a wildcard import will pull in most of the interesting
commands for this instrument."""

# pylint: disable=wildcard-import
from instrument.larmor.sans import *  # noqa: F401, F403
from instrument.larmor.scans import *  # noqa: F401, F403
from general.scans.detector import specific_spectra  # noqa: F401
from general.scans.fit import *  # noqa: F401, F403
from general.scans.motion import populate  # noqa: F401
from general.scans.scans import last_scan  # noqa: F401
