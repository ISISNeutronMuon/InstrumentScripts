import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(r"C:\\", "Instrument", "scripts")))

from genie_python import genie as g
from techniques.reflectometry import SampleGenerator, run_angle, contrast_change, transmission


def runscript(dry_run=False):
    """
    Run my script
    :param dry_run: True just print what would happen; False do it
    """

    if not dry_run:
        g.change_period(1)
        g.cset("monitor", 1)

    # Set up defaults for all samples
    sample_generator = SampleGenerator(

        translation=100,
        height2_offset=0,
        phi_offset=0,
        psi_offset=0,
        height_offset=1.0,
        resolution=0.03,
        footprint=60)

    # Set up all the samples
    samples = [
        sample_generator.new_sample(
            title="S1 dDPPCS",
            height_offset=-0.005,
            phi_offset=0.400-0.299,  # aligned phi - aligned theta
            psi_offset=-0.06,
            translation=100.0),
        sample_generator.new_sample(
            title="S2 dDPPC",
            height_offset=-0.155,
            phi_offset=0.391-0.3,  # aligned phi - aligned theta
            psi_offset=0.121,
            translation=50.5),
        sample_generator.new_sample(
            title="S3 dDPPC",
            height_offset=-0.320,
            phi_offset=0.447-0.299,  # aligned phi - aligned theta
            psi_offset=-0.067,
            translation=353.0),
        sample_generator.new_sample(
            title="S4 dDPPC",
            height_offset=-0.305,
            phi_offset=0.453-0.299,  # aligned phi - aligned theta
            psi_offset=-0.061,
            translation=20.0)
    ]

    # ====================================
    # Script body begins here:
    # ====================================

    # HPLC lines:
    #  A=D2O CaCl; B=H2O CaCl; C=; D=

    HDO_concentrations = [50, 50, 0, 0]
    H20_concentrations = [0, 100, 0, 0]

    # ---D2O contrasts:-----
    standard_angles("D2O", samples[0], dry_run=dry_run)
    contrast_change(1, HDO_concentrations, 1.5, 30, dry_run=dry_run)

    transmission(samples[1], "Sapp", 40, 0.410, 0.2, 40, 30, dry_run=dry_run)
    transmission(samples[1], "Sapp", 20, 1.366, 0.666, 5, 3.75, dry_run=dry_run)
    transmission(samples[1], "Sapp", 20, 1.366, 0.666, 40, 30, dry_run=dry_run)

    standard_angles("D2O", samples[1], dry_run=dry_run)
    contrast_change(2, HDO_concentrations, 1.5, 30, dry_run=dry_run)

    standard_angles("D2O", samples[2], dry_run=dry_run)
    contrast_change(4, [100, 0, 0, 0], 1.5, 5, wait=True, dry_run=dry_run)
    contrast_change(3, HDO_concentrations, 1.5, 30, dry_run=dry_run)

    standard_angles("D2O", samples[3], dry_run=dry_run)
    contrast_change(4, HDO_concentrations, 1.5, 30, dry_run=dry_run)

    # HDO contrasts:
    measure_and_change(samples, "HDO", H20_concentrations, dry_run=dry_run)

    # H2O contrasts:
    measure_and_change(samples, "H2O", None, dry_run=dry_run)


def standard_angles(subtitle, sample, dry_run=False):
    """
    Measure the standard angles for a sample

    Args:
        subtitle: subtitle to use
        sample: sample to measure
        dry_run: True to print changes; False perform changes
    """
    sample.subtitle = subtitle
    run_angle(sample, 0.3, 10, s3vg=5, s4vg=5, mode="NR", dry_run=dry_run)
    run_angle(sample, 1.0, 15, mode="NR", dry_run=dry_run)
    run_angle(sample, 2.3, 35, mode="NR", dry_run=dry_run)


def measure_and_change(samples, subtitle, concern_to_set_after, dry_run=False):
    """
    Measure all samples over all angles and alter the concentration after measurement is finished
    :param samples: the samples to measure
    :param subtitle: subtitle for measurement
    :param concern_to_set_after: concentrations to set; None don't alter
    :param dry_run: True just print what is going on; False do the movement

    """
    for sample_index in range(4):
        standard_angles(subtitle, samples[sample_index], dry_run=dry_run)
        if concern_to_set_after is not None:
            contrast_change(sample_index + 1, concern_to_set_after, 1.5, 30, dry_run=dry_run)
