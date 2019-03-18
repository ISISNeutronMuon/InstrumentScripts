from genie_python import genie as g

CRISP_LOOKUP = {"S1S": "MOT:MTR0101",
                "S1N": "MOT:MTR0102",
                "S1E": "MOT:MTR0103",
                "S1W": "MOT:MTR0104",
                "S1H": "MOT:MTR0105",
                "SMROT": "MOT:MTR0106",

                "S2S": "MOT:MTR0201",
                "S2N": "MOT:MTR0202",
                "S2E": "MOT:MTR0203",
                "S2W": "MOT:MTR0204",
                "S2H": "MOT:MTR0205",
                "PHI MON": "MOT:MTR0206",
                "PHI": "MOT:MTR0207",
                "PSI": "MOT:MTR0208",

                "MAGPHI": "MOT:MTR0301",
                "MAGHEIGHT": "MOT:MTR0302",
                "HEIGHT": "MOT:MTR0303",
                "TRANS": "MOT:MTR0304",
                "HUBER PHI": "MOT:MTR0305",
                "HUBER PSI": "MOT:MTR0306",
                "OCPHI": "MOT:MTR0307",
                "TRANS MON": "MOT:MTR0308",

                "S3HI": "MOT:MTR0401",
                "S3LO": "MOT:MTR0402",
                "S3HI MON": "MOT:MTR0403",
                "S3LO OLD": "MOT:MTR0404",
                "S3RIGHT": "MOT:MTR0405",
                "S3LEFT": "MOT:MTR0406",

                "ANTSAMP": "MOT:MTR0501",
                "ANTDET": "MOT:MTR0502",
                "ANTRANS": "MOT:MTR0503",
                "ANANG": "MOT:MTR0504",
                "S3HEIGHT": "MOT:MTR0505",

                "S4S": "MOT:MTR0601",
                "S4N": "MOT:MTR0602",
                "S4E": "MOT:MTR0603",
                "S4W": "MOT:MTR0604",
                "S4H": "MOT:MTR0605",
                "S4ROT": "MOT:MTR0606",
                "MDHEIGHT": "MOT:MTR0607"}

ENUM_SET = "Set"
ENUM_USE = "Use"


def zero_motor_at(axis_name, zero_value):
    """
    Redefines zero for the given motor axis to be at the given position.

    Args:
        axis_name (str): The name of the motor axis to redefine.
        zero_value (float): The current position which should be redefined as the motor zero position.

    """
    try:
        pv_lookup = CRISP_LOOKUP
        motor_pv = g.prefix_pv_name(pv_lookup[axis_name])
        motor_set_pv = motor_pv + ".SET"
        curr_pos = g.get_pv(motor_pv)
        redef_pos = curr_pos - zero_value
        g.set_pv(motor_set_pv, ENUM_SET)
        g.adv.wait_for_pv(motor_set_pv, ENUM_SET)
        g.set_pv(motor_pv + ".VAL", redef_pos)
        g.adv.wait_for_pv(motor_pv, redef_pos)
        g.set_pv(motor_pv + ".SET", ENUM_USE)
        g.adv.wait_for_pv(motor_set_pv, ENUM_USE)
    except KeyError:
        print("Motor axis {} does not exist.".format(axis_name))
    except Exception as e:
        print(e.message)
