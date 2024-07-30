"""This module exists to make mock version of the beamline

This module creates mocks to handle classes that may not be available
on development or testing machines.
"""

from mock import Mock
import numpy as np
from random import *

# Seed the random number generator so that unit tests always produce
# the same images
np.random.seed(0)

g = Mock()
g.__ge__ = lambda self, compare: True
g.period = 0
g.frames = 0
g.uamps = 0
g.runnumber = 1

g.get_period.side_effect = lambda: g.period
g.get_frames.side_effect = lambda: g.frames
g.get_uamps.side_effect = lambda: randint(1, 100)
g.get_runnumber.side_effect = range(1, 1000)


def get_pv_from_block(name):
    """
    Fake get_pv_from_block for mock genie_python
    """
    if name == "Theta":
        return "PV:THETA"
    if name == "Two_Theta":
        return "PV:TWO_THETA"
    return "PV:UNKNOWN"


def pv_exists(pv_name):
    """Fake pv_exists for mock genie_python"""
    return pv_name in PVS


g.adv.get_pv_from_block.side_effect = get_pv_from_block
# pylint: disable=protected-access
g._genie_api.pv_exists.side_effect = pv_exists

PVS = {"PV:THETA.EGU": "deg", "PV:TWO_THETA.EGU": "deg",
       "CS:SB:Theta.RDBD": 1.5,
       "REFL_01:CONST:S1_Z": -2300.0,
       "REFL_01:CONST:S2_Z": -300.0,
       "REFL_01:CONST:SM2_Z": -1000.0,
       "REFL_01:CONST:SAMPLE_Z": 0.0,
       "REFL_01:CONST:S3_Z": 50.0,
       "REFL_01:CONST:S4_Z": 3000.0,
       "REFL_01:CONST:PD_Z": 3010.0,
       "REFL_01:CONST:S3_MAX": 100.0,
       "REFL_01:CONST:S4_MAX": 10.0,
       "REFL_01:CONST:MAX_THETA": 5.0,
       "REFL_01:CONST:NATURAL_ANGLE": 2.3,
       "REFL_01:CONST:HAS_HEIGHT2": "YES"
       }


def set_pv(pv_name, value, **kwargs):
    """
    Fake set_pv for mock genie_python
    """
    # pylint: disable=unused-argument
    PVS[pv_name] = value


def get_pv(pv_name, **kwargs):
    """
    Fake get_pv for mock genie_python
    """
    # pylint: disable=unused-argument
    # return PVS.get(pv_name, 0)
    return PVS.get(pv_name, "")


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

instrument = {"Theta": 0, "Two_Theta": 0, "MODE": 'Solid',
              "S1HC": 0, "S2HC": 0, "S3HC": 0, "S4HC": 0,
              "S1AVG": 10.0}

g.get_blocks.side_effect = instrument.keys


def fake_spectrum(channel, period):  # pragma: no cover
    """Create a fake intensity spectrum."""
    if channel == 1:
        return {"signal": np.zeros(1000) + 1}
    x = np.arange(1000)
    base = np.cos(0.01 * (instrument["Theta"] + 1.05) * x) + 1
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
        base += (1 + np.cos(g.cget("Theta")["value"])) * \
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
