# ## This script was generated on 15/02/2022, at 16:55:10
# ## with ScriptMaker (c) Maximilian Skoda 2020 
# ## Enjoy and use at your own risk.
from datetime import datetime
from script_actions import ScriptActions, DryRun
from sample import SampleGenerator
from contrast_change import *

import sys
import os

# sys.path.insert(0, os.path.abspath(os.path.join(r"C:\\", "Instrument", "scripts")))
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g

# from technique.reflectometry import SampleGenerator, run_angle, run_angle_new,  run_angle_SM_new,\
# 									contrast_change, transmission, transmission_new, transmission_new_SM,\
# 									run_angle_new_edit,  run_angle_SM_new_edit, transmission_new_edit, transmission_new_SM_edit

run_angle = ScriptActions.run_angle


def runscript(dry_run=False):
    sample_generator = SampleGenerator(
        translation=400.0,
        height2_offset=0.0,
        phi_offset=0.0,
        psi_offset=0.0,
        height_offset=0.0,
        resolution=0.035,
        sample_length=80,
        valve=1,
        footprint=60,
        hgaps={'S1HG': 47.9, 'S2HG': 30, 'S3HG': 60})

    sample_1 = sample_generator.new_sample(title="Si1-C19",
                                           translation=605.0,
                                           height_offset=-8.57,
                                           phi_offset=0.900 - 0.697,
                                           psi_offset=-0.0,
                                           valve=1)

    sample_2 = sample_generator.new_sample(title="Si2-P52",
                                           translation=505.0,
                                           height_offset=-8.27,
                                           phi_offset=0.874 - 0.702,
                                           psi_offset=-0.0,
                                           valve=2)

    sample_3 = sample_generator.new_sample(title="Si3-C24",
                                           translation=405,
                                           height_offset=-8.346,
                                           phi_offset=0.846 - 0.700,
                                           psi_offset=-0.0,
                                           valve=3)

    sample_4 = sample_generator.new_sample(title="Si4-unmarked",
                                           translation=305.0,
                                           height_offset=-8.564,
                                           phi_offset=0.853 - 0.702,
                                           psi_offset=-0.0,
                                           valve=4)

    D2O = [100, 0, 0, 0]
    H2O = [0, 100, 0, 0]
    SMW = [38, 62, 0, 0]

    DryRun.dry_run = dry_run
    samp = sample_1
    samp.subtitle = "D2O vesicle rinsing"
    run_angle(samp, 0.7, count_uamps=10)
    run_angle(samp, 2.3, 30)
    contrast_change(samp, SMW, flow=1.0, volume=15, wait=True)

    # samp=sample_1
    # samp.subtitle="SMW"
    # run_angle_new_edit(samp,0.7,20)
    # run_angle_new_edit(samp,2.3,30)
    # contrast_change(samp.valve,H2O,flow=2.0,volume=15)

    # for samp in [sample_2, sample_3, sample_4]:
    # samp.subtitle="D2O"
    # run_angle_new_edit(samp,0.7,10)
    # run_angle_new_edit(samp,2.3,30)
    # contrast_change(samp.valve,H2O,flow=2.0,volume=15)

    for samp in [sample_1, sample_3, sample_4]:
        samp.subtitle="H2O"
        run_angle(samp,0.7,10)
        run_angle(samp,2.3,30)
        contrast_change(samp, D2O, flow=1.0, volume=15)

    # transmission(sample_3,"Si3-unmarked", at_angle=0.7, count_uamps=20, hgaps={'S1HG': 10, 'S2HG': 6})
    # transmission(sample_3,"Si3-unmarked", at_angle=0.7, count_uamps=20, hgaps={'S1HG': 50, 'S2HG': 30})

    print("\n=== Total time: ", str(int(DryRun.run_time / 60))+"h " + str(int(DryRun.run_time % 60)) + "min ===")

runscript(dry_run=True)