from math import tan, radians, sin

from genie_python import genie as g

def SampleGenerator():
    pass

class Sample():
    def __init__(self, title, subtitle, translation, coarse_nomirror, phi_offset, psi, height, resolution, footprint):
        """

        Args:
            translation: The translation for the sample
            coarse_nomirror: Height of the second stage with no mirror relative to the beam for this sample
            phi_offset: offset from 0 for the sample in the phi direction
            resolution: resolution for this sample
        """
        self.subtitle = subtitle
        self.title = title
        self.footprint = footprint
        self.resolution = resolution
        self.height = height
        self.psi = psi
        self.phi_offset = phi_offset
        self.translation = translation
        self.coarse_nomirror = coarse_nomirror


class InstrumentConstant(object):
    def __init__(self, s1s2, s2sa, maxTheta, s4max, SM_sa, s3max=None):

        self.s1s2 = s1s2
        self.s2sa = s2sa
        self.maxTheta = maxTheta
        self.s4max = s4max
        self.SM_sa = SM_sa
        if s3max is None:
            self.s3max = s3max
        else:
            self.s3max = s3max


INSTRUMENT_CONSTANTS = {
    "INTER": InstrumentConstant(
                s1s2 = 1940.5,
                s2sa = 364.0,
                maxTheta = 2.3, # usual maximum angle
                s4max = 10.0, # max s4_vg at maxTheta
                SM_sa = 1375.0),
    "SURF": InstrumentConstant(
                s1s2 = 1448.0,
                s2sa = 389.0,
                maxTheta = 1.8, # usual maximum angle
                s4max = 10.0, # max s4vg at maxTheta
                SM_sa = 1088.26),
    "CRISP": InstrumentConstant(
                s1s2 = 2596.0,
                s2sa = 343.0,
                maxTheta = 2, # usual maximum angle
                s4max = 20.0, # max s4vg at maxTheta
                SM_sa = 2311),
    "DEFAULT": InstrumentConstant(
                s1s2 = 1940.5,
                s2sa = 364.0,
                maxTheta = 2.3, # usual maximum angle
                s4max = 10.0, # max s4_vg at maxTheta
                SM_sa = 1385.0)
}


def run_angle(sample, angle, how_long, s1_vg=None, s2_vg=None, s3_vg=None, s4_vg=None, setup=False, mode=None, howlong_is_time=False, auto_height=False, dry_run=False):
    """
    Do a run with a given theta
    Args:
        sample (Sample): sample
        angle:
        how_long:
        s1_vg:
        s2_vg:
        s3_vg:
        s4_vg:
        setup:
        mode:
        howlong_is_time:
        auto_height:
        dry_run:

    Returns:

    """

    instrument = g.get_instrument()
    try:
        constants = INSTRUMENT_CONSTANTS[instrument]
    except KeyError:
        print("Instrument, '', not found in constants list using default")
        constants = INSTRUMENT_CONSTANTS["DEFAULT"]

    # Move this first before the heights as this can cause some drift.

    print("Translation to {}".format(sample.translation))
    if not dry_run:
        g.cset("TRANSLATION", sample.translation)
        g.waitfor_move()

    print("Change to mode: {}".format(mode))
    if not dry_run:
        if mode is not None:
            g.cset("MODE", mode)
        sm_angle=(2.3-angle)/2
        if sm_angle > 0.001:
            g.cset("SM_in", "IN")
            g.cset("smangle", sm_angle)
        else:
            g.cset("SM_in", "OUT")

        g.cset("height2_offset", sample.coarse_nomirror)
        g.cset("phi", angle + sample.phi_offset)
        g.cset("psi", sample.psi)

    g.cset("theta", angle)

    if not auto_height:
        g.cset("height", sample.height)

    _set_slit_gaps(angle, constants, s1_vg, s2_vg, s3_vg, s4_vg, sample)

    g.waitfor_move()

    title = "{} {} th={}".format(sample.title, sample.subtitle, angle)
    g.change_title(title)

    # count
    if not setup:
        if auto_height:
            auto_height()
        if howlong_is_time:
            g.waitfor_time(seconds=how_long)
        else:
            g.waitfor_uamps(how_long)


def _set_slit_gaps(theta, constants, s1_vg, s2_vg, s3_vg, s4_vg, sample, dry_run):
    """
    Set the slit gaps either to user settings or calculated based on foot print and max slit size
    Args:
        theta: angle theta is set to
        constants: machine constants
        s1_vg: s1 vertical gap set by user; None use footprint calculated gap
        s2_vg: s2 vertical gap set by user; None use footprint calculated gap
        s3_vg: s3 vertical gap set by user; None use percentage of maximum
        s4_vg: s4 vertical gap set by user; None use percentage of maximum
        sample: sample parameters
        dry_run: True don't do anything just print; False print and go to

    Returns:

    """
    s1sa = constants.s1s2 + constants.s2sa
    footprint_at_theta = sample.footprint * sin(radians(theta))
    s1 = 2 * s1sa * tan(radians(sample.resolution * theta)) - footprint_at_theta
    s2 = constants.s1s2 * (footprint_at_theta + s1) / s1sa - s1

    factor = theta / constants.maxTheta
    s3 = constants.s3max * factor
    s4 = constants.s4max * factor

    if s1_vg is not None:
        s1 = s1_vg

    if s2_vg is not None:
        s2 = s2_vg

    if s3_vg is not None:
        s3 = s3_vg

    if s4_vg is None:
        s4 = s4_vg

    print("Slits 1-4 set to: {}, {}, {}, {}".format(s1, s2, s3, s4))
    if not dry_run:
        g.cset("S1VG", s1)
        g.cset("S2VG", s2)
        g.cset("S3VG", s3)
        g.cset("S4VG", s4)
