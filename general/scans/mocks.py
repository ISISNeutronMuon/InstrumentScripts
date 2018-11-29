"""This module exists to make mock version of the beamline

This module creates mocks to handle classes that may not be available
on development or testing machines.
"""

from mock import Mock
import numpy as np

# Seed the random number generator so that unit tests always produce
# the same images
np.random.seed(0)

g = Mock()
g.period = 0
g.frames = 0
g.get_period.side_effect = lambda: g.period
g.get_frames.side_effect = lambda: g.frames


PVS = {}


def set_pv(pv, value, **kwargs):
    PVS[pv] = value


def get_pv(pv, **kwargs):
    return PVS.get(pv, 0)

g.set_pv = set_pv
g.get_pv = get_pv


def cget(block):
    """Fake cget for the fake genie_python"""
    if block in instrument:
        return {"value": instrument[block]}
    return None


def cset(block=None, value=None, **kwargs):
    """Fake cset for the fake genie_python"""
    instrument[block] = value
    for k in kwargs:
        instrument[k] = kwargs[k]


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
    if channel == 4:
        base[np.isnan(base)] = 0
        base *= 0
        print("Taking a count at theta=%0.2f and two theta=%0.2f" %
              (g.cget("Theta")["value"], g.cget("Two_Theta")["value"]))
        base += (1+np.cos(g.cget("Theta")["value"])) * \
            np.sqrt(g.cget("Theta")["value"]) + \
            g.cget("Two_Theta")["value"] ** 2 + \
            0.05 * np.random.rand()
        # raise RuntimeError(str(base))
    return {"signal": base}


g.get_spectrum.side_effect = fake_spectrum

RUNSTATE = "SETUP"


def get_runstate():
    """Get the run state of the instrument"""
    return RUNSTATE


g.get_runstate.side_effect = get_runstate
