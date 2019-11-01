"""
The module defines a series of Monoid classes for handlings
measurements.  For the unfamiliar, a monoid is just a type that A) has
a zero value and B) can be combined with other values of the same type
to produce new monoids.  For example, Sum is a monoid because Sum(a) +
Sum(b) = Sum(a+b) and Sum(a) + Sum(0) = Sum(a).

Putting the incoming data into amonoid makes it easier to get the
information out of a combined measuremnts.
"""

from abc import ABCMeta, abstractmethod
from matplotlib.pyplot import rcParams
import numpy as np
from six import add_metaclass


@add_metaclass(ABCMeta)
class Monoid(object):
    """
    The Monoid base class enforces the two laws: There must be a zero
    operation and a combining function (add).
    """
    @staticmethod
    @abstractmethod
    def zero():
        """
        The zero element of the monoid.  This element obeys the law that

        x + x.zero() == x
        """

    @abstractmethod
    def err(self):
        """
        Return the uncertainty of the current value
        """

    @abstractmethod
    def __add__(self, x):
        pass

    def __radd__(self, x):
        return self + x

    def pure(self, x):
        """Turn a number into a member of this monoid"""
        return self.__class__(x)

    def upgrade(self, x):
        """Ensure that a value is a member of this monoid"""
        if x in (0, 0.0):
            return self.zero()
        if not isinstance(x, self.__class__):
            return self.pure(x)
        return x


class Average(Monoid):
    """
    This monoid calculates the average of its values.
    """

    def __init__(self, x, count=1):
        self.total = x
        self.count = count

    def __float__(self):
        if self.count == 0:
            return float(np.nan)
        return float(self.total) / float(self.count)

    def __add__(self, y):
        y = self.upgrade(y)
        return Average(
            self.total + y.total,
            self.count + y.count)

    @staticmethod
    def zero():
        return Average(0, 0)

    def err(self):
        if self.count == 0:
            return np.nan
        if self.total == 0:
            return 0
        return np.sqrt(self.total**2 / self.count**2
                       * (1 / self.total + 1 / self.count))

    def __str__(self):
        if self.count == 0:
            return str(np.nan)
        return str(self.total / self.count)

    def __repr__(self):
        return "Average({}, count={})".format(self.total, self.count)


class Exact(Average):
    """
    A monoid representing an exact measurement.
    """

    def err(self):
        return 0


class Sum(Monoid):
    """
    This monoid calculates the sum total of the values presented
    """

    def __init__(self, x):
        self.total = x

    def __float__(self):
        return float(self.total)

    def __add__(self, y):
        y = self.upgrade(y)
        return Sum(self.total + y.total)

    @staticmethod
    def zero():
        return Sum(0)

    def err(self):
        return np.sqrt(self.total)

    def __str__(self):
        return str(self.total)

    def __repr__(self):
        return "Sum({})".format(self.total)


class Polarisation(Monoid):
    """
    This monoid calculates the polarisation from the total of all of
    the up and down counts.
    """

    def __init__(self, ups, downs=0):
        self.ups = ups
        self.downs = downs

    def __float__(self):
        if float(self.ups) + float(self.downs) == 0:
            return 0
        return (float(self.ups) - float(self.downs)) / \
            (float(self.ups) + float(self.downs))

    def __add__(self, y):
        y = self.upgrade(y)
        return Polarisation(
            self.ups + y.ups,
            self.downs + y.downs)

    def err(self):
        if float(self.ups) + float(self.downs) == 0:
            return 0.0
        if isinstance(self.ups, Monoid):
            ups = self.ups
        else:
            ups = Sum(self.ups)
        if isinstance(self.downs, Monoid):
            downs = self.downs
        else:
            downs = Sum(self.downs)

        # If ups=downs, then the numerator has an infinite relative
        # error, so the relative error of the denominator can be
        # ignored
        if float(ups) == float(downs):
            return np.sqrt(
                downs.err()**2 + ups.err()**2) / (float(ups) + float(downs))

        return float(self) * np.sqrt(downs.err()**2 + ups.err()**2) \
            * np.sqrt((float(ups) - float(downs))**-2 +
                      (float(ups) + float(downs))**-2)

    @staticmethod
    def zero():
        return Polarisation(0, 0)

    def __str__(self):
        return str(float(self))

    def __repr__(self):
        return "Polarisation({}, {})".format(self.ups, self.downs)


class MonoidList(Monoid):
    """
    This class turns a collection of Monoids into its own Monoid.
    """

    def __init__(self, values):
        self.values = values

    def zero(self):
        return [x.zero() for x in self.values]

    def __add__(self, y):
        if y == 0:
            y = self.zero()
        return MonoidList([a + b for a, b in zip(self.values, y)])

    def __str__(self):
        return "[{}]".format(
            ", ".join([str(x) for x in self]))

    def __repr__(self):
        return "MonoidList([{}])".format(
            ", ".join([repr(x) for x in self.values]))

    def __iter__(self):
        for x in self.values:
            yield x

    def err(self):
        return [x.err() for x in self.values]

    def min(self):
        """Return the smallest value"""
        lowest = self.values[0]
        for x in self.values[1:]:
            if float(lowest) > float(x):
                lowest = x
        return lowest

    def max(self):
        """Return the largest value"""
        best = self.values[0]
        for x in self.values[1:]:
            if float(best) < float(x):
                best = x
        return best


class ListOfMonoids(list):
    """
    A modified list class with special helpers for handlings
    lists of Monoids
    """

    def __init__(self, *args):
        list.__init__(self, *args)
        try:
            self.color_cycle = rcParams["axes.prop_cycle"].by_key()["color"]
        except KeyError:
            self.color_cycle = ["k", "b", "g", "r"]

    def values(self):
        """
        Get the numerical values from the List
        """
        if isinstance(self[0], MonoidList):
            return np.array([[float(v) for v in y] for y in self]).T
        return [float(y) for y in self]

    def err(self):
        """
        Get the uncertainty values from the List
        """
        if isinstance(self[0], MonoidList):
            return np.array([y.err() for y in self]).T
        return [y.err() for y in self]

    def plot(self, axis, xs):
        """
        Make an errorbar plot of a monoid onto an axis
        at a given set of x coordinates
        """
        markers = "osp+xv^<>"
        if isinstance(self[0], MonoidList):
            for y, err, color, marker in zip(self.values(), self.err(),
                                             self.color_cycle, markers):
                axis.errorbar(xs, y, yerr=err, fmt="",
                              color=color, marker=marker,
                              linestyle="None")
        else:
            axis.errorbar(xs, self.values(), yerr=self.err(), fmt="d")

    def max(self):
        """
        Find the largest value in the list, including for uncertainty
        """
        return np.nanmax(np.array(self.values()) +
                         np.array(self.err()))

    def min(self):
        """
        Find the smallest value in the list, including for uncertainty
        """
        return np.nanmin(np.array(self.values()) -
                         np.array(self.err()))
