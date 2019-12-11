"""
Base routine for reflectometry techniques
"""
import sys
from collections import OrderedDict
from contextlib import contextmanager
from math import tan, radians, sin

from six.moves import input
from genie_python import genie as g

from technique.reflectometry.instrument_constants import get_instrument_constants


def run_angle(sample, angle, count_uamps=None, count_seconds=None, count_frames=None, s1vg=None, s2vg=None, s3vg=None,
              s4vg=None, smangle=None, mode=None, auto_height=False, dry_run=False):
    """
    Move to a given theta and smangle with slits set. If a current, time or frame count are given then take a
    measurement.

    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        angle: The angle to measure at, theta and in liquid mode also the sm angle
        count_uamps: the current to run the measurement for; None for use count_seconds
        count_seconds: the time to run the measurement for if uamps not set; None for use count_frames
        count_frames: the number of frames to wait for; None for don't count
        s1vg: slit 1 vertical gap; None to use sample footprint and resolution
        s2vg: slit 2 vertical gap; None to use sample footprint and resolution
        s3vg: slit 3 vertical gap; None use fraction of maximum based on theta
        s4vg: slit 4 vertical gap; None use fraction of maximum based on theta
        smangle: super mirror angle, place in the beam, if set to 0 remove from the beam; None don't move super mirror
        mode: mode to run in; None don't change modes
        auto_height: if True when taking data run the auto-height routine
        dry_run: True just print what is going to happen; False do the experiment

    """

    print("** Run angle {} **".format(sample.title))

    movement = _Movement(dry_run)

    movement.dry_run_warning()
    constants = get_instrument_constants()
    movement.change_to_soft_period_count()
    movement.set_translation(sample.translation)  # Move this first before the heights as this can cause some drift.
    mode = movement.change_to_mode_if_not_none(mode)

    print("Mode {}".format(mode))

    if mode == "LIQUID":
        # In liquid the sample is tilted by the incoming beam angle so that it is level, this is accounted for by
        # adjusting the super mirror
        smangle = (constants.incoming_beam_angle - angle)/2
        movement.set_smangle_if_not_none(smangle)
    else:
        # assume angle sample can be set, if there is a sm angle then set the sample to include this bounce
        movement.set_smangle_if_not_none(smangle)
        sm_reflection = smangle * 2.0 if smangle is not None else 0
        movement.set_phi_psi(sm_reflection + angle + sample.phi_offset, 0 + sample.psi_offset)

    movement.set_height2_offset(sample.height2_offset, constants)
    movement.set_theta(angle)

    if not auto_height:
        movement.set_height_offset(sample.height)

    movement.set_slit_gaps(angle, constants, s1vg, s2vg, s3vg, s4vg, sample)
    movement.wait_for_move()
    movement.update_title(sample.title, sample.subtitle, angle, smangle, add_current_gaps=True)

    # count
    if count_seconds is None and count_uamps is None and count_frames is None:
        print("Setup only no measurement")
    else:
        if auto_height:
            auto_height()
        movement.count_for(count_uamps, count_seconds, count_frames)


def transmission(sample, title, s1vg, s2vg, s3vg=None, s4vg=None,
                 count_seconds=None, count_uamps=None, count_frames=None,
                 s1hg=None, s2hg=None, s3hg=None, s4hg=None,
                 height_offset=5, smangle=None, mode=None, dry_run=False):
    """
    Perform a transmission
    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        title: Title to set
        s1vg: slit 1 vertical gap
        s2vg: slit 2 vertical gap
        s3vg: slit 3 vertical gap; if None use max for instrument
        s4vg: slit 4 vertical gap; if None use max for instrument
        count_seconds: time to count for in seconds
        count_uamps: number of micro amps to count for
        count_frames: number of frames to count for
        s1hg: slit 1 horizontal gap; None to leave unchanged
        s2hg: slit 2 horizontal gap; None to leave unchanged
        s3hg: slit 3 horizontal gap; None to leave unchanged
        s4hg: slit 4 horizontal gap; None to leave unchanged
        height_offset: Height offset from normal to set the sample to (offset is in negative direction)
        smangle: super mirror angle, place in the beam, if set to 0 remove from the beam; None don't move super mirror
        mode: mode to run in; None don't change mode
        dry_run: True to print what happens; False to do experiment
    """

    print("** Transmission {} **".format(title))

    movement = _Movement(dry_run)

    movement.dry_run_warning()
    constants = get_instrument_constants()
    movement.change_to_soft_period_count()

    movement.set_translation(sample.translation)  # Move this first before the heights as this can cause some drift.

    with reset_hgaps_and_sample_height(movement, sample, constants):
        movement.change_to_mode_if_not_none(mode)

        movement.set_smangle_if_not_none(smangle)

        movement.set_height2_offset(sample.height2_offset, constants)
        movement.set_theta(0.0)

        if height_offset < 10:  # if the height offset is less than can be achieved by the fine z use this
            movement.set_height_offset(sample.height - height_offset)
        else:
            movement.set_height2_offset(sample.height2_offset - height_offset, constants)

        if s3vg is None:
            s3vg = constants.s3max
        if s4vg is None:
            s4vg = constants.s4max

        movement.set_h_gaps(s1hg, s2hg, s3hg, s4hg)
        movement.set_slit_gaps(0.0, constants, s1vg, s2vg, s3vg, s4vg, sample)
        movement.wait_for_move()

        movement.update_title(title, "", None, smangle, add_current_gaps=True)
        movement.count_for(count_uamps, count_seconds, count_frames)

        # Horizontal gaps and height reset by with reset_gaps_and_sample_height


@contextmanager
def reset_hgaps_and_sample_height(movement, sample, constants):
    """
    After the context is over reset the gaps back to the value before. If keyboard interupt give options for what to do.
    Args:
        movement(_Movement): object that does movement required (or pronts message for a dry run)
        sample: sample to get the sample offset from
        constants: instrument constants

    """
    horizontal_gaps = movement.get_gaps(vertical=False)

    def _reset_gaps():
        print("Reset horizontal gaps to {}".format(horizontal_gaps.values))
        movement.set_h_gaps(**horizontal_gaps)

        movement.set_height_offset(sample.height)
        movement.set_height2_offset(sample.height2_offset, constants)
        movement.wait_for_move()

    try:
        yield
        _reset_gaps()
    except KeyboardInterrupt:
        movement.pause()

        while True:
            choice = input("ctrl-c hit do you wish to (A)bort or (E)nd or (K)eep Counting?")
            if choice is not None and choice.upper() in ["A", "E", "K"]:
                break
            print("Invalid choice try again!")

        if choice.upper() == "A":
            movement.abort()
            print("Setting horizontal slit gaps to pre-tranmission values.")
            _reset_gaps()

        elif choice.upper() == "E":
            movement.end()
            _reset_gaps()
        elif choice.upper() == "K":
            print("Continuing counting, remember to set back horizontal slit gaps when the run is ended.")
            movement.resume()

        movement.wait_for_seconds(5)


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
    s1, s2 = movement.calculate_slit_gaps(theta, footprint, resolution, constants)
    print("For a foortprint of {} and resolution of {} at an angle {}:".format(theta, footprint, resolution))
    print("s1vg={}".format(s1))
    print("s2vg={}".format(s2))


class _Movement(object):
    """
    Encapsulate instrument changes
    """

    def __init__(self, dry_run):
        self.dry_run = dry_run

    def change_to_mode_if_not_none(self, mode):
        """
        Change the mode if not in dry run
        :param mode: mode to change to; if None don't don't change mode
        :return: new mode
        """
        if mode is not None:
            print("Change to mode: {}".format(mode))
            if not self.dry_run:
                g.cset("MODE", mode)
        else:
            mode = g.cget("MODE")["value"]
        return mode

    def dry_run_warning(self):
        """
        Print a warning if in dry run
        """
        if self.dry_run:
            print("Nothing will change this is a DRY RUN!!!")

    def set_theta(self, theta):
        """
        Set theta if not in dry run
        :param theta: new theta
        """
        print("Theta set to: {}".format(theta))
        if not self.dry_run:
            g.cset("THETA", theta)

    def get_gaps(self, vertical):
        """
        :param vertical: True for vertical gaps; False for Horizontal gaps
        :return: dictionary of gaps
        """
        v_or_h = "V" if vertical else "H"
        gaps = OrderedDict()
        for slit_num in [1, 2, 3, 4]:
            gap_pv = "S{}{}G".format(slit_num, v_or_h)
            gaps[gap_pv.lower()] = g.cget(gap_pv)["value"]

        return gaps

    def update_title(self, title, subtitle, theta, smangle, add_current_gaps):
        """
        Update the current title with or without gaps if not in dry run
        :param title: title to set
        :param subtitle: sub title to set
        :param theta: theta for the experiment
        :param smangle: sm angle; if None it doesn't appear in the title
        :param add_current_gaps: current gaps
        """
        new_title = "{} {}".format(title, subtitle)
        if theta is not None:
            new_title = "{} th={:.4g}".format(new_title, theta)
        if smangle is not None:
            new_title = "{} SM={:.4g}".format(new_title, smangle)

        if add_current_gaps:
            gaps = self.get_gaps(vertical=True).values()
            gaps.extend(self.get_gaps(vertical=False).values())
            new_title = "{} VGs ({:.3g} {:.3g} {:.3g} {:.3g}) HGs ({:.3g} {:.3g} {:.3g} {:.3g})".format(
                new_title, *gaps)

        if self.dry_run:
            print("New Title: {}".format(new_title))
        else:
            g.change_title(new_title)

    def set_height_offset(self, height_offset):
        """
        Set the sample height offset if not in dry run
        :param height_offset:
        """
        print("Sample: height offset from beam={}".format(height_offset))
        if not self.dry_run:
            g.cset("SAMPLEOFFSET", height_offset)

    def set_height2_offset(self, height, constants):
        """
        Set the sample height2 offset if the instrument has a height 2
        :param height: new height offset
        :param constants: constants for the instrument
        """
        if constants.has_height2:
            print("Sample: height2 offset from beam={}".format(height))
            if not self.dry_run:
                g.cset("HEIGHT2_OFFSET", height)
        elif height != 0:
            print("ERROR: Height 2 off set is being ignored")

    def set_translation(self, translation):
        """
        Set the smaple translation if not in dry run and wait for move
        :param translation: new translation
        """
        print("Translation to {}".format(translation))
        if not self.dry_run:
            g.cset("TRANS", translation)
            g.waitfor_move()

    def set_slit_gaps(self, theta, constants, s1vg, s2vg, s3vg, s4vg, sample):
        """
        Set the slit gaps either to user settings or calculated based on foot print and max slit size, if not in dry run
        Args:
            theta: angle theta is set to
            constants: machine constants
            s1vg: s1 vertical gap set by user; None use footprint calculated gap
            s2vg: s2 vertical gap set by user; None use footprint calculated gap
            s3vg: s3 vertical gap set by user; None use percentage of maximum
            s4vg: s4 vertical gap set by user; None use percentage of maximum
            sample: sample parameters
        """
        s1, s2 = self.calculate_slit_gaps(theta, sample.footprint, sample.resolution, constants)

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
        if s1 < 0.0 or s2 < 0.0 or s3 < 0.0 or s4 < 0.0:
            sys.stderr.write("Vertical slit gaps are being set to less than 0!\n")
        if not self.dry_run:
            g.cset("S1VG", s1)
            g.cset("S2VG", s2)
            g.cset("S3VG", s3)
            g.cset("S4VG", s4)

    def calculate_slit_gaps(self, theta, footprint, resolution, constants):
        """
        Calulcate the slit gaps
        :param theta: theta
        :param footprint: footprint of the sample
        :param resolution: resoultion required
        :param constants: instrument constants
        :return: slit 1 and slit 2 vertical gaps
        """
        s1sa = constants.s1s2 + constants.s2sa
        footprint_at_theta = footprint * sin(radians(theta))
        s1 = 2 * s1sa * tan(radians(resolution * theta)) - footprint_at_theta
        s2 = (constants.s1s2 * (footprint_at_theta + s1) / s1sa) - s1
        return s1, s2

    def set_h_gaps(self, s1hg, s2hg, s3hg, s4hg):
        """
        Set the horiztonal slit gaps if not None and if not is a dry run
        :param s1hg: slit 1 horizontal gap
        :param s2hg: slit 2 horizontal gap
        :param s3hg: slit 3 horizontal gap
        :param s4hg: slit 4 horizontal gap
        :return:
        """
        print("Setting hgaps to {} (None's are not changed)".format([s1hg, s2hg, s3hg, s4hg]))
        if s1hg < 0.0 or s2hg < 0.0 or s3hg < 0.0 or s4hg < 0.0:
            sys.stderr.write("Horizontal slit gaps are being set to less than 0!\n")

        if not self.dry_run:
            if s1hg is not None:
                g.cset("S1HG", s1hg)
            if s2hg is not None:
                g.cset("S2HG", s2hg)
            if s3hg is not None:
                g.cset("S3HG", s3hg)
            if s4hg is not None:
                g.cset("S4HG", s4hg)

    def change_to_soft_period_count(self, count=1):
        """
        Change the number of soft periods if not in dry run
        :param count: number of periods
        """
        if not self.dry_run:
            g.change_number_soft_periods(count)
        else:
            print("Number of periods set to {}".format(count))

    def set_phi_psi(self, phi, psi):
        """
        Set phi and psi if not in dry run
        :param phi: phi value to set
        :param psi: psi value to set
        """
        print("Sample: Phi={}, Psi={}".format(phi, psi))
        if not self.dry_run:
            g.cset("PHI", phi)
            g.cset("PSI", psi)

    def wait_for_move(self):
        """
        Wait for a move if not in dry run
        """
        if not self.dry_run:
            g.waitfor_move()

    def set_smangle_if_not_none(self, smangle):
        """
        Set the super mirror angle and put it in the beam if not None and not dry run
        :param smangle: super mirror angle; None for do not set and leave it where it is
        """
        if smangle is not None:
            is_in_beam = "IN" if smangle > 0.0001 else "OUT"
            print("SM angle (in beam?): {} ({})".format(smangle, is_in_beam))
            if not self.dry_run:
                g.cset("SMANGLE", smangle)
                g.cset("SMINBEAM", is_in_beam)

    def pause(self):
        """
        Pause when not in dry run
        """
        if not self.dry_run:
            g.pause()

    def abort(self):
        """
        Abort when not in dry run
        """
        if not self.dry_run:
            g.abort()

    def end(self):
        """
        End when not in dry run
        """
        if not self.dry_run:
            g.end()

    def resume(self):
        """
        Resume if not in dry run
        """
        if not self.dry_run:
            g.resume()

    def wait_for_seconds(self, seconds):
        """
        Wait for a number of seconds if not in dry run
        :param seconds: seconds to wait for
        """
        if not self.dry_run:
            g.waitfor_time(seconds)
        else:
            print("Wait for {} seconds".format(seconds))

    def count_for(self, count_uamps, count_seconds, count_frames):
        """
        Count for one of uamps, seconds, frames if not None in that order
        :param count_uamps: number of uamps to count for; None count in a different way
        :param count_seconds: number of seconds to count for; None count in a different way
        :param count_frames: number of frames to count for; None count in a different way
        """
        if count_uamps is not None:
            print("Wait for {} uA".format(count_uamps))
            if not self.dry_run:
                g.begin()
                g.waitfor_uamps(count_uamps)
                g.end()

        elif count_seconds is not None:
            print("Measure for {} s".format(count_seconds))
            if not self.dry_run:
                g.begin()
                g.waitfor_time(seconds=count_seconds)
                g.end()

        elif count_frames is not None:
            print("Wait for {} frames count (i.e. count this number of frames from the current frame)".format(
                count_frames))
            if not self.dry_run:
                final_frame = count_frames + g.get_frames()
                g.begin()
                g.waitfor_frames(final_frame)
                g.end()
