# Auxiliary constants union set
NATURAL_ANGLE = 2.3                     # Natural angle of the beam
MAX_THETA = 4.5                         # Maximum Theta value
S3_MAX = 130.0                          # Maximum S3 gap - DO WE NEED THIS?
S4_MAX = 130.0                          # Maximum S4 gap - NEEDED FOS SURF
HAS_HEIGHT2 = "YES"                     # Whether two height stages are present (this is the case on TS2, but not TS1)
VSLITS_INDICES = ["1", "1a", "2", "3"]  # For allowing iteration when setting or getting slit gaps
HSLITS_INDICES = ["1", "2", "3"]        # For allowing iteration when setting or getting slit gaps
SM_BLOCK = "SM2"                        # Main supermirror block (if several are present)
SM_DEFAULTS = {'SM1': 0.0, 'SM2': 0.0}  # Default angles for the supermirror(s) - parked angle
OSC_BLOCK = "S2HG"                      # Default block for oscillating horizontal gap use in transmissions
TRANSMISSON_HEIGHT_OFFSET = 5.0         # Default offset of (fine/main) height for lowering sample during transmissions
TRANSMISSON_HEIGHT_OFFSET_MAX = 10.0    # Maximimum height offset to be used with fine height. Larger setpoints will use the coarse height.
LASER_OFFSET_BLOCK = "b.KEYENCE"        # Block name of Keyence readback - could/should be the same on all instruments



# OFFSPEC
add_constant(BeamlineConstant("OPI", "OFFSPEC", "OPIs to show on front panel"))

add_constant(BeamlineConstant("MAX_THETA", 4.5, "Maximum Theta value"))  # TODO
natural_angle = -2.3
add_constant(BeamlineConstant("NATURAL_ANGLE", natural_angle, "Natural angle of the beam"))
add_constant(BeamlineConstant("S3_MAX", S3_MAX, "Max S3 VGAP"))
add_constant(BeamlineConstant("S4_MAX", S4_MAX, "Placeholder"))
add_constant(BeamlineConstant("S4_Z", Z_S4, "Placeholder"))
add_constant(BeamlineConstant("PD_Z", Z_PD, "Placeholder"))
add_constant(BeamlineConstant("HAS_HEIGHT2", HAS_HEIGHT2, "Coarse/Fine height both present"))

# INTER
add_constant(BeamlineConstant("OPI", "INTER", "OPIs to show on front panel"))
add_constant(BeamlineConstant("Slits", "[1, 2]", "Slit list"))
add_constant(BeamlineConstant("MAX_THETA", 2.3, "Maximum Theta value"))
add_constant(BeamlineConstant("NATURAL_ANGLE", 2.3, "Natural angle of the beam below horizon"))
add_constant(BeamlineConstant("HAS_HEIGHT2", True, "Has second height stage"))

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

# POLREF
