"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""

from __future__ import print_function

import os

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from general.scans.mocks import g

from general.scans.defaults import Defaults
from general.scans.detector import NormalisedIntensityDetector, create_spectra_definition


# pylint: disable=no-name-in-module
class PolrefDefaultScan(Defaults):
    """
    This class represents a scan of a block. This is not a thread safe class.
    """

    # spectra definition based on gcl script.
    _single_det_spectra = [create_spectra_definition(1, 100.0, 50000.0),   # Chopper pit
                           create_spectra_definition(2, 100.0, 60000.0),   # Front of Blockhouse
                           create_spectra_definition(3, 3000.0, 70000.0),  # Before Sample
                           create_spectra_definition(4, 3000.0, 70000.0)]  # Point detector
    _multi_det_spectra = [create_spectra_definition(i, 3800.0, 90000.0) for i in range(5, 646)]  # linear detector

    detector = NormalisedIntensityDetector(default_monitor=2, default_detector=280,
                                           spectra_definitions=_single_det_spectra + _multi_det_spectra)

    def __init__(self):
        super(PolrefDefaultScan, self).__init__()

    def scan(self, motion, start=None, stop=None, count=None, frames=None, det=None, mon=None,
             **kwargs):
        """
        Scan a motion.

        Parameters
        ----------
        motion
            motion to scan, usually a block
        start
            value to start from; if None must be specified in a different way
        stop
            value to stop at; if None must be specified in a different way
        count
            number of points; if None must be specified in a different way
        frames
            number of frames to count for; None either use a different measurement method or define the scan don't
            perform it
        det
            the detector spectra number; None use the default
        mon
            the monitor spectra number; None use the default
        kwargs
            various other options consistent with the scan library, common options are:
            fit - produce a fit using this type of fit e.g. Gaussian, CentreOfMass, TopHat
            before - A relative starting position for the scan.
            after - A relative ending position for the scan
            gaps - The number of steps to take
            stride - The approximate step size.  The scan may shrink this step size to ensure that the final point is
                still included in the scan.
            detector - Choose how to measure the dependent variable in the scan.  A set of these will have already been
                defined by your instrument scientist.  If you need something ad hoc, then check the documentation on
                specific_spectra for more details
            pixel_range - For summing the counts of multiple pixels. pixel_range is the number of pixels to consider
                either side of the central detector spectrum
            min_pixel - For summing the counts of multiple pixels. min_pixel is the spectrum number for the lower bound
                of the range. Overridden by pixel_range
            max_pixel - For summing the counts of multiple pixels. max_pixel is the spectrum number for the upper bound
                of the range. Overridden by pixel_range

        Returns
        -------
            the scan, or if fitted the fit

        Examples
        --------
        Scan theta from -0.5 to 0.5 with 11 steps and counting 100 frames using default detector and monitors
        >>> scan(b.THETA, -0.5, 0.5, 11, frames=100)
        """
        return super().scan(motion, start=start, stop=stop, count=count, frames=frames, det=det,
                            mon=mon, **kwargs)



_scan_instance = PolrefDefaultScan()
scan = _scan_instance.scan
ascan = _scan_instance.ascan
dscan = _scan_instance.dscan
rscan = _scan_instance.rscan
last_scan = _scan_instance.last_scan
