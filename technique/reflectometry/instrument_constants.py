"""
Instrument specific constants
"""
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g


class InstrumentConstant(object):
    """
    Defines full set of constants for reflectometer. These should be common to all reflectometry instruments.
    If some are constant everywhere then set value, otherwise default to None so "None" is only handling needed in NR_Motion etc.
    """
    def __init__(self):
        """
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
            max_fine_trans: default maximum height offset for transmission in mm using sample-defined height. Absolute greater than this will default to "height2".
        """

        s1_z = get_reflectometry_value("S1_Z")
        s2_z = get_reflectometry_value("S2_Z")
        sample_z = get_reflectometry_value("SAMPLE_Z")

        self.s1s2 = s2_z - s1_z
        self.s2sa = sample_z - s2_z
        self.max_theta = get_reflectometry_value("MAX_THETA")
        self.s3max = get_reflectometry_value("S3_MAX")
        self.has_height2 = get_reflectometry_value("HAS_HEIGHT2") == "YES"
        #TODO: Think above are all defined the same across all instruments but need to check.
        self.s4max = None
        self.s3_beam_blocker_offset = None
        self.angle_for_s3_offset = None
        self.vslits = None
        self.hslits = None
        self.periods = None
        self.smblock = None
        self.hgdefaults = None
        self.smdefaults = None
        self.oscblock = None
        self.trans_angle = None
        self.trans_offset = None
        self.max_fine_trans = None
        
    def __repr__(self):
        return "Constants: {}".format(self.__dict__)

def get_reflectometry_value(value_name, raise_on_not_found=True):
    """
    :param value_name: name of the value
    :return: value for the value_name stored in the pv on the REFL server
    :raises IOError: if PV does not exist
    """
    pv_name = "REFL_01:CONST:{}".format(value_name)
    value = g.get_pv(pv_name, is_local=True)
    if raise_on_not_found and value is None:
        raise IOError("PV {} does not exist".format(pv_name))

    return value
