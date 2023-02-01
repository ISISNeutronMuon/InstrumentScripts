"""This module adds a helper class for detectors."""
from collections import namedtuple
from functools import wraps
from .monoid import Average, MonoidList

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .mocks import g

# Number of time to retry getting spectra if None is returned
SPECTRA_RETRY_COUNT = 5


def _resume_count_pause(frames=None, uamps=None, seconds=None, minutes=None, hours=None, **kwargs):
    """
    Do a resume count and pause of the dae
    Parameters
    ----------
    frames: int
        frames to count if None do uamps
    uamps: int
        uamps to count if None do a time
    seconds: int
        number of seconds to count if all times are None error
    minutes: int
        number of minutes to count if all times are None error
    hours: int
        number of hours to count if all times are None error
    kwargs:
        extra arguments to allow for interesting calls, not used
    """
    g.resume()
    if frames is not None:
        g.waitfor_frames(frames + g.get_frames())
    elif uamps is not None:
        g.waitfor_uamps(uamps + g.get_uamps())
    elif seconds is not None or minutes is not None or hours is not None:
        g.waitfor_time(hours=hours, minutes=minutes, seconds=seconds)
    else:
        raise ValueError("No valid count length. User must define either number frames, current or time period")

    g.pause()


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
        period_count = self.period_function(self._scan)
        g.change(nperiods=period_count)
        g.change(period=1)
        try:
            g.begin(paused=1)

            @wraps(self._f)
            def wrap(*args, **kwargs):
                """Wrapped function to change periods"""
                x = self._f(*args, **kwargs)
                new_period = 1 + g.get_period()
                if new_period <= period_count:
                    g.change_period(new_period)
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
        _resume_count_pause(**kwargs)

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


SpectraDefinition = namedtuple("SpectraDefintion", ["name", "spectra_number", "t_min", "t_max"])


def create_spectra_definition(spectra_number, t_min=None, t_max=None, name=None):
    """
    Create a spectra definition to be used with SpectraWithTimeRange for instance.

    Parameters
    ----------
    spectra_number: int
        spectra number to use
    t_min: float|None
        minimum time of flight to integrate spectra from; None for as low as possible
    t_max: float|None
        maximum time of flight to integrate spectra to; None for as high as possible
    name: str|int
        unique name of the spectra definition; None use the spectra_number

    Returns
    -------
        spectra definition
    """
    if name is None:
        name = spectra_number
    return SpectraDefinition(name, spectra_number, t_min, t_max)


class NormalisedIntensityDetector(DaePeriods):
    """
    Detector Manager to detect the normalised intensity of two spectra with optional time of flight ranges.

    E.g. sums up two spectra specified between energy ranges and gives one divided by the other.

    Examples:
        Within you instruments default scan class can be used as detector.

        Examples:

        >>> class Surf(Defaults):
        >>>    detector = NormalisedIntensityDetector(default_monitor=2, default_detector=3,
        >>>                        spectra_definitions = [create_spectra_definition(1, 1000.0, 15000.0),
        >>>                                               create_spectra_definition(2, 1050.0, 15500.0),
        >>>                                               create_spectra_definition(3, 1450.0, 16500.0)])

        Then when calling scan you can use the default spectra with
        >>> scan(...)

        or to use specific spectra (these must be called with keywords)
        >>> scan(... mon=1, det=2)

    """

    def __init__(self, pre_init=lambda: None, period_function=len, default_monitor="default_monitor",
                 default_detector="default_detector", spectra_definitions=None):
        """
        Initialiser.

        Parameters
        ----------
        pre_init: Function
          Any additional setup that's needed by the detector called before any measurements are taken
            (e.g. starting wiring tables)
        period_function: Function
          A function that takes a scan and calculates the number of periods
          that need to be created.  The default value is to just take the
          length of the scan.
        default_monitor: int|str
            the name of the spectra that will be used as the monitor if not overriden in the scan
        default_detector: int|str
            the name of the spectra that will be used as the monitor if not overriden in the scan
        spectra_definitions: list[SpectraDefinition]
            list of spectra definition. Use the method create_spectra_definition to create these
        """
        super(NormalisedIntensityDetector, self).__init__(self.detector_measurement, pre_init=pre_init,
                                                          period_function=period_function, unit="I/I_0")

        if spectra_definitions is None:
            spectra_definitions = [create_spectra_definition(2, 1050.0, 15500.0, "default_monitor"),
                                   create_spectra_definition(3, 1450.0, 16500.0, "default_detector")]

        self.default_monitor = default_monitor
        self.default_detector = default_detector
        self.spectra_definitions = {spectra_definition.name: spectra_definition
                                    for spectra_definition in spectra_definitions}
        self.monitor = None  # type:SpectraDefinition
        self.detector = None  # type:SpectraDefinition

    def __call__(self, scan, mon=None, det=None, **kwargs):
        """
        Call detect manger. This is typically done once before a scanning loop

        Parameters
        ----------
        scan
            scan that is calling this detect routine
        mon
            set the name of the spectra definition to use for the monitor; None use the default
        det
            set the name of the spectra definition to use for the detector; None use the default
        kwargs
            arguments to pass to super

        Returns
        -------
            self
        """
        super(NormalisedIntensityDetector, self).__call__(scan, **kwargs)
        monitor_name = mon if mon is not None else self.default_monitor
        self.monitor = self.spectra_definitions[monitor_name]
        detector_name = det if det is not None else self.default_detector
        self.detector = self.spectra_definitions[detector_name]
        return self

    def detector_measurement(self, acc, **kwargs):
        """
        Perform a detector measurement
        Args:
            acc: accumulator between measurements
            **kwargs: arguments to do with time asked for
        Returns:
            accumulator
            result from the detector measurement

        """
        _resume_count_pause(**kwargs)

        det_spectra_range = self._get_detector_spectra_range(**kwargs)

        for _ in range(SPECTRA_RETRY_COUNT):  # tries to get a non-None spectrum from the DAE
            monitor_spec_sum = g.integrate_spectrum(self.monitor.spectra_number, g.get_period(),
                                                    self.monitor.t_min, self.monitor.t_max)
            detector_spec_sum = 0
            for spectrum_num in det_spectra_range:
                det_sum = g.integrate_spectrum(spectrum_num, g.get_period(),
                                               self.detector.t_min, self.detector.t_max)
                try:
                    detector_spec_sum += det_sum
                except TypeError:
                    detector_spec_sum = None
                    break
            if monitor_spec_sum is None or detector_spec_sum is None:
                print("Spectrum is zero, retrying")
            else:
                break

        else:
            detector_spec_sum = 0
            monitor_spec_sum = 0

        print("Measuring (det {}/mon {}: {}/{})".format(self.detector.spectra_number, self.monitor.spectra_number,
                                                        detector_spec_sum, monitor_spec_sum))

        return acc, Average(detector_spec_sum, monitor_spec_sum)

    def _get_detector_spectra_range(self, **kwargs):
        """
        Returns a range of spectrum numbers (=detector pixels) as appropriate for the submitted arguments.

        Args:
            **kwargs: The keyword arguments

        Returns: The spectra range
        """
        if "pixel_range" in kwargs.keys():
            pixel_range = kwargs.get("pixel_range", 0)
            return range(max(0, self.detector.spectra_number - pixel_range),
                         self.detector.spectra_number + pixel_range + 1)
        else:
            min_pixel = kwargs.get("min_pixel", self.detector.spectra_number)
            max_pixel = kwargs.get("max_pixel", self.detector.spectra_number)
            return range(min_pixel, max_pixel + 1)
