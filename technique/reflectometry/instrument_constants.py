"""
Instrument specific constants
"""
from ast import literal_eval
from dataclasses import dataclass

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g


@dataclass
class InstrumentConstant(object):  # TODO: Do we need this class??
    """
    Defines full set of constants for reflectometer. These should be common to all reflectometry instruments.
    If some are constant everywhere then set value, otherwise default to None so "None" is only handling needed in NR_Motion etc.

    Instrument constants
    Args:
        s1s2: distance from s1 to s2
        s2sa: distance from s2 to sample
        max_theta: maximum allowed theta
        s4max: slit 4 maximum vertical gap
        s3max: slit 3 maximum vertical gap
        has_height2: has a height2 stage so height 2 tracks but height doesn't
        s3_beam_blocker_offset:
        angle_for_s3_offset:
        vslits: list of indices of vertical slits present (e.g. ["1", "2", "3"])
        hslits: list of indices of horiztonal slits present (e.g. ["1", "2", "3"])
        periods: default soft periods to reset back at run start. If none, doesn't change.
        smblock: block used as default supermirror. If None no mirror used. (e.g. "SM2")
        hgdefaults: default horizontal slit gap openings. Dict.
        smdefaults: default supermirrors and angles. Dict. (e.g. {'SM1': 0.0, 'SM2': 0.0})
        oscblock: default block used for oscillating slit.
        trans_angle: default angle used for setting s1vg and s2vg in transmission if not provided.
        trans_offset: default height offset for transmission in mm. Positive value moves sample down.
        max_fine_trans: default maximum height offset for transmission in mm using sample-defined height.
                        Absolute greater than this will default to "height2".
    """
    # TODO: possible define s1s2 and s2sa in constants file and import that
    # s1_z: float                     # get_reflectometry_value("S1_Z")
    # s2_z: float                     # get_reflectometry_value("S2_Z")
    # sample_z: float                 # get_reflectometry_value("SAMPLE_Z")

    s1s2: float
    s2sa: float
    MAX_THETA: float                # get_reflectometry_value("MAX_THETA")
    s3max: float                    # get_reflectometry_value("S3_MAX")
    HAS_HEIGHT2: str                # get_reflectometry_value("HAS_HEIGHT2") == "YES"
    # TODO: Think above are all defined the same across all instruments but need to check.
    s4max: float
    s3_beam_blocker_offset: float   # get_reflectometry_value("S3_BEAM_BLOCKER_OFFS")
    angle_for_s3_offset: float
    VSLITS_INDICES: list
    HSLITS_INDICES: list
    SM_BLOCK: str                    # "SM2"
    HG_DEFAULTS: dict
    SM_DEFAULTS: dict                # = {'SM1': 0.0, 'SM2': 0.0}
    OSC_BLOCK: str
    trans_angle: float              # TODO: do we need this?
    TRANSMISSION_HEIGHT_OFFSET: float             # = get_reflectometry_value("TRANS_OFFSET")
    TRANSMISSION_FINE_Z_OFFSET_MAX: float           # = get_reflectometry_value("MAX_FINE_TRANS")
    periods: int = 1

    def __repr__(self):
        return "Constants: {}".format(self.__dict__)


def get_instrument_constants():
    """
    Returns: constants for the current instrument from PVs defined in the refl server
    """

    return InstrumentConstant(
        s1s2 = get_reflectometry_value("S2_Z") -  get_reflectometry_value("S1_Z"),
        s2sa = get_reflectometry_value("SAMPLE_Z") - get_reflectometry_value("S2_Z"),
        MAX_THETA = get_reflectometry_value("MAX_THETA"),
        s3max = get_reflectometry_value("S3_MAX"),
        HAS_HEIGHT2 = get_reflectometry_value("HAS_HEIGHT2"),
        s4max = get_reflectometry_value("S4_MAX"),
        s3_beam_blocker_offset = get_reflectometry_value("S3_BEAM_BLOCKER_OFFS"),
        angle_for_s3_offset = 0.7,
        VSLITS_INDICES = get_reflectometry_value("VSLITS_INDICES"),
        HSLITS_INDICES = get_reflectometry_value("HSLITS_INDICES"),
        SM_BLOCK = get_reflectometry_value("SM_BLOCK"),
        HG_DEFAULTS = get_reflectometry_value("HG_DEFAULTS"),
        SM_DEFAULTS = get_reflectometry_value("SM_DEFAULTS"),
        OSC_BLOCK = get_reflectometry_value("OSC_BLOCK"),
        trans_angle = get_reflectometry_value("TRANS_ANGLE"),
        TRANSMISSION_HEIGHT_OFFSET = get_reflectometry_value("TRANSMISSION_HEIGHT_OFFSET"),
        TRANSMISSION_FINE_Z_OFFSET_MAX = get_reflectometry_value("TRANSMISSION_FINE_Z_OFFSET_MAX"),
        periods = get_reflectometry_value("PERIODS")
    )


def get_reflectometry_value(value_name):
    """
    :param value_name: name of the value
    :return: value for the value_name stored in the pv on the REFL server
    :raises IOError: if PV does not exist
    """
    pv_name = "REFL_01:CONST:{}".format(value_name)
    value = g.get_pv(pv_name, is_local=True)  # TODO: Need some kine of try block here
    # except UnableToConnectToPVException:??

    if value == "": # or whatever gets returned from the above exception
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
