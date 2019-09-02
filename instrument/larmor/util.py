"""This module holds small utilities for the Larmor beam line

While this servers as a general placehoold for minor scripts,
An attempt should be made to keep this module small and
eventually migrate code from here into more specific modules.
"""


from logging import debug
# import time
from technique.sans.genie import gen


def flipper1(state=0):
    """Set the state of the spinflipper.  0 is off and 1 is on"""
    if not state:
        gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", 0)
    else:
        gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", 1)
    # time.sleep(5)
    flipstate = gen.get_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE")
    debug("Flipstate=" + str(flipstate))
