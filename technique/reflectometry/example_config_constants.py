"""
Designed to sit in the instrument folder but shows example of how instrument constants fed through.
"""

from .instrument_constants import InstrumentConstant #TODO: check path on final location.

#TODO: the function may need renaming
def inst_script_constants():
    """
    Allows setting of specifics per instrument. Anything not set for an instrument remains as the default/None in instrumnet_constant file
    Example here for INTER.
    """
    constants = InstrumentConstant()

    #constants.s3_beam_blocker_offset = None ##Correct arguments for new beamblocker setup need to be added here.
    #constants.angle_for_s3_offset = None
    constants.VSLITS_INDICES = ["1", "1a", "2", "3"]
    constants.HSLITS_INDICES = ["1", "2", "3"]
    constants.periods = 1
    constants.SM_BLOCK = "SM2"
    constants.HG_DEFAULTS = {'S1HG': 50, 'S2HG': 30, 'S3HG': 60}
    constants.SM_DEFAULTS = {'SM1': 0.0, 'SM2': 0.0}
    constants.OSC_BLOCK = 'S2HG'
    constants.trans_angle = 0.7
    constants.TRANSMISSION_HEIGHT_OFFSET = 5
    constants.TRANSMISSION_FINE_Z_OFFSET_MAX = 10

    return constants

