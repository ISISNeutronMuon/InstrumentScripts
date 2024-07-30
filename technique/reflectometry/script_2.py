# ## This script was generated on 15/02/2022, at 16:55:10
# ## with ScriptMaker (c) Maximilian Skoda 2020 
# ## Enjoy and use at your own risk.
import time

from technique.reflectometry import *  # __all__ defined in __init__.py
import logging
import sys
import os

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from technique.reflectometry.mocks import g

# Remove all handlers associated with the root logger object.
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Set up new logger
logging.basicConfig(
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("example.log", mode="w"),
    ],
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",     # %(name)s -
    datefmt="%Y-%m-%d %H:%M:%S",
)


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

    # time.sleep(30)

    for samp in [sample_1, sample_3, sample_4]:
        samp.subtitle = "H2O"
        run_angle(samp, 0.7, count_seconds=300)
        run_angle(samp, 2.3, 30)
        contrast_change(samp, D2O, flow=1.0, volume=15)

    transmission(sample_3, "Si3-unmarked", at_angle=0.7, count_uamps=20, hgaps={'S1HG': 10, 'S2HG': 6})
    transmission(sample_3, "Si3-unmarked", at_angle=0.7, count_uamps=20, hgaps={'S1HG': 50, 'S2HG': 30})

    go_to_pressure(28, speed=30)

    inject(sample_4, D2O, flow=2.0, volume=20)

    if dry_run:
        print("\n=== Total time: ", str(int(DryRun.run_time / 60)) + "h " + str(int(DryRun.run_time % 60)) + "min ===")
        return DryRun.run_time


runtime = runscript(dry_run=True)

ans = input("Script will run for " +
            str(int(DryRun.run_time / 60)) + "h " + str(int(DryRun.run_time % 60)) + "min ===\nContinue ([y]/n)?")

if ans == 'y' or ans == "":
    runscript()
