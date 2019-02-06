"""The Scans module holds the base classes for scan objects.  These
objects reify the steps an instrument takes in a scan and allow us to
have single place where all of the various scanning methods can be
condensed.

The only export of this module that should ever need to be directly
accessed by other modules is SimpleScan.  Everything else should be
treated as private.

"""
from __future__ import absolute_import, print_function
from abc import ABCMeta, abstractmethod
from collections import Iterable, OrderedDict
from contextlib import contextmanager

import numpy as np
import itertools
from six import add_metaclass
import six
from .monoid import ListOfMonoids, Monoid, Average, Exact
from .detector import DetectorManager
from .fit import Fit, ExactFit
import time

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    # We must be in a test environment
    from .mocks import g

import matplotlib.pyplot as plt

TIME_KEYS = ["frames", "uamps", "seconds", "minutes", "hours"]


def just_times(kwargs):
    """Filter a dict down to just the waitfor members"""
    return {x: kwargs[x] for x in kwargs
            if x in TIME_KEYS}


def merge_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    final = x.copy()
    final.update(y)
    return final


def _plot_range(array):
    if not array:
        return (-0.05, 0.05)
    # array = [float(x) for x in array]
    low = array.min()
    high = array.max()
    diff = high-low
    return (low - 0.05 * diff,
            high + 0.05 * diff)


def estimate(seconds=None, minutes=None, hours=None,
             uamps=None, frames=None, **_):
    """Estimate takes a measurement specification and predicts how long
    the measurement will take in seconds.

    """
    if seconds or minutes or hours:
        if not seconds:
            seconds = 0
        if not minutes:
            minutes = 0
        if not hours:
            hours = 0
        return seconds + 60 * minutes + 3600 * hours

    if frames:
        return frames / 10.0

    if uamps:
        return 90 * uamps

    return 0


@add_metaclass(ABCMeta)
class Scan(object):
    """The virtual class that represents all controlled scans.  This class
    should never be instantiated directly, but rather by one of its
    subclasses."""

    defaults = None

    def _normalise_detector(self, detector):
        if not detector:
            detector = self.defaults.detector
        if not isinstance(detector, DetectorManager):
            raise ValueError(
                "fjiosfdjiosfdjisfdjisfdjiosfd {}".format(detector.__class__))
            detector = DetectorManager(detector)
        return detector

    @abstractmethod
    def map(self, func):
        """The map function returns a modified scan that performs the given
        function on all of the original positions to return the new positions.
        """
        pass

    @property
    @abstractmethod
    def reverse(self):
        """Create a new scan that runs in the opposite direction"""
        pass

    @abstractmethod
    def min(self):
        """Find the smallest point in a scan"""
        pass

    @abstractmethod
    def max(self):
        """Find the largest point in a scan"""
        pass

    def __iter__(self):
        pass

    def __add__(self, x):
        return SumScan(self, x)

    def __mul__(self, x):
        return ProductScan(self, x)

    def __and__(self, x):
        return ParallelScan(self, x)

    @property
    def forever(self):
        """
        Create a scan that will cycle until stopped by the user.
        """
        return ForeverScan(self)

    @property
    def and_back(self):
        """
        Run then scan both forwards and in reverse.  This can help minimise
        motor movement.
        """
        return self + self.reverse

    def plot(self, detector=None, save=None,
             action=None, **kwargs):
        """Run over the scan an perform a simple measurement at each position.
        The measurement parameter can be used to set what type of measurement
        is to be taken.  If the save parameter is set to a file name, then the
        plot will be saved in that file."""
        import warnings
        warnings.simplefilter("ignore", UserWarning)

        detector = self._normalise_detector(detector)

        fig, axis = plt.subplots()
        plt.show()

        xs = []
        ys = ListOfMonoids()

        action_remainder = None
        try:
            with open(self.defaults.log_file(), "w") as logfile, \
                 detector(self, save=save, **kwargs) as detect:
                for x in self:
                    # FIXME: Handle multidimensional plots
                    (label, position) = next(iter(x.items()))
                    value = detect(**just_times(kwargs))
                    if isinstance(value, float):
                        value = Average(value)
                    if position in xs:
                        ys[xs.index(position)] += value
                    else:
                        xs.append(position)
                        ys.append(value)
                    logfile.write("{}\t{}\t{}\n".format(xs[-1], str(ys[-1]),
                                                        str(ys[-1].err())))
                    axis.clear()
                    axis.set_xlabel(label)
                    if isinstance(self.min(), tuple):
                        rng = [1.05*self.min()[0] - 0.05 * self.max()[0],
                               1.05*self.max()[0] - 0.05 * self.min()[0]]
                    else:
                        rng = [1.05*self.min() - 0.05 * self.max(),
                               1.05*self.max() - 0.05 * self.min()]
                    axis.set_xlim(rng[0], rng[1])
                    rng = _plot_range(ys)
                    axis.set_ylim(rng[0], rng[1])
                    ys.plot(axis, xs)
                    if action:
                        action_remainder = action(xs, ys,
                                                  axis)
                    plt.draw()
        except KeyboardInterrupt:  # pragma: no cover
            pass
        if save:
            fig.savefig(save)

        return action_remainder

    def measure(self, title, measure=None, **kwargs):  # pragma: no cover
        """Perform a full measurement at each position indicated by the scan.
        The title parameter gives the run's title and allows for
        values to be interpolated into it.  For instance, the string
        "{theta}" will include the current value of the theta motor if
        it is being iterated over.

        WARNING: This function is deprecated and will be removed in
        the next release.

        """
        if not measure:
            measure = self.defaults.measure
        for x in self:
            measure(title, x, **kwargs)

    def fit(self, fit, **kwargs):
        """The fit method performs the scan, plotting the points as they are
        taken.  Once the scan is completed, a fit is then plotted over
        the scan and the fitting parameters are returned.

        """

        if not isinstance(fit, Fit):  # pragma: no cover
            raise TypeError("Cannot fit with {}. Perhaps you meant to call it"
                            " as a function?".format(fit))

        result = self.plot(action=fit.fit_plot_action(), **kwargs)

        if result is None:
            raise RuntimeError(
                "Could not get result from plot. Perhaps the fit failed?")
        elif isinstance(result[0], Iterable) and not isinstance(fit, ExactFit):
            result = np.array([x for x in result if x is not None])
            result = np.median(result, axis=0)

        return fit.readable(result)

    def calculate(self, time=False, pad=0, **kwargs):
        """Calculate the expected time needed to perform a scan.
        Additionally, print the expected time of completion.

        Beyond accepting the default arguments for setting a
        measurement time (e.g uamps, minutes, frames), this method
        accept two other keywords.  The pad argument is an extra time,
        in seconds, to add to each measurement to account for motor
        movements, file saving, and other such effects.  The quiet
        keyword, if set to true, prevents the printing of the expected
        time of completion.

        """
        from datetime import timedelta, datetime
        total = len(self) * (pad + estimate(**kwargs))
        # We can't test the time printing code since the result would
        # always change.
        if time:  # pragma: no cover
            delta = timedelta(0, total)
            print("The run would finish at {}".format(delta + datetime.now()))
        return total


class SimpleScan(Scan):
    """SimpleScan is a scan along a single axis for a fixed set of values"""

    def __init__(self, action, values, defaults):
        self.action = action
        self.values = values
        self.name = action.title
        self.defaults = defaults

    def map(self, func):
        """The map function returns a modified scan that performs the given
        function on all of the original positions to return the new positions.

        """
        return SimpleScan(self.action,
                          map(func, self.values),
                          self.name)

    @property
    def reverse(self):
        """Create a new scan that runs in the opposite direction"""
        return SimpleScan(self.action, self.values[::-1], self.defaults)

    def min(self):
        return self.values.min()

    def max(self):
        return self.values.max()

    def __iter__(self):
        for i in self.values:
            self.action(i)
            g.waitfor_move()
            dic = OrderedDict()
            dic[self.name] = self.action()
            yield dic

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return "SimpleScan({}, {}, {})".format(self.action.title.upper(),
                                               repr(self.values),
                                               repr(self.defaults))


class ContinuousMove(object):
    def __init__(self, start, stop, speed):
        self.start = start
        self.stop = stop
        self.speed = speed

    def __repr__(self):
        return "Continuous move from {} to {} at speed {}".format(
            self.start, self.stop, self.speed)


@contextmanager
def temporarily_change_motor_speed(motion, temporary_speed):
    """Context manager to temporarily change motor velocity, and put it
    back on exit.

    Args:
        motion: the motion object
        temporary_speed: the temporary speed to set within the context manager.

    """
    old_speed = motion.velocity
    try:
        motion.velocity = temporary_speed
        yield
    finally:
        motion.velocity = old_speed


class ContinuousScan(Scan):
    """A continuous scan that starts motion and then collects while the
axis is moving"""

    def __init__(self, motion, moves, defaults):
        """
        Initialize a continuous scan object

        Args:
            motion: the axis to move
            moves: a list of ContinuousMove objects describing the motion.
            defaults: the defaults class to use when constructing this scan.
        """
        super(Scan, self).__init__()
        self.motion = motion
        self.moves = moves

        for move in self.moves:
            if abs(move.start - move.stop) <= 0.005:
                raise ValueError(
                    "Cannot have start={} and stop={} within "
                    "motor tolerance of each other (tol={})")

        self.defaults = defaults

    @property
    def forever(self):
        """
        Create a scan that will cycle until stopped by the user.
        """
        return ForeverContinuousScan(self.motion, self.moves, self.defaults)

    def plot(self, detector=None, save=None, action=None, **kwargs):
        """Run over a continuous range """
        import warnings
        warnings.simplefilter("ignore", UserWarning)

        detector = self._normalise_detector(detector)
        fig, axis = plt.subplots()
        plt.show()

        xs = []
        ys = ListOfMonoids()

        action_remainder = None

        try:
            with open(self.defaults.log_file(), "w") as logfile, \
                    detector(self, save=save, **kwargs) as detect:

                for move in self:
                    # Set initial motor position to correct value.
                    if abs(self.motion() - move.start) > self.motion.tolerance:
                        self.motion(move.start)
                        while (abs(self.motion() - move.start)
                               > self.motion.tolerance):
                            time.sleep(0.1)

                    with temporarily_change_motor_speed(
                            self.motion, move.speed):
                        self.motion(move.stop)

                        while (abs(self.motion() - move.stop)
                               > self.motion.tolerance):
                            position = self.motion()
                            value = Exact(detect(**just_times(kwargs)))
                            xs.append(position)
                            ys.append(value)

                            logfile.write(
                                "{}\t{}\n".format(xs[-1], str(ys[-1])))
                            axis.clear()

                            if isinstance(self.min(), tuple):
                                rng = [1.05 * self.min()[0]
                                       - 0.05 * self.max()[0],
                                       1.05 * self.max()[0]
                                       - 0.05 * self.min()[0]]
                            else:
                                rng = [1.05 * self.min() - 0.05 * self.max(),
                                       1.05 * self.max() - 0.05 * self.min()]
                            axis.set_xlim(rng[0], rng[1])
                            rng = _plot_range(ys)
                            axis.set_ylim(rng[0], rng[1])
                            ys.plot(axis, xs)
                            if action:
                                action_remainder = action(xs, ys, axis)

                            plt.draw()

                            # If we plot in a tight loop, matplotlib
                            # can't keep up.  Taking data at 5Hz
                            # during the move seems the right balance
                            # of "continuous" and "pragmatic"
                            #
                            # Note: a galil's MAX update frequency is
                            # 40ms so there is no benefit in making
                            # this number smaller than 0.04
                            time.sleep(0.2)

        except KeyboardInterrupt:  # pragma: no cover
            pass

        if save:
            fig.savefig(save)

        return action_remainder

    def map(self, func):
        # The mapping function translates positions. What do we do
        # about speed?  Keep it constant, so the scan time changes, or
        # keep the scan time constant?  What are the implications of
        # either approach? Until there is a clear use case I think
        # leaving this behaviour undefined is sensible.
        raise NotImplementedError(
            "Mapping a continuous scan is not yet supported.")

    def min(self):
        return min(min(move.start, move.stop) for move in self.moves)

    def max(self):
        return max(max(move.start, move.stop) for move in self.moves)

    @property
    def reverse(self):
        moves = [ContinuousMove(start=move.stop,
                                stop=move.start,
                                speed=move.speed)
                 for move in self][::-1]
        return ContinuousScan(self.motion, moves=moves, defaults=self.defaults)

    def __len__(self):
        # Slightly different meaning - this is the number of
        # continuous moves that this scan will perform not the number
        # of points at which data will be taken. This meaning seems to
        # make the most sense given the existing framework.
        return len(self.moves)

    def __iter__(self):
        for move in self.moves:
            yield move

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            # We probably could do this in the future, but this would
            # need a bigger refactoring so that Continuous moves and
            # points could be added together in the same list.
            raise ValueError(
                "Adding a continuous and non-continuous "
                "scan together is not supported.")
        return ContinuousScan(self.motion,
                              self.moves + other.moves,
                              self.defaults)

    def __mul__(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError(
                "The product of a continuous and "
                "non-continuous scan is not supported.")
        return ContinuousScan(self.motion,
                              [itertools.product(self.moves, other.moves)],
                              self.defaults)

    def __and__(self, other):
        # We can't execute two continuous scans in parallel without
        # changing speeds.  This raises lots of questions so leave the
        # behaviour undefined for now.
        raise NotImplementedError(
            "Executing continuous scans in parallel is not supported.")

    def __repr__(self):
        return self.__class__.__name__


class SumScan(Scan):
    """The SumScan performs two separate scans sequentially"""

    def __init__(self, first, second):
        self.first = first
        self.second = second
        self.defaults = self.first.defaults

    def __iter__(self):
        for i in self.first:
            yield i
        for i in self.second:
            yield i

    def __len__(self):
        return len(self.first) + len(self.second)

    def __repr__(self):
        return "{} + {}".format(self.first, self.second)

    def map(self, func):
        """The map function returns a modified scan that performs the given
        function on all of the original positions to return the new positions.

        """
        return SumScan(self.first.map(func),
                       self.second.map(func))

    @property
    def reverse(self):
        """Creates a new scan that runs in the opposite direction"""
        return SumScan(self.second.reverse, self.first.reverse)

    def min(self):
        return min(self.first.min(), self.second.min())

    def max(self):
        return max(self.first.max(), self.second.max())


class ProductScan(Scan):
    """ProductScan performs every possible combination of the positions of
    its two constituent scans."""

    def __init__(self, outer, inner):
        self.outer = outer
        self.inner = inner
        self.defaults = self.outer.defaults

    def __iter__(self):
        for i in self.outer:
            for j in self.inner:
                yield merge_dicts(i, j)

    def __len__(self):
        return len(self.outer) * len(self.inner)

    def __repr__(self):
        return "{} * {}".format(self.outer, self.inner)

    def map(self, func):
        """The map function returns a modified scan that performs the given
        function on all of the original positions to return the new positions.

        """
        return ProductScan(self.outer.map(func),
                           self.inner.map(func))

    @property
    def reverse(self):
        """Creates a new scan that runs in the opposite direction"""
        return ProductScan(self.outer.reverse, self.inner.reverse)

    def min(self):
        return (self.outer.min(), self.inner.min())

    def max(self):
        return (self.outer.max(), self.inner.max())

    def plot(self, detector=None, save=None,
             action=None, **kwargs):
        """An overloading of Scan.plot to handle multidimensional
        scans."""
        import warnings
        warnings.simplefilter("ignore", UserWarning)

        if g and g.get_runstate() != "SETUP":
            raise RuntimeError("Cannot start scan while already in a run!" +
                               " Current state is: " + str(g.get_runstate()))

        detector = self._normalise_detector(detector)

        fig, axis = plt.subplots()
        plt.show()

        xs = []
        ys = []

        values = []
        for _ in range(len(self.outer)):
            values.append([np.nan] * len(self.inner))

        action_remainder = None
        try:
            with open(self.defaults.log_file(), "w") as logfile, \
                 detector(self, save) as detect:
                for x in self:
                    value = detect(**kwargs)

                    keys = list(x.keys())
                    keys[1] = keys[1]
                    keys[0] = keys[0]
                    y = x[keys[0]]
                    x = x[keys[1]]
                    if isinstance(value, float):
                        value = Average(value)
                    if x not in xs:
                        xs.append(x)
                    if y not in ys:
                        ys.append(y)
                    if isinstance(values[ys.index(y)][xs.index(x)], Monoid):
                        values[ys.index(y)][xs.index(x)] += value
                    else:
                        values[ys.index(y)][xs.index(x)] = value
                    logfile.write(
                        "{}\t{}\n".format(xs[-1], str(values[-1])))
                    axis.clear()
                    axis.set_xlabel(keys[1])
                    axis.set_ylabel(keys[0])
                    miny, minx = self.min()
                    maxy, maxx = self.max()
                    rng = [1.05*minx - 0.05 * maxx,
                           1.05*maxx - 0.05 * minx]
                    axis.set_xlim(rng[0], rng[1])
                    rng = [1.05*miny - 0.05 * maxy,
                           1.05*maxy - 0.05 * miny]
                    axis.set_ylim(rng[0], rng[1])
                    axis.pcolor(
                        self._estimate_locations(xs, len(self.inner),
                                                 minx, maxx),
                        self._estimate_locations(ys, len(self.outer),
                                                 miny, maxy),
                        np.array([[float(z) for z in row]
                                  for row in values]))
                    if action:
                        action_remainder = action(xs, values,
                                                  axis)
                    plt.draw()
        except KeyboardInterrupt:
            pass
        if save:
            fig.savefig(save)

        return action_remainder

    @staticmethod
    def _estimate_locations(xs, size, low, high):
        xs = np.array(xs)
        steps = xs[1:] - xs[:-1]
        if len(xs) >= 2:
            deltax = np.mean(steps)
        else:
            deltax = (high-low)/float(size)

        first = np.array([xs[0]]-deltax/2)
        remainder = size + 1 - len(xs)
        end = np.linspace(xs[-1] + deltax/2, high, remainder)[1:]
        return np.hstack([first, xs+deltax/2, end])


class ParallelScan(Scan):
    """ParallelScan runs two scans alongside each other, performing both
    sets of position adjustments before each step of the scan."""

    def __init__(self, first, second):
        self.first = first
        self.second = second
        self.defaults = self.first.defaults

    def __iter__(self):
        for x, y in six.moves.zip(self.first, self.second):
            yield merge_dicts(x, y)

    def __repr__(self):
        return "{} & {}".format(self.first, self.second)

    def __len__(self):
        return min(len(self.first), len(self.second))

    def map(self, func):
        """The map function returns a modified scan that performs the given
        function on all of the original positions to return the new positions.

        """
        return ParallelScan(self.first.map(func),
                            self.second.map(func))

    @property
    def reverse(self):
        """Creates a new scan that runs in the opposite direction"""
        return ParallelScan(self.first.reverse, self.second.reverse)

    def min(self):
        return (self.first.min(), self.second.min())

    def max(self):
        return (self.first.max(), self.second.max())


# We can't test the forever scan by definition, hence the no cover
# pragma
class ForeverScan(Scan):  # pragma: no cover
    """
    ForeverScan repeats the same scan over and over again to improve
    the statistics until the user manually halts the scan.
    """

    def __init__(self, scan):
        self.scan = scan
        self.defaults = scan.defaults

    def __iter__(self):
        while True:
            for x in self.scan:
                yield x

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.scan)

    def __len__(self):
        raise RuntimeError("Attempted to get the length of an infinite list")

    def map(self, func):
        return self.__class__(self.scan.map(func))

    @property
    def reverse(self):
        return self.__class__(self.scan.reverse)

    def min(self):
        return self.scan.min()

    def max(self):
        return self.scan.max()


class ForeverContinuousScan(ContinuousScan):
    """
    A special case of a forever scan that can operate with continuous moves.
    """
    def __len__(self):
        raise ValueError(
            "Can't get length of continuous scan that runs forever.")

    def __iter__(self):
        while True:
            for move in self.moves:
                yield move


class ReplayScan(Scan):
    """A Scan that merely repeated the output of a previous scan"""

    def __init__(self, xs, ys, axis):
        self.xs = xs
        self.ys = ys
        self.axis = axis
        # self.defaults = ReplayDetector(xs, ys)

    def min(self):
        return min(self.xs)

    def max(self):
        return max(self.xs)

    @property
    def reverse(self):
        return ReplayScan(self.xs[::-1], self.ys[::-1], self.axis)

    def map(self, func):
        return ReplayScan(map(func, self.xs), self.ys, self.axis)

    def __len__(self):
        return min(len(self.xs), len(self.ys))

    def __iter__(self):
        for x, _ in zip(self.xs, self.ys):
            dic = OrderedDict()
            dic[self.axis] = x
            yield dic

    def plot(self, detector=None, save=None,
             action=None, **kwargs):
        """Overload the scan method for the replay scan.  Since we aren't
actually detecting anything, we can run the code much simpler instead
of trying to fake a detector."""
        action_remainder = None
        xs = self.xs
        ys = ListOfMonoids(self.ys)

        fig, axis = plt.subplots()
        plt.show()

        axis.clear()
        if isinstance(self.min(), tuple):
            rng = [1.05*self.min()[0] - 0.05 * self.max()[0],
                   1.05*self.max()[0] - 0.05 * self.min()[0]]
        else:
            rng = [1.05*self.min() - 0.05 * self.max(),
                   1.05*self.max() - 0.05 * self.min()]
        axis.set_xlabel(self.axis)
        axis.set_xlim(rng[0], rng[1])
        rng = _plot_range(ys)
        axis.set_ylim(rng[0], rng[1])
        ys.plot(axis, xs)
        if action:
            action_remainder = action(xs, ys, axis)
        if save:
            fig.savefig(save)

        plt.draw()

        return action_remainder


def last_scan(path=None, axis="replay"):
    """Load the last run scan and replay that scan

    PARAMETERS
    ----------
    path
      The log file to replay.  If None, replay the most recent scan
    axis
      The label for the x axis

    """
    import os
    if path is None:
        path = max([f for f in os.listdir(os.getcwd()) if f[-4:] == ".dat"],
                   key=os.path.getctime)
    with open(path, "r") as infile:
        xs, ys, errs = np.loadtxt(infile, unpack=True)
        ys = [Average((y/e)**2, y/e**2) for y, e in zip(ys, errs)]
        return ReplayScan(xs, ys, axis)
