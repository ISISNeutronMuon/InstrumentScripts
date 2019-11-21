"""
Base routine for reflectometry techniques
"""
from collections import OrderedDict
from contextlib import contextmanager
from math import tan, radians, sin

from six.moves import input
from genie_python import genie as g

from technique.reflectometry.instrument_constants import get_instrument_constants


def run_angle(sample, angle, count_uamps=None, count_seconds=None, count_frames=None, s1vg=None, s2vg=None, s3vg=None,
              s4vg=None, smangle=None, mode=None, auto_height=False, dry_run=False):
    """
    Move to a given theta with slits set. If a current or time are given then take a measurement otherwise just go to
    the position.

    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        angle: The angle to measure at
        count_uamps: the current to run the measurement for; None for use other count
            (if all counts are none then don't count)
        count_seconds: the time to run the measurement for if uamps not set; None for use other count
            (if all counts are none then don't count)
        count_frames: the number of frames to wait for; None for use other count
            (if all counts are none then don't count)
        s1vg: slit 1 vertical gap; None to use sample footprint and resolution
        s2vg: slit 2 vertical gap; None to use sample footprint and resolution
        s3vg: slit 3 vertical gap; None use fraction of maximum based on theta
        s4vg: slit 4 vertical gap; None use fraction of maximum based on theta
        smangle: the super mirror angle if set sm get put in; None don't move the super mirror unless the mode has
            changed
        mode: mode to run in; None don't change modes (means super mirror is not moved in or out for instance)
        auto_height: if True when taking data run the auto-height routine (default False)
        dry_run: True just print what is going to happend; False do the movement
    """

    print("** Run angle {} **".format(sample.title))

    movement = _Movement(dry_run)

    movement._dry_run_warning()
    constants = get_instrument_constants()
    movement._set_translation(sample.translation)  # Move this first before the heights as this can cause some drift.
    mode = movement._change_to_mode(mode)

    print("Mode {}".format(mode))

    if mode == "LIQUID":
        # Not being used on Crisp come back to this if loop
        movement._set_smangle_if_not_none(angle)
    elif mode == "Polarised NR":
        movement._set_smangle_if_not_none(smangle)
        movement._set_phi_psi(1.5 + sample.phi_offset, 0 + sample.psi_offset)
        #TODO: 1.5 should be user defined this is not right for polerised nr it should be in in liqud?
    else:
        # assume angle sample can be set
        movement._set_phi_psi(angle + sample.phi_offset, 0 + sample.psi_offset)
        movement._set_smangle_if_not_none(smangle)

    movement._set_height2_offset(sample.height2_offset, constants)
    movement._set_theta(angle)

    if not auto_height:
        movement._set_height_offset(sample.height)

    movement._set_slit_gaps(angle, constants, s1vg, s2vg, s3vg, s4vg, sample)
    movement._wait_for_move()
    movement._update_title("{} {} th={}".format(sample.title, sample.subtitle, angle))

    # count
    if count_seconds is None and count_uamps is None and count_frames is None:
        print("Setup only no measurement")
    else:
        if auto_height:
            auto_height()
        if count_uamps is not None:
            movement._count_for_uamps(count_uamps)
        elif count_seconds is not None:
            movement._count_for_time(count_seconds)
        elif count_frames is not None:
            movement._count_for_frames(count_frames)


def transmission(sample, title, s1vg, s2vg, count_seconds=None, count_uamps=None, count_frames=None, s1hg=None,
                 s2hg=None, s3hg=None, s4hg=None,
                 height_offset=None, smangle=None, mode=None, dry_run=False):
    """
    Perform a transmission
    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        title: Title to set
        count_seconds: time to count for in seconds
        count_uamps: number of micro amps to count for
        count_frames: number of frames to count for
        s1vg: slit 1 vertical gap
        s2vg: slit 2 vertical gap
        s1hg: slit 1 horizontal gap; None to leave unchanged
        s2hg: slit 2 horizontal gap; None to leave unchanged
        s3hg: slit 3 horizontal gap; None to leave unchanged
        s4hg: slit 4 horizontal gap; None to leave unchanged
        height_offset: Height offset from normal to set the sample to
        smangle: super mirror angle; None for don't use a super mirror
        mode: mode to run in; None don't change mode
        dry_run: True to print what happens; False to do experiment
    """

    print("** Transmission {} **".format(title))

    movement = _Movement(dry_run)

    movement._dry_run_warning()
    constants = get_instrument_constants()
    movement._change_to_1_period()

    movement._set_translation(sample.translation)  # Move this first before the heights as this can cause some drift.

    with reset_hgaps(dry_run):
        movement._change_to_mode(mode)

        movement._set_smangle_if_not_none(smangle)

        movement._set_height2_offset(sample.height2_offset, constants)
        movement._set_theta(0.0)

        if smangle is not None:
            subtitle = "SM={}, ".format(smangle)
        else:
            subtitle = ""

        if height_offset is None:
            movement._set_height_offset(sample.height - 5)
        elif height_offset < 10:  # if the height offset is less than can be achieved by the fine z use this
            movement._set_height_offset(sample.height - height_offset)
        else:
            movement._set_height2_offset(sample.height2_offset - height_offset, constants)

        movement._set_h_gaps(s1hg, s2hg, s3hg, s4hg)
        movement._set_slit_gaps(0.0, constants, s1vg, s2vg, constants.s3max, constants.s4max, sample)
        movement._wait_for_move()
        horizontal_gaps = [g.cget("s{}hg".format(num))["value"] for num in [1, 2, 3, 4]]

        title = "{} transmission {} VGs ({} {}) HGs ({} {} {} {})".format(title, subtitle, s1vg, s2vg, *horizontal_gaps)
        movement._update_title(title)
        if count_uamps is not None:
            movement._count_for_uamps(count_uamps)
        elif count_seconds is not None:
            movement._count_for_time(count_seconds)
        elif count_frames is not None:
            movement._count_for_frames(count_frames)

        movement._set_height_offset(sample.height)
        movement._set_height2_offset(sample.height2_offset, constants)
        # Horizontal gaps reset by with reset_gaps


@contextmanager
def reset_hgaps(dry_run=False):
    """
    After the context is over reset the gaps back to the value before. If keyboard interupt give options for what to do.
    Args:
        dry_run: True print what will happen; False do reset

    """
    horizontal_gaps = OrderedDict()
    for gap_name in ("S1HG", "S2HG", "S3HG", "S4HG"):
        horizontal_gaps[gap_name] = g.cget(gap_name)["value"]

    def _reset_gaps():
        print("Reset horizontal gaps to {}".format(horizontal_gaps.items()))
        if not dry_run:
            for gap_name, gap_size in horizontal_gaps.items():
                g.cset(gap_name, gap_size)
            g.waitfor_move()

    try:
        yield
        _reset_gaps()
    except KeyboardInterrupt:
        if not dry_run:
            print("Not dry run pause")
            g.pause()
        while True:
            choice = input("ctrl-c hit do you wish to (A)bort or (E)nd or (K)eep Counting?")
            if choice is not None and choice.upper() in ["A", "E", "K"]:
                break
            print("Invalid choice try again!")

        if choice.upper() == "A":
            if not dry_run:
                g.abort()
            print("Setting horizontal slit gaps to pre-tranmission values.")
            _reset_gaps()

        elif choice.upper() == "E":
            if not dry_run:
                g.end()
            _reset_gaps()
        elif choice.upper() == "K":
            print("Continuing counting, remember to set back horizontal slit gaps when the run is ended.")
            g.resume()

        if not dry_run:
            g.waitfor_time(seconds=5)


def slit_check(theta, footprint, resolution):
    """
    Check the slits values
    Args:
        theta: theta
        footprint: desired footprint
        resolution:  desired resolution

    """
    constants = get_instrument_constants()
    movement = _Movement(True)
    s1, s2 = movement._calculate_slit_gaps(theta, footprint, resolution, constants)
    print("For a foortprint of {} and resolution of {} at an angle {}:".format(theta, footprint, resolution))
    print("s1vg={}".format(s1))
    print("s2vg={}".format(s2))


class _Movement(object):
    """
    Encapsulate instrument changes
    """

    def __init__(self, dry_run):
        self.dry_run = dry_run

    def _change_to_mode(self, mode):
        if mode is not None:
            print("Change to mode: {}".format(mode))
            if not self.dry_run:
                g.cset("MODE", mode)
        else:
            mode = g.cget("MODE")["value"]
        return mode

    def _dry_run_warning(self):
        if self.dry_run:
            print("Nothing will change this is a DRY RUN!!!")

    def _set_theta(self, theta):
        print("Theta set to: {}".format(theta))
        if not self.dry_run:
            g.cset("theta", theta)

    def _update_title(self, title):
        if self.dry_run:
            print("New Title: {}".format(title))
        else:
            g.change_title(title)

    def _set_height_offset(self, height):
        print("Sample: height offset from beam={}".format(height))
        if not self.dry_run:
            g.cset("SAMPLEOFFSET", height)

    def _set_height2_offset(self, height, constants):
        if constants.has_height2:
            print("Sample: height2 offset from beam={}".format(height))
            if not self.dry_run:
                g.cset("HEIGHT2_OFFSET", height)
        elif height != 0:
            print("ERROR: Height 2 off set is being ignored")

    def _set_translation(self, translation):
        print("Translation to {}".format(translation))
        if not self.dry_run:
            g.cset("TRANS", translation)
            g.waitfor_move()

    def _set_slit_gaps(self, theta, constants, s1vg, s2vg, s3vg, s4vg, sample):
        """
        Set the slit gaps either to user settings or calculated based on foot print and max slit size
        Args:
            theta: angle theta is set to
            constants: machine constants
            s1vg: s1 vertical gap set by user; None use footprint calculated gap
            s2vg: s2 vertical gap set by user; None use footprint calculated gap
            s3vg: s3 vertical gap set by user; None use percentage of maximum
            s4vg: s4 vertical gap set by user; None use percentage of maximum
            sample: sample parameters
        """
        s1, s2 = self._calculate_slit_gaps(theta, sample.footprint, sample.resolution, constants)

        factor = theta / constants.maxTheta
        s3 = constants.s3max * factor
        s4 = constants.s4max * factor

        if s1vg is not None:
            s1 = s1vg

        if s2vg is not None:
            s2 = s2vg

        if s3vg is not None:
            s3 = s3vg

        if s4vg is not None:
            s4 = s4vg

        print("Slit gaps 1-4 set to: {}, {}, {}, {}".format(s1, s2, s3, s4))
        if not self.dry_run:
            g.cset("S1VG", s1)
            g.cset("S2VG", s2)
            g.cset("S3VG", s3)
            g.cset("S4VG", s4)

    def _calculate_slit_gaps(self, theta, footprint, resolution, constants):
        s1sa = constants.s1s2 + constants.s2sa
        footprint_at_theta = footprint * sin(radians(theta))
        s1 = 2 * s1sa * tan(radians(resolution * theta)) - footprint_at_theta
        s2 = (constants.s1s2 * (footprint_at_theta + s1) / s1sa) - s1
        return s1, s2

    def _set_h_gaps(self, s1hg, s2hg, s3hg, s4hg):
        print("Setting hgaps to {} (None's are not changed)".format([s1hg, s2hg, s3hg, s4hg]))
        if not self.dry_run:
            if s1hg is not None:
                g.cset("S1HG", s1hg)
            if s2hg is not None:
                g.cset("S2HG", s2hg)
            if s3hg is not None:
                g.cset("S3HG", s3hg)
            if s4hg is not None:
                g.cset("S4HG", s4hg)

    def _change_to_1_period(self):
        if not self.dry_run:
            g.change_period(1)

    def _count_for_time(self, seconds):
        print("Measure for {} s".format(seconds))
        if not self.dry_run:
            g.begin()
            g.waitfor_time(seconds=seconds)
            g.end()

    def _count_for_uamps(self, count_uamps):
        print("Wait for {} uA".format(count_uamps))
        if not self.dry_run:
            g.begin()
            g.waitfor_uamps(count_uamps)
            g.end()

    def _count_for_frames(self, count_frames):
        print("Wait for {} frames count (i.e. count this number of frames from the current frame)".format(count_frames))
        if not self.dry_run:
            final_frame = count_frames + g.get_frames()
            g.begin()
            g.waitfor_frames(final_frame)
            g.end()

    def _set_phi_psi(self, phi, psi):
        print("Sample: Phi={}, Psi={}".format(phi, psi))
        if not self.dry_run:
            g.cset("PHI", phi)
            g.cset("PSI", psi)

    def _wait_for_move(self):
        if not self.dry_run:
            g.waitfor_move()

    def _set_smangle_if_not_none(self, smangle):
        if smangle is not None:
            print("SM angle: {}".format(smangle))
            if not self.dry_run:
                g.cset("SMANGLE", smangle)
                g.cset("SMINBEAM", "IN")
