"""The Util module contains functions which are useful for the
instrument scientist in defining their beamline.  Nothing in this
module should ever need to be called by the end user.

"""
from functools import wraps
import numpy as np

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

        if count:
            return np.linspace(start, stop, count)

        if step:
            return np.arange(start, stop, step)

    if start is not None and count and (stride or step):
        if stride:
            step = stride
        return np.linspace(start, start + (count - 1) * step, count)
    raise RuntimeError("Unable to build a scan with that set of options.")


def local_wrapper(obj, method):
    """Get a function that calls a METHOD on object OBJect"""
    try:
        @wraps(getattr(obj, method, lambda: None))
        def inner(*args, **kwargs):
            """Call the method without the object"""
            return getattr(obj, method)(*args, **kwargs)
        return inner
    except AttributeError:
        def inner(*args, **kwargs):  # pylint: disable=unused-argument
            """Call the method without the object"""
            raise RuntimeError("Stupid Mock Issue")
