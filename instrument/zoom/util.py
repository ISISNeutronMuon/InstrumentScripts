"""This module holds small utilities for the Larmor beam line

While this servers as a general placehoold for minor scripts,
An attempt should be made to keep this module small and
eventually migrate code from here into more specific modules.
"""


from logging import debug
# import time
from technique.sans.genie import gen


def flipper1(state=None):
    """Set the state of the spinflipper. """
    """Spin flipper current switches between -2 and +2. Flipper +2V is Flipper On/Active."""
    work_curr=2
    if state==0 or state ==1:
        gen.cset('Spin_flipper', 2*(state-0.5)*work_curr)
        gen.cset('flipper_onoff', state)
    flipstate = gen.cget('flipper_onoff')
    debug("Flipstate=" + str(flipstate))




