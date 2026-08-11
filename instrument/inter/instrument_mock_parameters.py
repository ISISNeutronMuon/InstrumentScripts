"""
Specific instrument parameters to be imported into technique/reflectometry/mocks.py
So that mocks behave correctly for the correct instrument.
"""

# INTER Mock settings

PVS = {"PV:THETA.EGU": "deg", "PV:TWO_THETA.EGU": "deg",
       "CS:SB:Theta.RDBD": 1.5,
       "REFL_01:CONST:S1_Z": -2300.0,
       "REFL_01:CONST:S2_Z": -300.0,
       "REFL_01:CONST:SM2_Z": -1000.0,
       "REFL_01:CONST:SAMPLE_Z": 0.0,
       "REFL_01:CONST:SM_Z": 0.0,
       "REFL_01:CONST:S3_Z": 50.0,
       "REFL_01:CONST:S4_Z": 3000.0,
       "REFL_01:CONST:PD_Z": 3010.0,
       "REFL_01:CONST:S3_MAX": 100.0,
       "REFL_01:CONST:S4_MAX": 10.0,
       "REFL_01:CONST:MAX_THETA": 5.0,
       "REFL_01:CONST:NATURAL_ANGLE": 2.3,
       "REFL_01:CONST:HAS_HEIGHT2": "True",
       "REFL_01:CONST:VSLITS_INDICES": ["1", "1A", "2", "3"],
       "REFL_01:CONST:HSLITS_INDICES": ["1", "2", "3"],
       "REFL_01:CONST:HG_DEFAULTS": {'S1HG': 40.0, 'S2HG': 30},
       "REFL_01:CONST:SM_BLOCK": "SM2",
       "REFL_01:CONST:OSC_BLOCK": "S2HG",
       "REFL_01:CONST:SM_DEFAULTS": {'SM1': 0.0, 'SM2': 0.0},
       "REFL_01:CONST:TRANSM_HT_OFFS": 5.0,
       "REFL_01:CONST:TRANSM_FIN_Z_OFFS_M": 10,
       "REFL_01:CONST:S3_BEAM_BLOCK_OFFS": 0,
       "REFL_01:CONST:TRANS_ANGLE": 0.7,
       "REFL_01:CONST:PERIODS": 1
       }


instrument = {"Theta": 0, "Two_Theta": 0, "MODE": 'Solid',
              "S1HG": 50.0, "S2HG": 30, "S3HG": 30,
              "S1HC": 0, "S2HC": 0, "S3HC": 0, "S4HC": 0, "S1AVG": 10.0,
              "S3_BEAM_BLOCKER_OFFS": 0, "MODE": "SOLID"}

SE = {  # HPLC blocks:
    "knauer2": 3, "KNAUER": 1, "Component_A": 100, "Component_B": 0, "Component_C": 0, "Component_D": 0,
    "start_pump_for_time": 0, "start_pump_for_volume": 1, "hplcflow": 2.0, "pump_for_time": 0, "pump_for_volume": 1}
