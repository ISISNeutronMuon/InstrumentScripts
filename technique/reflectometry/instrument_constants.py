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
        """
        self.s1s2 = None
        self.s2sa = None
        self.max_theta = None
        self.s4max = None
        self.s3max = None
        self.has_height2 = None
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
        
    def __repr__(self):
        return "Constants: {}".format(self.__dict__)

## Below section to be edited and moved to other file in instrument folder.
# def get_instrument_constants():
    # """
    # Returns: constants for the current instrument from PVs defined in the refl server
    # """
    # try:
        # s1_z = get_reflectometry_value("S1_Z")
        # s2_z = get_reflectometry_value("S2_Z")
        # sm_z = get_reflectometry_value("SM_Z") # set to SM2_Z for now, needs updating to include both.
        # sample_z = get_reflectometry_value("SAMPLE_Z")
        # s3_z = get_reflectometry_value("S3_Z")
        # s4_z = get_reflectometry_value("S4_Z")
        # pd_z = get_reflectometry_value("PD_Z")
        # s3_max = get_reflectometry_value("S3_MAX")
        # s4_max = get_reflectometry_value("S4_MAX")
        # max_theta = get_reflectometry_value("MAX_THETA")
        # natural_angle = get_reflectometry_value("NATURAL_ANGLE")
        # has_height2 = get_reflectometry_value("HAS_HEIGHT2") == "YES"
        # s3_beam_blocker_offset = get_reflectometry_value("S3_BEAM_BLOCKER_OFFS")
        # angle_for_s3_offset = get_reflectometry_value("ANGLE_FOR_S3_OFFSET")

        # return InstrumentConstant(
            # s1s2=s2_z - s1_z,
            # s2sa=sample_z - s2_z,
            # max_theta=max_theta,  # usual maximum angle
            # s4max=s4_max,  # max s4_vg at max Theta
            # s3max=s3_max,  # max s4_vg at max Theta
            # sm_sa=sample_z - sm_z,
            # incoming_beam_angle=natural_angle,
            # has_height2=has_height2,
            # s3_beam_blocker_offset=s3_beam_blocker_offset,
            # angle_for_s3_offset=angle_for_s3_offset
            # )
    # except Exception as e:
        # raise ValueError("No instrument value pvs to calculate requested result: {}".format(e))


# def get_reflectometry_value(value_name, raise_on_not_found=True):
    # """
    # :param value_name: name of the value
    # :return: value for the value_name stored in the pv on the REFL server
    # :raises IOError: if PV does not exist
    # """
    # pv_name = "REFL_01:CONST:{}".format(value_name)
    # value = g.get_pv(pv_name, is_local=True)
    # if raise_on_not_found and value is None:
        # raise IOError("PV {} does not exist".format(pv_name))

    # return value
