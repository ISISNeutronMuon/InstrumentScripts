"""
Instrument specific constants
"""
from ast import literal_eval
from dataclasses import dataclass, field

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g


@dataclass
class InstrumentConstants:
    MAX_THETA: float = field(default_factory=lambda: get_reflectometry_value("MAX_THETA"))
    HAS_HEIGHT2: str = field(default_factory=lambda: get_reflectometry_value("HAS_HEIGHT2"))
    VSLITS_INDICES: list = field(default_factory=lambda: get_reflectometry_value("VSLITS_INDICES"))
    HSLITS_INDICES: dict = field(default_factory=lambda: get_reflectometry_value("HSLITS_INDICES"))

    s1s2: float = field(default_factory=lambda: get_reflectometry_value("S2_Z") - get_reflectometry_value("S1_Z"))
    s2sa: float = field(default_factory=lambda: get_reflectometry_value("SAMPLE_Z") - get_reflectometry_value("S2_Z"))
    s3max: float = field(default_factory=lambda: get_reflectometry_value("S3_MAX"))
    s4max: float = field(default_factory=lambda: get_reflectometry_value("S4_MAX"))
    s3_beam_blocker_offset: float = field(default_factory=lambda: get_reflectometry_value("S3_BEAM_BLOCKER_OFFS"))
    angle_for_s3_offset: float = 0.7

    SM_BLOCK: str = field(default_factory=lambda: get_reflectometry_value("SM_BLOCK"))
    HG_DEFAULTS: dict = field(default_factory=lambda: get_reflectometry_value("HG_DEFAULTS"))
    SM_DEFAULTS: dict = field(default_factory=lambda: get_reflectometry_value("SM_DEFAULTS"))
    OSC_BLOCK: float = field(default_factory=lambda: get_reflectometry_value("OSC_BLOCK"))
    trans_angle: float = field(default_factory=lambda: get_reflectometry_value("TRANS_ANGLE"))
    TRANSMISSION_HEIGHT_OFFSET: float = field(
        default_factory=lambda: get_reflectometry_value("TRANSMISSION_HEIGHT_OFFSET"))
    TRANSMISSION_FINE_Z_OFFSET_MAX: float = field(
        default_factory=lambda: get_reflectometry_value("TRANSMISSION_FINE_Z_OFFSET_MAX"))
    periods: int = field(default_factory=lambda: get_reflectometry_value("PERIODS"))


def get_instrument_constants():
    return InstrumentConstants()


def get_reflectometry_value(value_name):
    """
    :param value_name: name of the value
    :return: value for the value_name stored in the pv on the REFL server
    :raises IOError: if PV does not exist
    """
    pv_name = "REFL_01:CONST:{}".format(value_name)
    value = g.get_pv(pv_name, is_local=True)  # TODO: Need some kine of try block here
    # except UnableToConnectToPVException:??

    if value == "":  # or whatever gets returned from the above exception
        return None
    elif isinstance(value, str):
        try:
            # this will try and convert from str to dict/list
            value = literal_eval(value)
        except ValueError:
            # probably OK, just return the original string
            return value
        except SyntaxError:
            # Not ok, raise here, a list has probably not been finished with a ] or similar
            raise Exception(f"Constant {value_name} cannot be parsed, evaluating {value} threw an exception")
    else:
        return value
