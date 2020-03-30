"""This module adds a helper class for detectors."""
from functools import wraps

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .mocks import g
from .monoid import Average, MonoidList


class DetectorManager(object):
    """Manage routines for pulling data from the instrument"""

    def __init__(self, f, unit="Intensity"):
        self._f = f
        self.scan = None
        self.unit = unit

    def __call__(self, scan, **kwargs):
        self.scan = scan
        return self

    def __enter__(self):
        if g.get_runstate() != "SETUP":  # pragma: no cover
            raise RuntimeError("Cannot start scan while already in a run!" +
                               " Current state is: " + str(g.get_runstate()))
        return self._f

    def __exit__(self, typ, value, traceback):
        pass


def get_block(name):
    """
    A simple wrapper around g.cget to give a better exception message.
    """
    try:
        return g.cget(name)["value"]
    except AttributeError:
        raise ValueError("Could not get block '{}'".format(name))


class BlockDetector(DetectorManager):
    """
    A helper class for using an IBEX block as a detector.
    """

    def __init__(self, blockname, unit=None):
        self.blockname = blockname
        if not unit:
            unit = blockname
        self._f = lambda acc: (acc, get_block(self.blockname))
        DetectorManager.__init__(self, self._f, unit)

    def __call__(self, scan, **kwargs):
        return self

    def __enter__(self):
        return self._f

    def __exit__(self, typ, value, traceback):
        pass


class DaePeriods(DetectorManager):
    """This helper class aids in making detector managers that perform all
    of their measurements in a single DAE run, instead of constantly
    starting and stopping the DAE."""

    def __init__(self, f, pre_init, period_function=len, unit="Intensity"):
        """Create a new detector manager that runs in a single Dae run

        Parameters
        ----------
        f: Function
          The actual detector command.  Should return a Monoid with the
          measured value.
        pre_init: Function
          Any additional setup that's needed by the detector (e.g. starting
          wiring tables)
        period_function: Function
          A function that takes a scan and calculates the number of periods
          that need to be created.  The default value is to just take the
          length of the scan.
        """
        self._pre_init = pre_init
        self._save = True  # Default value should never be reachable
        self.period_function = period_function
        self._scan = None
        self._kwargs = {}
        DetectorManager.__init__(self, f, unit)

    def __call__(self, scan, save, **kwargs):
        self._pre_init()
        self._save = save
        self._kwargs = kwargs
        self._scan = scan
        return self

    def __enter__(self):
        if g.get_runstate() != "SETUP":  # pragma: no cover
            raise RuntimeError("Cannot start scan while already in a run!" +
                               " Current state is: " + str(g.get_runstate()))

        kwargs = self._kwargs
        if "title" in kwargs:
            title = kwargs["title"]
            self._save = True
        else:
            title = "Scan"
        g.change_title(title)
        g.change(nperiods=self.period_function(self._scan))
        g.change(period=1)
        try:
            g.begin(paused=1)

            @wraps(self._f)
            def wrap(*args, **kwargs):
                """Wrapped function to change periods"""
                x = self._f(*args, **kwargs)
                g.change_period(1 + g.get_period())
                return x

            return wrap
        except Exception:
            if g.get_runstate() != "SETUP":  # pragma: no cover
                self._end_or_abort()
            raise

    def __exit__(self, typ, value, traceback):
        self._end_or_abort()

    def _end_or_abort(self):
        if self._save:
            g.end()
        else:
            g.abort()


def dae_periods(pre_init=lambda: None, period_function=len, unit="Intensity"):
    """Decorate to add single run number support to a detector function"""
    def inner(func):
        """wrapper"""
        return DaePeriods(func, pre_init, period_function=period_function,
                          unit=unit)
    return inner


def specific_spectra(spectra_list, preconfig=lambda: None):
    """Create a detector that scans over a given set of spectrum numbers.

    The function takes a list of list of integers.  Each inner list contains
    the channel numbers that should be combined for one single data plot.
    A MonoidList of all of the combined spectra of each inner list will
    be returned.  In the event that there is only a single inner list,
    then only that single average value will be returned.

    Examples
    ========
    >> specific_spectra([[4], range(1000,2000)])
    Will create a plot with two data points on it.  The first will be
    all of the counts in monitor four.  The second will be the combined
    sum of the counts in channels 1000 through 1999, inclusive."""
    @dae_periods(preconfig, unit="Integrated Intensity")
    def inner(acc, **kwargs):
        """Get counts on a set of channels"""
        local_kwargs = {}
        if "frames" in kwargs:
            local_kwargs["frames"] = kwargs["frames"] + g.get_frames()
        if "uamps" in kwargs:
            local_kwargs["uamps"] = kwargs["uamps"] + g.get_frames()
        g.resume()
        g.waitfor(**local_kwargs)
        g.pause()

        # Ensure that get_spectrum actually returns a value
        spec = None
        while spec is None:
            spec = g.get_spectrum(1, g.get_period())
        base = sum(g.get_spectrum(1, period=g.get_period())["signal"]) * 100.0
        pols = [Average(0, base) for _ in spectra_list]
        for idx, spectra in enumerate(spectra_list):
            for channel in spectra:
                # Ensure that get_spectrum actually returns a value
                spec = None
                while spec is None:
                    spec = g.get_spectrum(channel, g.get_period())
                temp = sum(spec["signal"])
                pols[idx] += Average(temp * 100.0, 0.0)
        if len(pols) == 1:
            return acc, pols[0]
        return acc, MonoidList(pols)
    return inner
