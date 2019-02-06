"""This module contains helper classes for controlling motions on the beamline

There's three levels of depth to this module.  At the simplest level, merely
import and call populate().  This create motion object for every block
currently registered on the instrument.

The next level down is the BlockMotion class, which allows for creating
single objects that correspond to single IBEX blocks.

Finally, at the bottom, BlockMotion derives from the Motion object,
which gives a simple framework for all physical parameters that
can be controlled by an instrument.  Although it is called Motion,
it will also handle temperatures, currents, and other physical properties.
"""

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .mocks import g


class Motion(object):
    """A Motion object largely acts like a function to control and
    interrogate a single axis of motion.  When called without a
    parameter, it returns the current position.  Being called with a
    parameter causes the position to update.

    Example:
    Assume that we have some motion object Foo

    >>> Foo()
    7
    >>> Foo(5)
    >>> Foo()
    5

    """

    def __init__(self, getter, setter, title, low=None, high=None,
                 velocity_getter=None, velocity_setter=None,
                 tolerance_getter=None):
        self.getter = getter
        self.setter = setter
        self.title = title
        self._low = low
        self._high = high

        self._velocity = (velocity_getter, velocity_setter)

        self._tolerance_getter = tolerance_getter

    def __call__(self, x=None):
        if x is None:
            return self.getter()
        self.require(x)
        return self.setter(x)

    def __iadd__(self, x):
        self(self() + x)
        return self

    def __isub__(self, x):
        self(self() - x)
        return self

    def __imul__(self, x):
        self(self() * x)
        return self

    def __repr__(self):
        return "{} is at {}".format(self.title, self())

    def accessible(self, x):
        """Determines whether a motor can reach the desired position.

        Parameters
        ==========
        x
          The desired position for the motor

        Returns
        =======

        Tuple (Bool, Str)

        The boolean represents whether the possition can be reached
        The string is an error message explaining why the position is
        unreachable.

        """
        if self.low is not None and x < self.low:
            return (False,
                    "Position {} is below lower limit {} of motor {}".format(
                        x, self.low, self.title))
        if self.high is not None and x > self.high:
            return (False,
                    "Position {} is above upper limit {} of motor {}".format(
                        x, self.high, self.title))
        return (True, "Position is Accessible")

    def require(self, x):
        """Requires that the given position is accessible.  If not, an
        exception is thrown

        """
        success, msg = self.accessible(x)
        if success:
            return
        raise RuntimeError(msg)

    @property
    def low(self):
        """The motion's lower limit"""
        return self._low

    @low.setter
    def low(self, x):
        self._low = x

    @property
    def high(self):
        """The motion's uppder limit"""
        return self._high

    @high.setter
    def high(self, x):
        self._high = x

    @property
    def velocity(self):
        """The motion's requested speed"""
        return self._velocity[0]()

    @velocity.setter
    def velocity(self, vel):
        """Set the motion's speed"""
        self._velocity[1](vel)

    @property
    def tolerance(self):
        """The motion's tolerance"""
        return self._tolerance_getter()


class BlockMotion(Motion):
    """

    A helper class for creating motion objects from
    Ibex blocks

    Parameters
    ----------

    block
      A string containing the name of the ibex block to control
    """
    def __init__(self, block):
        if block not in g.get_blocks():
            raise RuntimeError(
                "Unknown block {}.  Does the capitalisation "
                "match IBEX?".format(block))
        Motion.__init__(self,
                        lambda: g.cget(block)["value"],
                        lambda x: g.cset(block, x),
                        block,
                        # Workarounds until a better solution to get
                        # fields from blocks is implemented in IBEX.
                        velocity_getter=lambda: g.get_pv(
                            "CS:SB:{}.VELO".format(block), is_local=True),
                        velocity_setter=lambda vel: g.set_pv(
                            "CS:SB:{}.VELO".format(block), vel, is_local=True),
                        tolerance_getter=lambda: g.get_pv(
                            "CS:SB:{}.RDBD".format(block), is_local=True),)


def pv_motion(pv_str, name):
    """Create a motion object around a PV string."""
    return Motion(lambda: g.get_pv(pv_str),
                  lambda x: g.set_pv(pv_str, x),
                  name,
                  velocity_getter=lambda: g.get_pv(
                      "{}.VELO".format(pv_str)),
                  velocity_setter=lambda x: g.set_pv(
                      "{}.VELO".format(pv_str), x),
                  tolerance_getter=lambda: g.get_pv(
                      "{}.RDBD".format(pv_str)))


def normalise_motion(motion):
    """Ensure that our motion is a true motion object."""
    if isinstance(motion, Motion):
        return motion
    if isinstance(motion, str):
        return BlockMotion(motion)
    raise TypeError(
        "Cannot run scan on axis {}. Try a string or a motion "
        "object instead.  It's also possible that you may "
        "need to rerun populate() to recreate your motion "
        "axes." .format(motion))


def populate():
    """Create Motion objects in the GLOBAL namespace for each
    block registered with IBEX."""
    for i in g.get_blocks():
        temp = BlockMotion(i)
        __builtins__[i.upper()] = temp
        __builtins__[i] = temp
        __builtins__[i.lower()] = temp
