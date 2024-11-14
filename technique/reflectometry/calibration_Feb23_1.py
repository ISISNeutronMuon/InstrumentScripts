### This script was generated on 15/02/2022, at 16:55:10
### with ScriptMaker (c) Maximilian Skoda 2020 
### Enjoy and use at your own risk. 
import sys
import os

from technique.reflectometry import SampleGenerator

from six.moves import input
from technique.reflectometry import *

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from technique.reflectometry.mocks import g
# from technique.reflectometry import SampleGenerator

sys.path.insert(0, os.path.abspath(os.path.join(r"C:\\", "Instrument", "scripts")))


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

    ASF_50 = sample_generator.new_sample(title="ASF050_01",
                                         translation=588.0,
                                         height_offset=5.652,
                                         phi_offset=0.698 - 0.5,
                                         psi_offset=0.0,
                                         footprint=40,
                                         resolution=0.02,
                                         height2_offset=0)

    sample_2 = sample_generator.new_sample(title="Si block",
                                           translation=225,
                                           height_offset=8.80,
                                           phi_offset=0.806 - 0.697,
                                           psi_offset=0.0,
                                           footprint=60,
                                           resolution=0.035,
                                           valve=1,
                                           height2_offset=0)

    sapphire = sample_generator.new_sample(title="Sapphire",
                                           translation=503,
                                           height_offset=-5.648,
                                           phi_offset=0.619 - 0.5,
                                           psi_offset=0,
                                           footprint=60,
                                           resolution=0.035,
                                           height2_offset=0.0)

    SS316 = sample_generator.new_sample(title="SS316",
                                        translation=450,
                                        height_offset=-5.313,
                                        phi_offset=0.590 - 0.5,
                                        psi_offset=0,
                                        footprint=60,
                                        resolution=0.035,
                                        height2_offset=0.0)

    # sample_D2O = sample_generator.new_sample(title="D2O",
    # translation = 380,
    # height_offset = -3.626,
    # phi_offset = 0.6 - 0.5,
    # psi_offset = 0,
    # footprint = 60,
    # resolution = 0.055,
    # height2_offset = 0.0)

    D2O = [100, 0, 0, 0]
    H2O = [0, 100, 0, 0]
    SMW = [38, 62, 0, 0]

    # sample_2.subtitle="D2O"
    # run_angle(sample_2,0.7,count_uamps=5, vgaps={'S3VG': 15})
    # run_angle(sample_2,2.3,count_uamps=20, vgaps={'S3VG': 20})
    # contrast_change(sample_2, H2O, flow=2, volume=20)

    # transmission(sample_2, "Si block trans osc_gap=2", count_uamps=20, at_angle=0.5, osc_gap=2)
    # transmission(sample_2, "Si block air trans", count_uamps=20, at_angle=0.5)

    sample_2.subtitle = "85 mg/mL HSA 5mM LaCl3 H2O 7h"
    run_angle(sample_2, 0.7, count_uamps=15, vgaps={'S3VG': 30})
    run_angle(sample_2, 2.3, count_uamps=25, vgaps={'S3VG': 30})

    # ASF_50.subtitle="air"
    # run_angle(ASF_50,0.5,count_uamps=10)
    # run_angle(ASF_50,1.0,count_uamps=20)
    # run_angle(ASF_50,2.3,count_uamps=30)
    #
    # SS316.subtitle="air"
    # run_angle(SS316,0.5,count_uamps=5)
    # run_angle(SS316,1.0,count_uamps=10)
    # run_angle(SS316,2.3,count_uamps=20)

    #
    # sapphire.subtitle="air"
    # run_angle(sapphire,0.5,count_uamps=5)
    # run_angle(sapphire,1.0,count_uamps=10)
    # run_angle(sapphire,2.3,count_uamps=20)
    #
    # transmission(sapphire, "Sapphire air trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5)
    transmission(sapphire, "Sapphire air trans", count_uamps=20, at_angle=1.0)

    # transmission(ASF_50, "ASF_50 air trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5)
    transmission(ASF_50, "ASF_50 air trans", count_uamps=20, at_angle=1.0)

    # sample_2.subtitle="85 mg/mL HSA 5mM LaCl3 H2O 2h"
    # run_angle(sample_2,0.7,count_uamps=15, vgaps={'S3VG': 30})
    # run_angle(sample_2,2.3,count_uamps=25, vgaps={'S3VG': 30})

    ####

    ## Section run off SM:
    ## SS316 at 0.45, 0.75 and 0.9 SM2 angle:
    SS316.subtitle = "air SM=0.75"
    run_angle_SM(SS316, 0.5, count_uamps=10, smangle=0.75)
    run_angle_SM(SS316, 0.8, count_uamps=10, smangle=0.75)
    run_angle_SM(SS316, 1.0, count_uamps=20, smangle=0.75)

    transmission_SM(sapphire, "sapphire air SM trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5, smangle=0.75)
    transmission_SM(sapphire, "sapphire air SM trans", count_uamps=20, at_angle=0.5, smangle=0.75)

    SS316.subtitle = "air SM=0.45"
    run_angle_SM(SS316, 0.5, count_uamps=10, smangle=0.45)
    run_angle_SM(SS316, 0.8, count_uamps=10, smangle=0.45)
    run_angle_SM(SS316, 1.0, count_uamps=20, smangle=0.45)
    run_angle_SM(SS316, 1.4, count_uamps=20, smangle=0.45)

    transmission_SM(sapphire, "sapphire air SM trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5, smangle=0.45)
    transmission_SM(sapphire, "sapphire air SM trans", count_uamps=20, at_angle=0.5, smangle=0.45)

    SS316.subtitle = "air SM=0.9"
    run_angle_SM(SS316, 0.5, count_uamps=10, smangle=0.9)
    run_angle_SM(SS316, 0.8, count_uamps=10, smangle=0.9)
    run_angle_SM(SS316, 1.0, count_uamps=20, smangle=0.9)

    transmission_SM(sapphire, "sapphire air SM trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5, smangle=0.9)
    transmission_SM(sapphire, "sapphire air SM trans", count_uamps=20, at_angle=0.5, smangle=0.9)

    # samples off supermirror@0.75:
    sapphire.subtitle = "air SM=0.75"
    run_angle_SM(sapphire, 0.5, count_uamps=10, smangle=0.75)
    run_angle_SM(sapphire, 0.8, count_uamps=10, smangle=0.75)
    run_angle_SM(sapphire, 1.0, count_uamps=20, smangle=0.75)

    transmission_SM(ASF_50, "ASF_50 air SM trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5, smangle=0.75)
    transmission_SM(ASF_50, "ASF_50 air SM trans", count_uamps=20, at_angle=0.5, smangle=0.75)

    ASF_50.subtitle = "air SM=0.75"
    run_angle_SM(ASF_50, 0.5, count_uamps=10, smangle=0.75)
    run_angle_SM(ASF_50, 0.8, count_uamps=10, smangle=0.75)
    run_angle_SM(ASF_50, 1.0, count_uamps=20, smangle=0.75)

    # samples off supermirror@0.45:
    sapphire.subtitle = "air SM=0.45"
    run_angle_SM(sapphire, 0.5, count_uamps=10, smangle=0.45)
    run_angle_SM(sapphire, 0.8, count_uamps=10, smangle=0.45)
    run_angle_SM(sapphire, 1.0, count_uamps=20, smangle=0.45)

    transmission_SM(ASF_50, "ASF_50 air SM trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5, smangle=0.45)
    transmission_SM(ASF_50, "ASF_50 air SM trans", count_uamps=20, at_angle=0.5, smangle=0.45)

    ASF_50.subtitle = "air SM=0.45"
    run_angle_SM(ASF_50, 0.5, count_uamps=10, smangle=0.45)
    run_angle_SM(ASF_50, 0.8, count_uamps=10, smangle=0.45)
    run_angle_SM(ASF_50, 1.0, count_uamps=20, smangle=0.45)
    run_angle_SM(ASF_50, 1.4, count_uamps=20, smangle=0.45)

    # samples off supermirror@0.9:
    sapphire.subtitle = "air SM=0.9"
    run_angle_SM(sapphire, 0.5, count_uamps=10, smangle=0.9)
    run_angle_SM(sapphire, 0.8, count_uamps=10, smangle=0.9)
    run_angle_SM(sapphire, 1.0, count_uamps=20, smangle=0.9)

    transmission_SM(ASF_50, "ASF_50 air SM trans osc_gap=5", count_uamps=20, at_angle=0.5, osc_gap=5, smangle=0.9)
    transmission_SM(ASF_50, "ASF_50 air SM trans", count_uamps=20, at_angle=0.5, smangle=0.9)

    ASF_50.subtitle = "air SM=0.9"
    run_angle_SM(ASF_50, 0.5, count_uamps=10, smangle=0.9)
    run_angle_SM(ASF_50, 0.8, count_uamps=10, smangle=0.9)
    run_angle_SM(ASF_50, 1.0, count_uamps=20, smangle=0.9)


# with g.sim.Simulate():
runscript(dry_run=True)
