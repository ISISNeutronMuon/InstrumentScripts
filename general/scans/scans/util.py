"""The Util module contains functions which are useful for the
instrument scientist in defining their beamline.  Nothing in this
module should ever need to be called by the end user.

"""
import numpy as np
from .scans import SimpleScan
from .motion import Motion, BlockMotion

TIME_KEYS = ["frames", "uamps", "seconds", "minutes", "hours"]


def get_points(
        current,
        start=None, stop=None,
        step=None, stride=None,
        count=None, gaps=None,
        before=None, after=None,
        **_):
    """This function takes a dictionary of keyword arguments for
    a scan and returns the points at which the scan should be measured.


    This function provides many ways to define a scan

    - start point, stop point, and number of points
    - start point, stop point, and spacing
    - start point, spacing, and number of points

    Parameters
    ----------
    current : float
      The present position of the motor.  This is needed to relative scans.
    start : float
      The absolute first position in the scan.  This is a valid start point.
    stop : float
      The absolute final position in the scan.  This is a valid stop point.
    before : float
      The relative first position in the scan.  If the motor is currently
      at 3 and ``before`` is set to -5, then the first scan point will be -2.
      This is a valid start point.
    after : float
      The relative final position in the scan.  If the motor is currently
      at 3 and ``before`` is set to 5, then the last scan point will be 8.
      This is a valid stop point.
    step : float
      The fixed distance between points.  If the distance between the
      beginning and end aren't an exact multiple of this step size,
      then the end point will not be included.  This is a valid spacing.
    stride : float
      The approximate distance between points.  In order to ensure that
      the ``start`` and ``stop`` points are included in the scan, a finer
      resolution scan will be called for if the stride is not an exact
      multiple of the distance. This is a valid spacing.
    count : float
      The number of measurements to perform.  A scan with a ``count`` of 2
      would measure at only the beginning and the end.  This is a valid
      number of points.
    gaps : float
      The number of steps that the motor will take.  A scan with a ``gaps``
      of 1 would measure at only the beginning and the end.  This is a
      valid number of points.

    Returns
    -------
    Array of Floats
      The positions for the scan.

    Raises
    ------
    RuntimeError
      If the supplied parameters cannot be combined into a coherent scan.


    """

    if gaps:
        count = gaps + 1
    if before is not None:
        start = current + before
    if after is not None:
        stop = current + after

    if start is not None and stop is not None:
        if stride:
            steps = np.ceil((stop - start) / float(stride))
            return np.linspace(start, stop, steps + 1)
        elif count:
            return np.linspace(start, stop, count)
        elif step:
            return np.arange(start, stop, step)
    elif start is not None and count and (stride or step):
        if stride:
            step = stride
        return np.linspace(start, start + (count - 1) * step, count)
    raise RuntimeError("Unable to build a scan with that set of options.")


def make_scan(defaults):
    """This is a helper function to be used by the instrument scientist.
    Given a defaults class that holds the default values needed for
    scans, it creates a scan function that uses those default values.

    The basic usage is that the instrument science will have some
    module for setting up their instrument, which will include

    >>> scan = make_scan(my_defaults)

    The main python environment will then import scan from that module

    """
    def scan(motion, start=None, stop=None, step=None, frames=None, **kwargs):
        # def scan(motion, **kwargs):
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
        elif isinstance(motion, str):
            motion = BlockMotion(motion)
        else:
            raise TypeError(
                "Cannot run scan on axis {}. Try a string or a motion "
                "object instead.  It's also possible that you may "
                "need to rerun populate() to recreate your motion "
                "axes." .format(motion))

        points = get_points(motion(), **kwargs)

        for point in points:
            motion.require(point)

        scn = SimpleScan(motion, points, defaults)
        if any([x in kwargs for x in
                TIME_KEYS]):
            if "fit" in kwargs:
                return scn.fit(**kwargs)
            return scn.plot(**kwargs)
        return scn
    return scan
