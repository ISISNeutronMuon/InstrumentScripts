Guide for Instrument Scientists
*******************************

.. highlight:: python
   :linenothreshold: 20

.. comment
     >>> import os, sys
     >>> sys.path.insert(0, os.getcwd())
     >>> import matplotlib
     >>> # matplotlib.use("Agg")
     >>> ();from instrument.larmor import *;()  # doctest:+ELLIPSIS
     (...)
     >>> from general.scans.motion import populate
     >>> populate()

Introduction
============

.. py:currentmodule:: general.scans

In theory, the minimal responsibility of the instrument scientist is
to write a single instance of the :class:`defaults.Defaults`
class.  The :meth:`defaults.Defaults.scan`,
:meth:`defaults.Defaults.ascan`,
:meth:`defaults.Defaults.dscan`, and
:meth:`defaults.Defaults.rscan` methods should then be exported
from the module.  The :meth:`util.local_wrapper` function can
simplify exporting these class methods.

Defaults
========

The ``Defaults`` class requires the instrument scientist to implement
four class methods.  If either of the two methods are missing, the class
will immediately throw an error on the first attempt to instantiate
it.  This helps finding errors quickly, instead of in the middle of a
measurement when the missing function is first needed.

detector
--------

The :meth:`defaults.Defaults.detector` function should return
the result of a measurement in a Monoid_.  This will most likely be
either a total number of counts on a detector or transmission monitor.
However, it is possible to provide more complicated measurements and
values, such as taking a flipping measurement and returning a
polarisation.

The value returned by the function should either be a raw count
represented by a number or an instance of the
:class:`monoid.Monoid` class.  The Monoid_ class allows for
multiple measurements to be combined correctly.

The :meth:`detector.specific_spectra` function is a
useful helper function for creating function the read from specific detectors.  For example

    >>> whole_detector = specific_spectra([[1]])

Will create a new detector function ``whole_detector`` which returns
the total counts on detector spectrum 1.  The user could then runghc

    >>> scan(Theta, 0, 2, 0.6, 50, detector=whole_detector)

To run the scan over those channels, instead of over the default setup.

log_file
--------

The :meth:`defaults.Defaults.log_file` returns the path to a
file where the results of the current scan should be stored.  This
function should return a unique value for each scan, to ensure that
previous results are not overwritten.  This can easily be achieved by
appending the current date and time onto the file name.

Monoid
======

Mathematically, a monoid is a collection with the following properties:

1) There exists an operator &, such that, for any two elements, such
   as x and y, in the collection, then there is another element in the
   collection whose value would be x & y.
2) a & (b & c) = (a & b) & c
3) There exists a zero element Z such that, a & Z = Z & a = a

The more intuitive explanation is that a monoid promises us that we
can combine many elements together and get back a single element.  Many common structures form monoids.

Count
  0 is the zero element and addition is the operator
Lists
  The zero element is the empty list and concatenation is the operator
Boolean
  False is the zero element and ``or`` is the operator
Product
  1 is the zero element and multiplication is the operator
Sum
  0 is the zero element and addition is the operator
Unit Monoid
  The collection with only a single element is a monoid.  The zero
  value is that element and the operator just returns its first
  value.  For example, the set {@} is a monoid with zero element
  @ and a combining operator @ & @ = @.
Minimum
  ∞ is the zero elemenent and the & operator simply returns the smallest of its operands
A pair of monoids (m, n)
  The zero element is (m_0, n_0) and our & operator is defined so that (m_x, n_x) & (m_y, n_y) = (m_x & m_y, n_x & n_y)

The ability of a pair of monoids to form another monoid allows for the
development of surprisingly deep structures.
For example, since the Sum and Count are both
monoids, then the combination (Sum, Count) is also a monoid.  We know
that dividing the sum by the count will give us the average.  What the
monoid convention provides, however, is a way to combine two averages
to correctly get the new average.  If I know that one set has an
average of 6 and the other has an average of 4, I don't know what the
average of the combined sets should be.  On the other hand, if I know
that one set has a sum and count of (60, 10) and the other has (160,
40), I know that the combined set has a sum and count of (220, 50) and
the total average is 4.4.  In a similar fashion, it is also possible
to express the standard deviation as a monoid, allowing for a standard
deviation that can be live updated as each data point arrives.

Uncertainties
-------------

Although monoids do not natively contain a notion of uncertainty [#]_,
the monoids used in this project could allow for the calculation of
uncertainty.  The design decision was that
adding that uncertainty calculation into the monoid provided enough
utility and simplified the value enough to warrant its inclusion,
despite the mathematical issues.  We may re-examine this issue in the future.

.. [#] Returning to the Unit monoid example, there is no obvious
       implementation of uncertainty for {@}.

Monoid Examples
---------------

Most of our monoids can be created fairly simply

>>> from general.scans.monoid import *
>>> s = Sum(2.0)
>>> x = Average(1.0)
>>> p = Polarisation(ups=100.0, downs=0.0)
>>> lst = MonoidList([p, x, s])

The first rule of monoids is that we can always add to values together

>>> s + 3
Sum(5.0)
>>> x + Average(5, count=2)
Average(6.0, count=3)
>>> p + Polarisation(ups=100, downs=400)
Polarisation(200.0, 400.0)
>>> lst + [300, 3, Sum(1)]
MonoidList([Polarisation(400.0, 0.0), Average(4.0, count=2), Sum(3.0)])

The second rule of monoids is that adding zero to something *always*
returns the original value.  This overrides other behaviours.

>>> s + 0
Sum(2.0)
>>> x + 0
Average(1.0, count=1)
>>> x + Average(0)
Average(1.0, count=2)
>>> sum([x, x, 0, 0, 0, 8, Average(0), Average(0)])
Average(10.0, count=5)
>>> p + 0
Polarisation(100.0, 0.0)
>>> lst + 0
MonoidList([Polarisation(100.0, 0.0), Average(1.0, count=1), Sum(2.0)])

Where appropriate, monoids can be cast into a float

>>> float(s)
2.0
>>> float(x)
1.0
>>> float(p)
1.0

Similarly, casting to a string is also available

>>> str(s)
'2.0'
>>> str(x)
'1.0'
>>> str(p)
'1.0'
>>> str(lst)
'[1.0, 1.0, 2.0]'

Every element has an associate uncertainty

>>> s.err()
1.4142135623730951
>>> lst.err()
[0.1414213562373095, 1.4142135623730951, 1.4142135623730951]
>>> Polarisation(8.0, 8.0).err()
0.25

The MonoidList has a couple of extra list related functionality.  It
can be iterated, like a normal list.

>>> lst += [0, -3, 8]
>>> for l in lst:
...    print(l)
1.0
-1.0
10.0

You can also find the minimum and maximum value

>>> lst.min()
Average(-2.0, count=2)
>>> lst.max()
Sum(10.0)


Models
======

All models for fitting should derive from the :class:`fit.Fit`
class.  However, this class is likely too generic for common use, as
it expects the instrument scientist to implement their own fitting
procedures.  While this is useful for implementing classes like
:class:`fit.PolyFit`, where we can take advantage of our
knowledge of the model to get an exact fitting procedure, most models
will not need this level of control.  For this reason, there is a
subclass :class:`fit.CurveFit` which simplifies this work as
much as possible.  Implementing a new model with `CurveFit` for fitting
requires implementing three functions.

_model
  This function should take a list of x coordinates as its first
  parameter.  The remaining function parameters should be the
  parameters of the model.  This function should return the value of
  the model at those x-coordinates for the model with the given parameters

guess
  This function takes two parameters - the lists of x and y
  coordinates for the data set.  The return value is a list of
  approximate values for the correct parameters to the _model
  function.  This rough approximation is used as the starting point
  for the fitting procedure.

readable
  This function operates on a list of parameters values like the kind
  returned by ``guess``.  It returns a dictionary with each parameter
  given a human readable name.  The purpose is to make it easier for
  users to understand the results of the fit.
