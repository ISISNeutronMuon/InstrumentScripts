"""
Instrument specific constants
"""
from genie_python import genie as g


class InstrumentConstant(object):
    """
    Set of constants for a given instrument
    """
    def __init__(self, s1s2, s2sa, max_theta, s4max, sm_sa, incoming_beam_angle, s3max=None, has_height2=True):
        """
        Instrument constants
        Args:
            s1s2: distance from s1 to s2
            s2sa: distance from s2 to sample
            max_theta: maximum allowed theta
            s4max: slit 4 maximum vertical gap
            sm_sa: distance from super mirror to sample
            incoming_beam_angle: the incoming beam angle used to make the sample level
            s3max: slit 3 maximum vertical gap
            has_height2: has a height2 stage so height 2 tracks but height doesn't
        """
        self.s1s2 = s1s2
        self.s2sa = s2sa
        self.maxTheta = max_theta
        self.s4max = s4max
        self.SM_sa = sm_sa
        self.s3max = s4max if s3max is None else s3max
        self.has_height2 = has_height2
        self.incoming_beam_angle = incoming_beam_angle


INSTRUMENT_CONSTANTS = {
    "INTER": InstrumentConstant(
                s1s2=1940.5,
                s2sa=364.0,
                max_theta=2.3,  # usual maximum angle
                s4max=10.0,  # max s4_vg at maxTheta
                sm_sa=1375.0,
                incoming_beam_angle=2.3),
    "SURF": InstrumentConstant(
                s1s2=1578.5,  # 1448.0,
                s2sa=257.3,  # 247, #389.0,
                max_theta=1.8,  # usual maximum angle
                s4max=10.0,  # max s4vg at maxTheta
                sm_sa=1096,  # 1088.26,
                has_height2=False,
                incoming_beam_angle=1.5),
    "CRISP": InstrumentConstant(
                s1s2=2596.0,
                s2sa=343.0,
                max_theta=2,  # usual maximum angle
                s4max=20.0,  # max s4vg at maxTheta
                sm_sa=2311,
                has_height2=False,
                incoming_beam_angle=1.5),
    "DEFAULT": InstrumentConstant(
                s1s2=1940.5,
                s2sa=364.0,
                max_theta=2.3,  # usual maximum angle
                s4max=10.0,  # max s4_vg at maxTheta
                sm_sa=1385.0,
                has_height2=False,
                incoming_beam_angle=1.5),
}


def get_instrument_constants():
    """
    Returns: constants for the current instrument
    """
    instrument = g.get_instrument()
    try:
        constants = INSTRUMENT_CONSTANTS[instrument]
    except KeyError:
        print("Instrument, '', not found in constants list using default")
        constants = INSTRUMENT_CONSTANTS["DEFAULT"]
    return constants
