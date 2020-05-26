"""This module contains helper classes for controlling motions on the beamline

There's two levels of depth to this module.  At the simplest level the BlockMotion class,
allows for creating single objects that correspond to single IBEX blocks.

At the bottom, BlockMotion derives from the Motion object,
which gives a simple framework for all physical parameters that
can be controlled by an instrument.  Although it is called Motion,
it will also handle temperatures, currents, and other physical properties.
"""

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .mocks import g

from six import text_type


class Motion(object):
    # pylint: disable=too-many-instance-attributes
    """A Motion object largely acts like a function to control and
    interrogate a single axis of motion.  When called without a
    parameter, it returns the current position.  Being called with a
    parameter causes the position to update.

    We can also define getters and setters for velocity of the motor,
    and a getter for the tolerance of the motor.

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
                 tolerance_getter=None, unit=None):
        self.getter = getter
        self.setter = setter
        self.title = title
        self.unit = unit
        self._low = low
        self._high = high

        self._velocity_getter = velocity_getter
        self._velocity_setter = velocity_setter

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

        return True, "Position is Accessible"

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
        """
        The velocity of the motor
        """
        return self._velocity_getter()

    @velocity.setter
    def velocity(self, vel):
        self._velocity_setter(vel)

    @property
    def tolerance(self):
        """
        The tolerance (deadband) of the motor
        """
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

    def __init__(self, block, unit):
        blocks = g.get_blocks()
        if block not in blocks:
            new_name = [name for name in blocks
                        if name and name.lower() == block.lower()]
            if new_name:
                block = new_name[0]
            else:
                raise RuntimeError("Unknown block {}.".format(block))
        Motion.__init__(self,
                        lambda: g.cget(block)["value"],
                        lambda x: g.cset(block, x),
                        block, unit=unit,
                        # Workarounds until a better solution to get fields
                        # from blocks is implemented in IBEX. Note that IBEX
                        # blocks must point at AXIS:MTR rather than AXIS for
                        # this to work.
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
                  unit=g.get_pv(pv_str+".EGU"),
                  velocity_getter=lambda: g.get_pv(
                      "{}.VELO".format(pv_str)),
                  velocity_setter=lambda x: g.set_pv(
                      "{}.VELO".format(pv_str), x),
                  tolerance_getter=lambda: g.get_pv(
                      "{}.RDBD".format(pv_str)))


def get_motion(motion_or_block_name):
    """
    Get a motion object from the argument. Use to pass a motion argument in scans.

    Parameters
    ----------
    motion_or_block_name
      either a motion object or a block name

    Returns
    -------
    motion object
    """
    if isinstance(motion_or_block_name, Motion):
        motion = motion_or_block_name
    elif isinstance(motion_or_block_name, (str, text_type)):
        motion = BlockMotion(motion_or_block_name, get_units(motion_or_block_name))
    else:
        raise TypeError("Cannot run scan on axis {}. Try a string or a motion object instead.".format(
            motion_or_block_name))
    return motion


def get_units(block_name):
    """
    Get the physical measurement units associated with a block name.

    Parameters
    ----------
    block_name: name of the block

    Returns
    -------
    units of the block
    """
    pv_name = g.adv.get_pv_from_block(block_name)
    if "." in pv_name:
        # Remove any headers
        pv_name = pv_name.split(".")[0]
    unit_name = pv_name + ".EGU"
    # pylint: disable=protected-access
    if getattr(g, "__api").pv_exists(unit_name):
        return g.get_pv(unit_name)
    return ""
