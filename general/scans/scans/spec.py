"""The Spec module implements a couple of commond commands from SPEC."""

from . import scan


def ascan(motor, start, end, intervals, time):
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
        return scan(motor, start=start, stop=end,
                    gaps=intervals).plot(seconds=time)
    return scan(motor, start=start, stop=end,
                gaps=intervals).plot(frames=-time)


def dscan(motor, start, end, intervals, time):
    """A reimplementations of dscan from spec

    Example
    -------
    >>> dscan(COARSEZ, -20, 20, 40, -50)

    Scan the CoarseZ motor from 20 mm below the current position
    to position 20 mm above the current position (inclusive) in 1 mm steps.
    At each point, take measure for 50 frames (about five seconds).
    After the plot, the CoarseZ motor will move back to its original position.

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
            return scan(motor, before=start, after=end,
                        gaps=intervals).plot(seconds=time)
        return scan(motor, before=start, after=end,
                    gaps=intervals).plot(frames=-time)
    finally:
        motor(init)


def rscan(motor, before=None, after=None, step=None, frames=None, **kwargs):
    """An ISIS specific relative scan function

    This function is identical to the normal scan function, but it
    defaults to using relative positions, instead of absolute.

    Example
    -------
    >>> rscan(coarsez, -20, 20, 1, 50)

    Scan the CoarseZ motor from 20 mm below the current position
    to position 20 mm above the current position (exclusive) in 1 mm steps.
    At each point, take measure for 50 frames (about five seconds).
    After the plot, the CoarseZ motor will move back to its original position.

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

        return scan(motor, **kwargs)
    finally:
        motor(init)
