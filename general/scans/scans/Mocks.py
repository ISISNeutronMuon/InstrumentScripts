"""This module exists to make mock version of the beamline

This module creates mocks to handle classes that may not be available
on development or testing machines.
"""

from mock import Mock
import numpy as np

g = Mock()
g.period = 0
g.frames = 0
g.get_period.side_effect = lambda: g.period
g.get_frames.side_effect = lambda: g.frames


def cget(block):
    """Fake cget for the fake genie_python"""
    if block in instrument:
        return {"value": instrument[block]}
    return None


def cset(block, value):
    """Fake cset for the fake genie_python"""
    instrument[block] = value


g.cget.side_effect = cget
g.cset.side_effect = cset


instrument = {"Theta": 0, "Two_Theta": 0}

g.get_blocks.side_effect = instrument.keys


def fake_spectrum(channel, period):  # pragma: no cover
    """Create a fake intensity spectrum."""
    if channel == 1:
        return {"signal": np.zeros(1000)+1}
    x = np.arange(1000)
    base = np.cos(0.01*(instrument["Theta"]+1.05)*x)+1
    if period % 2 == 0:
        base = 2 - base
    base *= 100000
    base += np.sqrt(base) * (2 * np.random.rand(1000) - 1)
    base /= x
    return {"signal": base}


g.get_spectrum.side_effect = fake_spectrum

lm = Mock()

RUNSTATE = "SETUP"


def get_runstate():
    """Get the run state of the instrument"""
    return RUNSTATE


g.get_runstate.side_effect = get_runstate
