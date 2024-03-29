"""This module holds small utilities for the Larmor beam line

While this servers as a general placehoold for minor scripts,
An attempt should be made to keep this module small and
eventually migrate code from here into more specific modules.
"""


from logging import debug
# import time
from technique.sans.genie import gen


def flipper1(state=None):
    """Set the state of the spinflipper.  0 is flipper off, and 1 flipper is running"""
    if state==0 or state ==1:
        gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", state)
    # time.sleep(5)
    flipstate = gen.cget('flipper_onoff', state)
    debug("Flipstate=" + str(flipstate))
