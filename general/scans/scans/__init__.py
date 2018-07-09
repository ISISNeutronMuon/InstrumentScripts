"""Scans provides a unified scanning layer for scattering instruments

A wildcard import from this module will provide all of the scanning
utilities a user could be expected to need at a beamline.

"""
from __future__ import absolute_import
# We are doing some trickery with the imports that pylint doesn't
# understand, so we need to turn off some warnings
# pylint: disable=wildcard-import, unused-import, unused-wildcard-import
from socket import gethostname
from multiprocessing import current_process
from .Fit import *  # noqa: F403,F401
from . import Fit
from .Motion import populate

host = gethostname().upper()

_all = Fit.__all__[:]

# pylint: disable=not-callable
if current_process().name == "MainProcess":
    populate()
_all += ["populate"]
# Cannot test actual instrument loading
if "LARMOR" in host:  # pragma: no cover
    from .Larmor import scan, pol_measure, fast_pol_measure  # noqa: F401
    _all += ["populate", "scan", "pol_measure", "fast_pol_measure"]
elif "ZOOM" in host:  # pragma: no cover
    from .Zoom import scan, monitor1, monitor2, monitor3, monitor4  # noqa: F403,F401,E501
    _all += ["scan", "monitor1", "monitor2",
             "monitor3", "monitor4"]
else:
    from .Instrument import scan  # noqa: F403,F401,E501
    _all += ["scan"]

# pylint: disable=wrong-import-position
from .Spec import ascan, dscan, rscan  # noqa: F403,F401,E501
_all += ["ascan", "dscan", "rscan"]
