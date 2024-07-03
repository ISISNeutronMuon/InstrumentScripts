### This script was generated on 15/02/2022, at 16:55:10
### with ScriptMaker (c) Maximilian Skoda 2020 
### Enjoy and use at your own risk. 

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
    format="%(asctime)s | %(levelname)s | %(message)s",  # %(name)s -
    datefmt="%Y-%m-%d %H:%M:%S",
)

max_per = 19


def runscript(dry_run=False):
    sample_generator = SampleGenerator(
        translation=400.0,
        height2_offset=0.0,
        phi_offset=0.0,
        psi_offset=0.0,
        height_offset=0.0,
        resolution=0.035,
        sample_length=60,
        valve=1,
        footprint=60,
        hgaps={'S1HG': 50.0, 'S2HG': 30, 'S3HG': 80})

    sample_1 = sample_generator.new_sample(title="S1 Repeat Nat-Dcyt-HPer",
                                           translation=225,
                                           height_offset=7.285,
                                           phi_offset=0.867 - 0.7,
                                           psi_offset=-0.410,
                                           valve=1)

    sample_2 = sample_generator.new_sample(title="S2 EAE-Dcyt-HPer",
                                           translation=375,
                                           height_offset=6.719,
                                           phi_offset=0.699 - 0.7,
                                           psi_offset=-0.279,
                                           valve=2)

    sample_3 = sample_generator.new_sample(title="S3 Nat-HCyt-DPer",
                                           translation=525,
                                           height_offset=7.447,
                                           phi_offset=0.779 - 0.7,
                                           psi_offset=-0.479,
                                           valve=3)

    sample_4 = sample_generator.new_sample(title="S4",
                                           translation=675,
                                           height_offset=8.62,
                                           phi_offset=0.736 - 0.7,
                                           psi_offset=-0.1,
                                           valve=4)

    DryRun.dry_run = dry_run

    D2O = [100, 0, 0, 0]
    FourMW = [71, 29, 0, 0]
    SiMW = [38, 62, 0, 0]
    H2O = [0, 100, 0, 0]

    transmission(sample_1, "S1 Si osc_gap=5", count_uamps=20, at_angle=0.7, osc_gap=5)
    transmission(sample_1, "S1 Si", count_uamps=20, at_angle=0.7)
    #

    temperatures_to_measure = [38]

    for temp in temperatures_to_measure:
        # g.cset('Julabo01_T_SP', temp)
        # inject(sample_3, D2O, flow=1.5, volume=18, wait=True)

        sample_3.subtitle = f"{temp}C D2O"
        run_angle(sample_3, 0.7, 10, vgaps={"S2VG": 2.0, "S3VG": 3.0})
        run_angle(sample_3, 2.3, 25)

        inject(sample_3, H2O, flow=1.5, volume=18, wait=True)

        sample_3.subtitle = f"{temp}C H2O"
        run_angle(sample_3, 0.7, 10)
        run_angle(sample_3, 2.3, 25)

        inject(sample_3, D2O, flow=1.5, volume=18, wait=True)

    # === Protein injections ===

    inject(sample_2, "SYRINGE_1", flow=1, volume=7, wait=True)
    sample_2.subtitle = '10C + MPB incubation D2O'
    run_angle(sample_2, 0.7, count_seconds=900)
    inject(sample_2, D2O, flow=1, volume=18, wait=True)

    inject(sample_3, "SYRINGE_1", flow=1, volume=7, wait=True)
    sample_3.subtitle = '38C + MPB incubation D2O'
    run_angle(sample_3, 0.7, count_seconds=900)
    inject(sample_3, D2O, flow=1, volume=18, wait=False)

    # === D2O Measurements ===
    sample_1.subtitle = '10C D2O'
    run_angle(sample_1, 0.7, 7)
    run_angle(sample_1, 2.3, 20)
    inject(sample_1, FourMW, flow=1, volume=18, wait=False)

    sample_3.subtitle = '38C + MPB Flush D2O'
    run_angle(sample_3, 0.7, 7)
    run_angle(sample_3, 2.3, 20)
    inject(sample_3, FourMW, flow=1, volume=18, wait=False)

    # === 4MW Measurements ===
    sample_1.subtitle = '10C 4MW'
    run_angle(sample_1, 0.7, 7)
    run_angle(sample_1, 2.3, 20)
    inject(sample_1, SiMW, flow=1, volume=18, wait=False)

    sample_3.subtitle = '38C + MPB Flush 4MW'
    run_angle(sample_3, 0.7, 7)
    run_angle(sample_3, 2.3, 20)
    inject(sample_3, SiMW, flow=1, volume=18, wait=False)

    # === SiMW Measurements ===
    sample_1.subtitle = '10C SiMW'
    run_angle(sample_1, 0.7, 15)
    run_angle(sample_1, 2.3, 25)
    inject(sample_1, H2O, flow=1, volume=18, wait=False)

    sample_3.subtitle = '38C + MPB Flush SiMW'
    run_angle(sample_3, 0.7, 15)
    run_angle(sample_3, 2.3, 25)
    inject(sample_3, H2O, flow=1, volume=18, wait=False)

    # === H2O Measurements ===
    sample_1.subtitle = '10C H2O'
    run_angle(sample_1, 0.7, 10)
    run_angle(sample_1, 2.3, 25)
    inject(sample_1, D2O, flow=1, volume=18, wait=False)

    sample_3.subtitle = '38C + MPB Flush H2O'
    run_angle(sample_3, 0.7, 10)
    run_angle(sample_3, 2.3, 25)
    inject(sample_3, D2O, flow=1, volume=18, wait=False)

    # === Protein injections ===

    inject(sample_1, "SYRINGE_1", flow=1, volume=7, wait=True)
    sample_1.subtitle = '10C + MPB incubation D2O'
    run_angle(sample_1, 0.7, count_seconds=900)
    inject(sample_1, D2O, flow=1, volume=18, wait=True)

    # === D2O Measurements ===
    sample_1.subtitle = '10C + MPB Flush D2O'
    run_angle(sample_1, 0.7, 7)
    run_angle(sample_1, 2.3, 20)
    inject(sample_1, FourMW, flow=1, volume=18, wait=False)

    sample_2.subtitle = '10C + MPB Flush D2O'
    run_angle(sample_2, 0.7, 7)
    run_angle(sample_2, 2.3, 20)
    inject(sample_2, FourMW, flow=1, volume=18, wait=False)

    # === 4MW Measurements ===
    sample_1.subtitle = '10C + MPB Flush 4MW'
    run_angle(sample_1, 0.7, 7)
    run_angle(sample_1, 2.3, 20)
    inject(sample_1, SiMW, flow=1, volume=18, wait=False)

    sample_2.subtitle = '10C + MPB Flush 4MW'
    run_angle(sample_2, 0.7, 7)
    run_angle(sample_2, 2.3, 20)
    inject(sample_2, SiMW, flow=1, volume=18, wait=False)

    # === SiMW Measurements ===
    sample_1.subtitle = '10C + MPB Flush SiMW'
    run_angle(sample_1, 0.7, 15)
    run_angle(sample_1, 2.3, 25)
    inject(sample_1, H2O, flow=1, volume=18, wait=False)

    sample_2.subtitle = '10C + MPB Flush SiMW'
    run_angle(sample_2, 0.7, 15)
    run_angle(sample_2, 2.3, 25)
    inject(sample_2, H2O, flow=1, volume=18, wait=False)

    # === H2O Measurements ===
    sample_1.subtitle = '10C + MPB Flush H2O'
    run_angle(sample_1, 0.7, 15)
    run_angle(sample_1, 2.3, 25)
    inject(sample_1, D2O, flow=1, volume=18, wait=False)

    sample_2.subtitle = '10C + MPB Flush H2O'
    run_angle(sample_2, 0.7, 15, vgaps={"S2VG": 2.0, "S3VG": 3.0})
    run_angle(sample_2, 2.3, 25)
    inject(sample_2, D2O, flow=1, volume=18, wait=False)

    # KEEP THIS:
    if dry_run:
        run_summary()
        # return DryRun.run_time


runscript(dry_run=True)

ans = input("Script will run for " +
            str(int(DryRun.run_time / 60)) + "h " + str(int(DryRun.run_time % 60)) + "min ===\nContinue ([y]/n)?")

if ans == 'y' or ans == "":
    runscript()

#
