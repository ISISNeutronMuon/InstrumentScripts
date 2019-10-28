"""

This module holds the base class for the instrument defaults.
This is an abstract class which will need to be overwritten
for each beamline.  This design was chosen because the
subclass cannot be instantiated unless all of the abstract methods
have been implemented.  This means that we detect mistakes in the
subclass the moment that the Defaults object is created, instead of
in the middle of a user run when a missing method is called.

"""

from abc import ABCMeta, abstractmethod
import os
from six import add_metaclass, text_type
import matplotlib.pyplot as plt
import numpy as np
from .scans import SimpleScan, ReplayScan
from .monoid import Average
from .motion import Motion, BlockMotion
from .util import get_points, TIME_KEYS

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .mocks import g


@add_metaclass(ABCMeta)
class Defaults(object):
    """A defaults object to store the correct functions for this instrument"""

    @staticmethod
    @abstractmethod
    def detector(**kwargs):
        """
        The default function for pulling a count off the detector.
        Takes the standard time settings (e.g. seconds, frames, uamps)
        as keyword arguments.

        """

    @staticmethod
    @abstractmethod
    def log_file():
        """
        Returns the name of a unique log file where the scan data can be saved.
        """

    @staticmethod
    def get_fig():
        """
        Get a figure for the next scan.  The default method is to
        create a new figure for each scan, but this can be overridden
        to re-use the same figure, if the instrument scientist
        chooses.
        """
        fig, axis = plt.subplots()
        plt.show()
        return (fig, axis)

    def scan(self, motion, start=None, stop=None, step=None, frames=None,
             **kwargs):
        """scan establishes the setup for performing a measurement scan.

        Examples
        --------

        >>> scan(translation, -5, 5, 0.1, 50)

        This will run a scan on the translation axis from -5 to 5
        (exclusive) in steps of 0.1, measuring for 50 frames at each
        point and taking a plot

        >>> scan(translation, start=-5, stop=5, stride=0.1).plot(frames=50)

        This will scan the translation access from -5 to 5 inclusive
        in steps of 0.1.  At each point, the a measurement will be
        taken for 50 frames and plotted.

        As a different example,

        >>> s = scan(coarsez, before=-50, step=5, gaps=20)

        This will create a scan on the CoarseZ axis, starting at 50 mm
        below the current position and continuing in 5 mm increments
        for another 20 measurements (for a total of 21).  Note that
        while the scan has been created, nothing will happen until we
        ask the scan to act.

        >>> result = s.fit(PeakFit(20), uamps=0.1)

        This will perform a 0.1 uamp measurement at each point on the
        scan and find the peak (with a presumed width of 20 mm).  At
        the end of the measurement, the `result` variable will hold
        the position of the observed peak.

        >>> scan(translation, -5, 5, 0.1, 50, detector=specfic_spectra([[3]]))

        This is similar to our original scan on translation, except
        that the scan will be performed on monitor 3, instead of the
        default spectrum.  You instrument scientist may have defined
        other detectors that you can use to perform special scans.

        The scan function itself has one mandatory parameter `motion`
        but will require another three keyword parameters to define
        the range of the scan.  In the example above, the motion
        parameter was TRANSLATION and the keyword parameters were
        start, stop, and stride.  Any set of three position parameters
        that uniquely define a range of motions will be accepted.

        PARAMETERS
        ----------
        motion
          The axis on which to perform the scan
        start
          An absolute starting position for the scan.
        stop
          An absolute ending position for the scan
        step
          The absolue step size.  The final position may be skipped if
          it is not an integer number of steps from the starting
          position.
        frames
          How many frames the measurement should be performed for.  If
          set to None or 0, then no automatic plot will be started.
        before
          A relative starting position for the scan.
        after
          A relative ending position for the scan
        count
          The number of points to measure
        gaps
          The number of steps to take
        stride
          The approximate step size.  The scan may shrink this step size
          to ensure that the final point is still included in the scan.
        detector
          An optional parameter to choose how to measure the dependent
          variable in the scan.  A set of these will have already been
          defined by your instrument scientist.  If you need something
          ad hoc, then check the documentation on specific_spectra for
          more details

        Returns
        -------
        Scan
          A scan object that will run through the requested points.

        """
        if start is not None:
            kwargs["start"] = start
        if stop is not None:
            kwargs["stop"] = stop
        if step:
            kwargs["step"] = step
        if frames:
            kwargs["frames"] = frames

        if isinstance(motion, Motion):
            pass
        elif isinstance(motion, (str, text_type)):
            motion = BlockMotion(motion, self.get_units(motion))
        else:
            raise TypeError(
                "Cannot run scan on axis {}. Try a string or a motion "
                "object instead.  It's also possible that you may "
                "need to rerun populate() to recreate your motion "
                "axes." .format(motion))

        points = get_points(motion(), **kwargs)

        if len(points) == 0:  # pylint: disable=len-as-condition
            raise RuntimeError(
                "Your requested scan contains no points.  Are you "
                "trying to move a negative distance with positive "
                "steps?")

        for point in points:
            motion.require(point)

        scn = SimpleScan(motion, points, self)
        if any([x in kwargs for x in
                TIME_KEYS]):
            if "fit" in kwargs:
                return scn.fit(**kwargs)
            return scn.plot(**kwargs)
        return scn

    def ascan(self, motor, start, end, intervals, time):
        """A reimplementations of ascan from spec

        Example
        -------
        >>> ascan(COARSEZ, -20, 20, 40, -50)

        Scan the CoarseZ motor from position -20 to position 20
        (inclusive) in 1 mm steps.  At each point, take measure for
        50 frames (about five seconds). After the plot, the CoarseZ
        motor will be at position 20.

        Parameters
        ----------
        motor
        The axis to scan
        start
        The initial position
        stop
        The final position
        intervals
        How many steps to take between the initial and final position
        time
        If positive, the measurement time at each point in seconds.  If
        negative, the measurement frames at each point.

        """
        if time > 0:
            return self.scan(motor, start=start, stop=end,
                             gaps=intervals).plot(seconds=time)
        return self.scan(motor, start=start, stop=end,
                         gaps=intervals).plot(frames=-time)

    def dscan(self, motor, start, end, intervals, time):
        """A reimplementations of dscan from spec

        Example
        -------
        >>> dscan(COARSEZ, -20, 20, 40, -50)

        Scan the CoarseZ motor from 20 mm below the current position
        to position 20 mm above the current position (inclusive) in 1
        mm steps.  At each point, take measure for 50 frames (about
        five seconds).  After the plot, the CoarseZ motor will move
        back to its original position.

        Parameters
        ----------
        motor
        The axis to scan
        start
        The initial position as an offset from the current position
        stop
        The final position as an offset from the current position
        intervals
        How many steps to take between the initial and final position
        time
        If positive, the measurement time at each point in seconds.  If
        negative, the measurement frames at each point.

        """
        init = motor()
        try:
            if time > 0:
                return self.scan(motor, before=start, after=end,
                                 gaps=intervals).plot(seconds=time)
            return self.scan(motor, before=start, after=end,
                             gaps=intervals).plot(frames=-time)
        finally:
            motor(init)

    def rscan(self, motor, before=None, after=None, step=None, frames=None,
              **kwargs):
        """An ISIS specific relative scan function

        This function is identical to the normal scan function, but it
        defaults to using relative positions, instead of absolute.

        Example
        -------
        >>> rscan(coarsez, -20, 20, 1, 50)

        Scan the CoarseZ motor from 20 mm below the current position
        to position 20 mm above the current position (exclusive) in 1
        mm steps.  At each point, take measure for 50 frames (about
        five seconds).  After the plot, the CoarseZ motor will move
        back to its original position.

        Parameters
        ----------
        motor
        The axis to scan
        before
        The initial position as an offset from the current position
        after
        The ending position as an offset from the current position
        step
        The absolute step size
        frames
        The number of pulse frames to measure at each point

        """
        init = motor()
        try:
            if before:
                kwargs["before"] = before
            if after:
                kwargs["after"] = after
            if step:
                kwargs["step"] = step
            if frames:
                kwargs["frames"] = frames

            return self.scan(motor, **kwargs)
        finally:
            motor(init)

    def populate(self):
        """Create Motion objects in the GLOBAL namespace for each
        block registered with IBEX."""
        for i in g.get_blocks():
            if not isinstance(i, (str, text_type)):
                continue
            temp = BlockMotion(i, self.get_units(i))
            __builtins__[i.upper()] = temp
            __builtins__[i] = temp
            __builtins__[i.lower()] = temp

    _UNITS = {"Theta": u"deg", "Two_Theta": u"deg"}

    def get_units(self, motion):
        """Get the physical measurement units associated with a block name."""
        if motion in self._UNITS:
            return self._UNITS[motion]
        return "Unknown Unit"

    def last_scan(self, path=None, axis="replay"):
        """Load the last run scan and replay that scan

        PARAMETERS
        ----------
        path
        The log file to replay.  If None, replay the most recent scan
        axis
        The label for the x axis

        """
        if path is None:
            path = max([f for f in os.listdir(os.getcwd())
                        if f[-4:] == ".dat"],
                       key=os.path.getctime)
        with open(path, "r") as infile:
            base = infile.readline()
            axis = base.split("\t")[0]
            result = base.split("\t")[1]
            xs, ys, errs = np.loadtxt(infile, unpack=True)
            ys = [Average((y / e)**2, y / e**2) for y, e in zip(ys, errs)]
            return ReplayScan(xs, ys, axis, result, self)
