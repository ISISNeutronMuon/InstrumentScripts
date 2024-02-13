"""
Instrument specific constants
"""
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g

from ast import literal_eval


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
        self.max_theta = max_theta
        self.s4max = s4max
        self.sm_sa = sm_sa
        self.s3max = s4max if s3max is None else s3max
        self.has_height2 = has_height2
        self.incoming_beam_angle = incoming_beam_angle

    def __repr__(self):
        return "s1s2={}, s2sa={}, sm_sa={}, max_theta={}, s3max={}, s4max={}, has_height_2={}, natural_angle={}".format(
            self.s1s2, self.s2sa, self.sm_sa, self.max_theta, self.s3max, self.s4max, self.has_height2,
            self.incoming_beam_angle
        )


def get_instrument_constants():
    """
    Returns: constants for the current instrument from PVs defined in the refl server
    """
    try:
        s1_z = get_reflectometry_value("S1_Z")
        s2_z = get_reflectometry_value("S2_Z")
        sm_z = get_reflectometry_value("SM2_Z") # set to SM2_Z for now, needs updating to include both.
        sample_z = get_reflectometry_value("SAMPLE_Z")
        s3_z = get_reflectometry_value("S3_Z")
        s4_z = get_reflectometry_value("S4_Z")
        pd_z = get_reflectometry_value("PD_Z")
        s3_max = get_reflectometry_value("S3_MAX")
        s4_max = get_reflectometry_value("S4_MAX")
        max_theta = get_reflectometry_value("MAX_THETA")
        natural_angle = get_reflectometry_value("NATURAL_ANGLE")
        has_height2 = get_reflectometry_value("HAS_HEIGHT2") == "YES"

        return InstrumentConstant(
            s1s2=s2_z - s1_z,
            s2sa=sample_z - s2_z,
            max_theta=max_theta,  # usual maximum angle
            s4max=s4_max,  # max s4_vg at max Theta
            s3max=s3_max,  # max s4_vg at max Theta
            sm_sa=sample_z - sm_z,
            incoming_beam_angle=natural_angle,
            has_height2=has_height2)
    except Exception as e:
        raise ValueError("No instrument value pvs to calculated requested result: {}".format(e))


def get_reflectometry_value(value_name):
    """
    :param value_name: name of the value
    :return: value for the value_name stored in the pv on the REFL server
    :raises IOError: if PV does not exist
    """
    pv_name = "REFL_01:CONST:{}".format(value_name)
    value = g.get_pv(pv_name, is_local=True)

    if isinstance(value, str)
        try:
            # this will try and convert from str to dict/list
            value = literal_eval(value)
        except ValueError:
            # probably OK, just return the original string
            return value
        except SyntaxError:
            # Not ok, raise here, a list has probably not been finished with a ] or similar
            raise Exception(f"Constant {value_name} cannot be parsed, evaluating {value} threw an exception")


    return value
