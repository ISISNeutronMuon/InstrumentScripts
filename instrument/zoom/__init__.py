"""The base module for the Zoom beamline

Using a wildcard import will pull in most of the interesting
commands for this instrument."""

# pylint: disable=wildcard-import
from instrument.zoom.sans import *  # noqa: F401, F403
from instrument.zoom.scans import *  # noqa: F401, F403
from general.scans.detector import specific_spectra  # noqa: F401
from general.scans.fit import *  # noqa: F401, F403
from general.scans.motion import populate  # noqa: F401
