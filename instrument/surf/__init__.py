"""The base module for the SURF beamline

Using a wildcard import will pull in most of the interesting
commands for this instrument."""

# pylint: disable=wildcard-import
from instrument.surf.scans import *  # noqa: F401, F403
from general.scans.fit import *  # noqa: F401, F403
