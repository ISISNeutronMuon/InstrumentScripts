"""
Base routine for reflectometry techniques
UPDATED: Feb 2022 for Cycle 2021_2.
"""
import sys
from collections import OrderedDict
from contextlib2 import contextmanager

from future.moves import itertools
from math import tan, radians, sin

from six.moves import input

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g


# import general.utilities.io
from sample import Sample
from instrument_constants import get_instrument_constants


def run_angle_new_edit(sample, angle: float, count_uamps: float = None, count_seconds: float = None,
                       count_frames: float = None, vgaps: dict = None, hgaps: dict = None, mode: str = None,
                       dry_run: bool = False, include_gaps_in_title: bool = False, osc_slit: bool = False,
                       osc_block: str = 'S2HG', osc_gap: float = None):
    """
    Move to a given theta and smangle with slits set. If a current, time or frame count are given then take a
    measurement.
    Both supermirrors removed and all angle axes enabled.

    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        angle: The angle to measure at, theta and in liquid mode also the sm angle
        count_uamps: the current to run the measurement for; None for use count_seconds
        count_seconds: the time to run the measurement for if uamps not set; None for use count_frames
        count_frames: the number of frames to wait for; None for don't count
        vgaps: vertical gaps to be set; Where not defined uses sample footprint and resolution
        hgaps: horizontal gaps to be set; Where not defined gap is unchanged
        mode: mode to run in; None don't change modes
        dry_run: If True just print what would happen; If False, run the experiment
        include_gaps_in_title: Whether current slit gap sizes should be appended to the run title or not
        osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap extent setting.
        osc_block: block to oscillate
        osc_gap: gap of slit during oscillation. If None then takes defaults (see osc_slit_setup)
    TODO: this set of examples needs updating.
    Examples:
        The simplest scan is:
        >>> my_sample = Sample("My title", "my subtitle", 0, 0, 0, 0, 0, 0.6, 3.0)
        >>> run_angle(my_sample, 0.3, count_seconds=10)
        This will use my_sample settings to perform a measurement at the theta angle of 0.3 for 10 seconds. It will set
        slits 1 and 2 so that the resolution is 0.6 and the footprint is 3, then set slits 3 based on the fraction
        of the the maximum theta allowed. It will remove all supermirrors from the beam. The mode will not be
        changed and it will not use a height gun for auto-height mode.

        >>> run_angle(my_sample, 0.5, vgaps={'s1vg': 0.1, 's2vg' 0.3}, mode="Solid")
        In this evocation we are setting theta to 0.5 with s1 and s2 set to 0.1 and 0.3. The mode is also
        changed to Solid. Depending on what this means on your instrument this may also set the offsets for components
        back to 0. No count was specified so in this case the beamline is moved to the position and left there; no
        data is captured.

        >>> run_angle(my_sample, 0.0, dry_run=True)
        In this run, dry_run is set to True so nothing will actually happen, it will only print the settings that would
        be used for the run to the screen.
    """

    print("** Run angle {} **".format(sample.title))

    movement = _Movement(dry_run)

    constants, mode_out = movement.setup_measurement(mode)

    movement.sample_setup(sample, angle, constants, mode_out)
    if hgaps is None:
        hgaps = sample.hgaps
    movement.set_axis_dict(hgaps)
    movement.set_slit_vgaps(angle, constants, vgaps, sample)
    movement.wait_for_move()
    movement.update_title(sample.title, sample.subtitle, angle, add_current_gaps=include_gaps_in_title)

    movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps, hgaps)


def run_angle_SM_new_edit(sample, angle, count_uamps=None, count_seconds=None, count_frames=None, vgaps: dict = None,
                          hgaps: dict = None, smangle=0.0, mode=None, do_auto_height=False, laser_offset_block="b.KEYENCE",
                          fine_height_block="HEIGHT", auto_height_target=0.0, continue_on_error=False, dry_run=False,
                          include_gaps_in_title=False,
                          smblock='SM2', osc_slit: bool = False, osc_block: str = 'S2HG', osc_gap: float = None):
    """
    Move to a given theta and smangle with slits set. If a current, time or frame count are given then take a
    measurement.
    Behaviour depends on mode:
        If 'Liquid' then phi-psi do not move and smangle determined by theta.
        If not Liquid then phi-psi enabled and smangle is set via smangle Arg.

    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        angle: The angle to measure at, theta and in liquid mode also the sm angle
        count_uamps: the current to run the measurement for; None for use count_seconds
        count_seconds: the time to run the measurement for if uamps not set; None for use count_frames
        count_frames: the number of frames to wait for; None for don't count
        vgaps: vertical gaps to be set; Where not defined uses sample footprint and resolution
        hgaps: horizontal gaps to be set; Where not defined gap is unchanged
        smangle: super mirror angle, place in the beam, if set to 0 remove from the beam; None don't move super mirror
        mode: mode to run in; None don't change modes
        do_auto_height: if True when taking data run the auto-height routine
        laser_offset_block: The block for the laser offset from centre
        fine_height_block: The block for the sample fine height
        auto_height_target: The target value for laser offset if using auto height
        continue_on_error: If True, continue script on error; If False, interrupt and prompt the user on error
        dry_run: If True just print what would happen; If False, run the experiment
        include_gaps_in_title: Whether current slit gap sizes should be appended to the run title or not
        smblock: prefix of supermirror block to be used; generally expect 'SM1' or 'SM2' for INTER or 'SM' for SURF.
            List of strings can be provided to use multiple mirrors.
        osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap extent setting.
        osc_block: block to oscillate
        osc_gap: gap of slit during oscillation. If None then takes defaults (see osc_slit_setup)
    Examples:
        The simplest scan is:
        >>> my_sample = Sample("My title", "my subtitle", 0, 0, 0, 0, 0, 0.6, 3.0)
        >>> run_angle_SM(my_sample, 0.3, count_seconds=10)
        This will use my_sample settings to perform a measurement at the theta angle of 0.3 for 10 seconds. It will set
        slits 1 and 2 so that the resolution is 0.6 and the footprint is 3, then set slits 3 based on the fraction
        of the the maximum theta allowed. If liquid mode in IBEX it will calculate the supermirror angle to keep the
        sample flat, otherwise the super mirror will be moved out of the beam. It will not use a height gun for
         auto-height mode.

        >>> run_angle_SM(my_sample, 0.5, vgaps={'s1vg': 0.1, 's2vg': 0.3}, mode="Solid")
        In this evocation we are setting theta to 0.5 with s1 and s2 set to 0.1 and 0.3. The mode is also
        changed to Solid. Depending on what this means on your instrument this may also set the offsets for components
        back to 0. No count was specified so in this case the beamline is moved to the position and left there; no
        data is captured.

        >>> run_angle_SM(my_sample, 0.0, dry_run=True)
        In this run, dry_run is set to True so nothing will actually happen, it will only print the settings that would
        be used for the run to the screen.
    """

    print("** Run angle {} **".format(sample.title))

    movement = _Movement(dry_run)

    constants, mode_out = movement.setup_measurement(mode)
    smblock_out, smang_out = movement.sample_setup(sample, angle, constants, mode_out, smang=smangle, smblock=smblock)

    if do_auto_height:
        auto_height(laser_offset_block, fine_height_block, target=auto_height_target,
                    continue_if_nan=continue_on_error, dry_run=dry_run)

    if hgaps is None:
        hgaps = sample.hgaps
    movement.set_axis_dict(hgaps)
    movement.set_slit_vgaps(angle, constants, vgaps, sample)
    movement.wait_for_move()

    movement.update_title(sample.title, sample.subtitle, angle, smang_out, smblock_out, add_current_gaps=include_gaps_in_title)

    movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps, hgaps)


# TODO: Do we want to change the order of the arguments here?
def transmission_new_edit(sample, title: str, vgaps: dict = None, hgaps: dict = None, count_uamps: float = None,
                          count_seconds: float = None, count_frames: float = None, height_offset: float = 5,
                          mode: str = None, dry_run: bool = False, include_gaps_in_title: bool = True,
                          osc_slit: bool = True, osc_block: str = 'S2HG', osc_gap: float = None, at_angle: float = 0.7):
    """
    Perform a transmission with both supermirrors removed. Args: sample (techniques.reflectometry.sample.Sample): The
    sample to measure title: Title to set vgaps: vertical gaps to be set; for each gap if not specified then
    determined for angle at_angle hgaps: horizontal gaps to be set; for each gap if not specified then remains
    unchanged count_seconds: time to count for in seconds count_uamps: number of micro amps to count for
    count_frames: number of frames to count for height_offset: Height offset from normal to set the sample to (offset
    is in negative direction) mode: mode to run in; None don't change mode dry_run: If True just print what would
    happen; If False, run the transmission include_gaps_in_title: Whether current slit gap sizes should be appended
    to the run title or not osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap
    extent setting. Takes extent from equivalent gap Args if exists otherwise, goes into defaults in osc_slit_setup.
    osc_block: block to oscillate osc_gap: gap of slit during oscillation. If None then takes defaults (see
    osc_slit_setup) at_angle: angle to calculate slit settings

    TODO: Need to update examples with oscillation.
    Examples:
        The simplest transmission is:

        >>> my_sample = Sample("My title", "my subtitle", 0, 0, 0, 0, 0, 0.6, 3.0) >>> transmission(my_sample,
        "My Title", count_seconds=1) This will set slit gaps 1 and 2 based on sample parameters. Slits 3 and 4 will
        be set to maximum vertical width. The horizontal slits will be left where they are. The height of the sample
        will be set to 5mm below the expected sample position. The super mirror will stay where it is and the mode
        won't change. After the run the horizontal slits will be set back to where they were when the move started.

        A more complicated example:
        >>> transmission(my_sample, "My Title", vgaps={"S1VG": 0.1, "S2VG": 0.2, "S3VG": 0.3}, count_frames=1,
        >>>              hgaps = {'s1hg': 20, 's2hg': 20, 's3hg': 20}, smangle=0.1, dry_run=True)
        Dry_run is true here so nothing will actually happen, but the effects will be printed to the screen. If
        dry_run had not been set then the vertical gaps would be set to 0.1, 0.2, 0.3 and 0.4, the horizontal gaps
        would be all set to 20. The super mirror would be moved into the beam and set to the angle 0.1.
        The system will be record at least 1 frame of data.
    """

    print("** Transmission {} **".format(title))

    movement = _Movement(dry_run)
    constants, mode_out = movement.setup_measurement(mode)

    with reset_hgaps_and_sample_height_new(movement, sample, constants):
        movement.sample_setup(sample, 0.0, constants, mode_out, height_offset)

        if vgaps is None:
            vgaps = {}
        if "S3VG".casefold() not in vgaps.keys():
            vgaps.update({"S3VG": constants.s3max})

        if hgaps is None:
            hgaps = sample.hgaps
        movement.set_axis_dict(hgaps)
        movement.set_slit_vgaps(at_angle, constants, vgaps, sample)
        # Edit for this to be an instrument default for the angle to be used in calc when vg not defined.
        movement.wait_for_move()

        movement.update_title(title, "", None, add_current_gaps=include_gaps_in_title)
        movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps, hgaps)

        # Horizontal gaps and height reset by with reset_gaps_and_sample_height


# TODO: Do we want to change the order of the arguments here?
def transmission_new_SM_edit(sample, title: str, vgaps: dict = None, hgaps: dict = None,
                             count_uamps: float = None, count_seconds: float = None, count_frames: float = None,
                             height_offset: float = 5, smangle: float = 0.0,
                             mode: str = None, dry_run: bool = False, include_gaps_in_title: bool = True,
                             osc_slit: bool = True,
                             osc_block: str = 'S2HG', osc_gap: float = None, at_angle: float = 0.7,
                             smblock: str = 'SM2'):
    """
    Perform a transmission. Smangle is set via smangle Arg and the mirror can be specified.
    Behaviour depends on mode:
        If 'Liquid' then phi-psi do not move.
        If not Liquid then phi-psi enabled.
    Args:
        sample (techniques.reflectometry.sample.Sample): The sample to measure
        title: Title to set
        vgaps: vertical gaps to be set; for each gap if not specified then determined for angle at_angle
        hgaps: horizontal gaps to be set; for each gap if not specified then remains unchanged
        count_seconds: time to count for in seconds
        count_uamps: number of micro amps to count for
        count_frames: number of frames to count for
        height_offset: Height offset from normal to set the sample to (offset is in negative direction)
        smangle: super mirror angle, place in the beam, if set to 0 remove from the beam; None don't move super mirror
        mode: mode to run in; None don't change mode
        dry_run: If True just print what would happen; If False, run the transmission
        include_gaps_in_title: Whether current slit gap sizes should be appended to the run title or not
        osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap extent setting. Takes extent
        from equivalent gap Args if exists otherwise, goes into defaults in osc_slit_setup.
        osc_block: block to oscillate
        osc_gap: gap of slit during oscillation. If None then takes defaults (see osc_slit_setup)
        at_angle: angle used in calculating slit settings
        smblock: prefix of supermirror block to be used; generally expect 'SM1' or 'SM2' for INTER or 'SM' for SURF.
            List of strings can be provided to use multiple mirrors.

    TODO: Need to update examples with oscillation.
    Examples:
        The simplest transmission is:

        >>> my_sample = Sample("My title", "my subtitle", 0, 0, 0, 0, 0, 0.6, 3.0)
        >>> transmission(my_sample, "My Title", 0.1, 0.2, count_seconds=1)
        This will set slit gaps 1 and 2 to 0.1 and 0.2. Slits 3 and 4 will be set to maximum vertical width. The
        horizontal slits will be left where they are. The height of the sample will be set to 5mm below the expected
        sample position. The super mirror will stay where it is and the mode won't change. After the run the horizontal
        slits will be set back to where they were when the move started.

        A more complicated example:
        >>> transmission(my_sample, "My Title", 0.1, 0.2, 0.3, 0.4, count_frames=1,
        >>>              s1hg=20, s2hg=20, s3hg=20, s4hg=20, smangle=0.1, mode="PNR", dry_run=True)
        Dry_run is true here so nothing will actually happen, but the effects will be printed to the screen. If
        dry_run had not been set then the vertical gaps would be set to 0.1, 0.2, 0.3 and 0.4, the horizontal gaps
        would be all set to 20. The super mirror would be moved into the beam and set to the angle 0.1. The mode will
        be changed to PNR. The system will be record at least 1 frame of data.
    """

    print("** Transmission {} **".format(title))

    movement = _Movement(dry_run)
    constants, mode_out = movement.setup_measurement(mode)

    with reset_hgaps_and_sample_height_new(movement, sample, constants):

        smblock_out, smang_out = movement.sample_setup(sample, 0.0, constants, mode_out, height_offset, smangle, smblock)

        if vgaps is None:
            vgaps = {}
        if "S3VG".casefold() not in vgaps.keys():
            vgaps.update({"S3VG": constants.s3max})
        if hgaps is None:
            hgaps = sample.hgaps
        movement.set_axis_dict(hgaps)
        movement.set_slit_vgaps(at_angle, constants, vgaps, sample)
        # Edit for this to be an instrument default for the angle to be used in calc when vg not defined.
        movement.wait_for_move()

        movement.update_title(title, "", None, smang_out, smblock_out, add_current_gaps=include_gaps_in_title)
        movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap,
                                   vgaps, hgaps)

        # Horizontal gaps and height reset by with reset_gaps_and_sample_height


# Added extra part for centres too.
@contextmanager
def reset_hgaps_and_sample_height_new(movement, sample, constants):
    """
    After the context is over reset the gaps back to the value before and set the height to the default sample height.
    Edited to reset the gap centres too.
    If keyboard interrupt give options for what to do.
    Args:
        movement(_Movement): object that does movement required (or pronts message for a dry run)
        sample: sample to get the sample offset from
        constants: instrument constants

    """
    horizontal_gaps = movement.get_gaps(vertical=False, centres=False)
    horizontal_cens = movement.get_gaps(vertical=False, centres=True)

    def _reset_gaps():
        print("Reset horizontal centres to {}".format(list(horizontal_cens.values())))
        movement.set_axis_dict(horizontal_cens)
        print("Reset horizontal gaps to {}".format(list(horizontal_gaps.values())))
        movement.set_axis_dict(horizontal_gaps)
        # TODO join the above together?

        movement.set_axis("HEIGHT", sample.height_offset, constants)
        movement.set_axis("HEIGHT2", sample.height2_offset, constants)
        movement.wait_for_move()

    try:
        yield
        _reset_gaps()
    except KeyboardInterrupt:
        running_on_entry = not movement.is_in_setup()
        if running_on_entry:
            g.pause()

        while True:
            print("")
            choice = input("ctrl-c hit do you wish to (A)bort or (E)nd or (K)eep Counting?")
            if choice is not None and choice.upper() in ["A", "E", "K"]:
                break
            print("Invalid choice try again!")

        if choice.upper() == "A":
            if running_on_entry:
                g.abort()
            print("Setting horizontal slit gaps to pre-tranmission values.")
            _reset_gaps()

        elif choice.upper() == "E":
            if running_on_entry:
                g.end()
            _reset_gaps()

        elif choice.upper() == "K":
            print("Continuing counting, remember to set back horizontal slit gaps when the run is ended.")
            if running_on_entry:
                g.resume()

        movement.wait_for_seconds(5)
        print("\n\n PRESS ctl + c to get the prompt back \n\n")  # This is because there is a bug in pydev
        raise  # reraise the exception so that any running script will be aborted


# THIS MAY BECOME REDUNDANT.
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
    calc_dict = movement.calculate_slit_gaps(theta, footprint, resolution, constants)
    print("For a footprint of {} and resolution of {} at an angle {}:".format(theta, footprint, resolution))
    print(calc_dict)


def slit_check_new(sample=None, theta: float = 0.7, footprint: float = None, resolution: float = None):
    """
    Check the slits values with option based on sample. If footprint and resolution are given this will supersede the
    sample settings.
    TODO: The default theta value can be later tied to instrument defaults.
    Args:
        :param sample: option to find value of pre-defined Sample.
        :param theta: theta for calculation, default is 0.7.
        :param footprint: desired incident footprint
        :param resolution: desired incident resolution
    :return: prints in calculated values.

    Examples:
    To calculate for a pre-defined sample at default angle=0.7 or for an alternative angle of 0.8:
        slit_check_new(mySample)
        slit_check_new(mySample, 0.8)
    To calculate for specified footprint and resolution:
        slit_check_new('', 0.7, 60, 0.03) or slit_check_new(theta=0.7,footprint=60,resolution=0.03)
        slit_check_new(mySample, 0.7, 60, 0.03)
    In the last case the settings within mySample will be ignored and the values of 60 and 0.03 used.
    """
    if not footprint and not resolution:
        footprint = sample.footprint
        resolution = sample.resolution
        print("Calculating slit gaps for sample: {}".format(sample))
    constants = get_instrument_constants()
    movement = _Movement(True)
    try:
        calc_dict = movement.calculate_slit_gaps(theta, footprint, resolution, constants)
        print("For a footprint of {} and resolution of {} at an angle {}:".format(footprint, resolution, theta))
        print(calc_dict)
    except:
        print("Error: you must define either a existing sample for the calculation, or a footprint AND resolution.")


def auto_height(laser_offset_block: str, fine_height_block: str, target: float = 0.0, continue_if_nan: bool = False,
                dry_run: bool = False):
    """
    Moves the sample fine height axis so that it is centred on the beam, based on the readout of a laser height gun.

    Args:
        laser_offset_block: The name of the block for the laser offset from centre
        fine_height_block: The name of the block for the sample fine height axis
        target: The target laser offset
        continue_if_nan: Defines what to do in case of invalid values. If True, ignore errors and continue execution.
            If False, break and wait for user input. (default: False)
        dry_run: If True just print what is going to happen; If False, set the auto height

        >>> auto_height(b.KEYENCE, b.HEIGHT2)

        Moves HEIGHT2 by (KEYENCE * (-1))

        >>> auto_height(b.KEYENCE, b.HEIGHT2, target=0.5, continue_if_nan=True)

        Moves HEIGHT2 by (target - b.KEYENCE) and does not interrupt script execution if an invalid value is read.
    """
    try:
        target_height, current_height = _calculate_target_auto_height(laser_offset_block, fine_height_block, target)
        if not dry_run:
            g.cset(fine_height_block, target_height)
            _auto_height_check_alarms(fine_height_block)
            g.waitfor_move()
    except TypeError as e:
        prompt_user = not (continue_if_nan or dry_run)
        general.utilities.io.alert_on_error("ERROR: cannot set auto height (invalid block value): {}".format(e),
                                            prompt_user)


def _auto_height_check_alarms(fine_height_block):
    """
    Checks whether a given block for the fine height axis is in alarm after a move and sends an alert if not.

    Args:
        fine_height_block: The name of the fine height axis block
    """
    alarm_lists = g.check_alarms(fine_height_block)
    if any(fine_height_block in alarm_list for alarm_list in alarm_lists):
        general.utilities.io.alert_on_error(
            "ERROR: cannot set auto height (target outside of range for fine height axis?)", True)


def _calculate_target_auto_height(laser_offset_block, fine_height_block, target):
    if laser_offset_block is None:
        raise TypeError("No block given for laser offset.")
    elif fine_height_block is None:
        raise TypeError("No block given for fine height.")
    current_laser_offset = g.cget(laser_offset_block)["value"]
    difference = target - current_laser_offset

    current_height = g.cget(fine_height_block)["value"]
    target_height = current_height + difference

    print("Target for fine height axis: {} (current {})".format(target_height, current_height))
    return target_height, current_height


class _Movement(object):
    """
    Encapsulate instrument changes
    """

    def __init__(self, dry_run):
        self.dry_run = dry_run

    def change_to_mode_if_not_none(self, mode):
        """
        Change the mode if not in dry run
        :param mode: mode to change to; if None don't change mode
        :return: new mode
        """
        if mode is not None:
            print("Change to mode: {}".format(mode))
            if not self.dry_run:
                g.cset("MODE", mode)
        else:
            mode = self._get_block_value("MODE")
        return mode

    def dry_run_warning(self):
        """
        Print a warning if in dry run
        """
        if self.dry_run:
            print("Nothing will change this is a DRY RUN!!!")

    def set_axis(self, axis: str, value: float, constants):
        """
        Set an axis if not in dry run. If dry run will flag if axis does not exist.
        Special behaviour for height2_offset based on whether in instrument constants.
        Args:
            axis: axis block to set
            value: value to set axis to
            constants: constants for the instrument to check height behaviour
        """
        special_axes = ['HEIGHT2']  # This could link to an instrument specific function?
        if axis.upper() in special_axes and not constants.has_height2:
            print("ERROR: Height 2 off set is being ignored")
        else:
            print("{} set to: {}".format(axis, value))
            if not self.dry_run:
                try:
                    g.cset(axis, value)
                except:
                    raise KeyError("Block {} does not exist".format(axis))
            else:
                try:
                    self._get_block_value(axis)
                except:
                    raise KeyError("Block {} does not exist".format(axis))

    def get_gaps(self, vertical: bool, centres: bool = False, slitrange: list = ['1', '2', '3']):
        """
        :param vertical: True for vertical gaps; False for Horizontal gaps
        :param centres: True to return centres; False to return gaps
        :param slitrange: string list to iterate over
        :return: dictionary of gaps
        """
        v_or_h = "V" if vertical else "H"
        g_or_c = "C" if centres else "G"
        gaps = {}
        for slit_num in slitrange:
            gap_pv = "S{}{}{}".format(slit_num, v_or_h, g_or_c)
            gaps[gap_pv.lower()] = self._get_block_value(gap_pv)

        return gaps

    def _get_block_value(self, pv_name):
        """
        Get a block value of post an error if block doesn't exist

        :param pv_name: pv name
        :return :value of pv
        :raises ValueError: if block does not exist

        """
        block_value = g.cget(pv_name)
        if block_value is None:
            raise KeyError("Block {} does not exist".format(pv_name))
        return block_value["value"]

    def update_title(self, title, subtitle, theta, smangle=None, smblock='SM', add_current_gaps=False):
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
            new_title = "{} {}={:.4g}".format(new_title, smblock, smangle)
        else:
            new_title = "{} transmission".format(new_title)

        if add_current_gaps:
            # TODO sort out the gaps here. Is this changed format ok?
            #gaps = itertools.chain(self.get_gaps(vertical=True).values(), self.get_gaps(vertical=False).values())
            #new_title = "{} VGs ({:.3g} {:.3g} {:.3g} {:.3g}) HGs ({:.3g} {:.3g} {:.3g} {:.3g})".format(new_title, *gaps)
            vgaps = self.get_gaps(vertical=True,slitrange=['1', '1A', '2', '3'])
            hgaps = self.get_gaps(vertical=False)
            for i, k in vgaps.items():
                new_title = "{} {}={:.4g}".format(new_title, i, k)
            for i, k in hgaps.items():
                new_title = "{} {}={:.3g}".format(new_title, i, k)
            #new_title = "{} ({}) ({})".format(new_title, vgaps, hgaps)

        if self.dry_run:
            g.change_title(new_title)
            print("New Title: {}".format(new_title))
        else:
            g.change_title(new_title)

    def set_slit_vgaps(self, theta: float, constants, vgaps: dict, sample):
        """
        Set the vertical slit gaps either to user settings or calculated based on footprint and max slit size,
        if not in dry run
        Args:
            theta: angle theta is set to
            constants: machine constants
            vgaps: user defined gaps
            sample: sample parameters
        """
        calc_dict = self.calculate_slit_gaps(theta, sample.footprint, sample.resolution, constants)

        factor = theta / constants.max_theta
        s3 = constants.s3max * factor
        calc_dict.update({'S3VG': s3})
        
        if vgaps is None:
            vgaps = {}
        ## Look at inputs. Might not need to deal with None...?
        for key, value in vgaps.items():
            calc_dict.update({} if value is None else {key.upper(): value})

        print("Slit gaps set to: {}".format(calc_dict))
        for key, value in calc_dict.items():
            if value < 0.0:
                sys.stderr.write("Vertical slit gaps are being set to less than 0!\n")
        self.set_axis_dict(calc_dict)

    def set_axis_dict(self, axes_to_set: dict):
        """
        Set a dictionary of axes to new set points, if not in dry run. Primary use for slits.
        Args:
            axes_to_set: dictionary of axes with new set values
        Raises error if axis block does not exist.
        """
        # TODO:  And for less than 0 as warning?
        print("Setting axes: {}".format(axes_to_set))
        for gap in axes_to_set.keys():
            if not self.dry_run:
                try:
                    g.cset(gap, axes_to_set[gap])
                except:
                    raise KeyError("Block {} does not exist".format(gap))
            else:
                try:
                    self._get_block_value(gap)
                except:
                    raise KeyError("Block {} does not exist".format(gap))

    def calculate_slit_gaps(self, theta, footprint, resolution, constants):
        """
        Calculate the slit gaps
        :param theta: theta
        :param footprint: footprint of the sample
        :param resolution: resolution required
        :param constants: instrument constants
        :return: slit 1 and slit 2 vertical gaps
        Added warnings and errors for s2 > s1 and negative values respectively.
        """
        s1sa = constants.s1s2 + constants.s2sa
        footprint_at_theta = footprint * sin(radians(theta))
        s1 = 2 * s1sa * tan(radians(resolution * theta)) - footprint_at_theta
        s2 = (constants.s1s2 * (footprint_at_theta + s1) / s1sa) - s1
        if s2 > s1:
            print("Warning: Calculation gives s2vg larger than s1vg. The script will continue.")
        elif s1 < 0 or s2 < 0:
            raise ValueError("The slit calculation gives a negative gap. Check the footprint and resolution values.")
        return {'S1VG': s1, 'S2VG': s2}

    # This and the centres below can be combined if input is a dictionary instead.

    def change_to_soft_period_count(self, count=1):
        """
        Change the number of soft periods if not in dry run
        :param count: number of periods
        """
        if not self.dry_run:
            g.change_number_soft_periods(count)
        else:
            print("Number of periods set to {}".format(count))

    def wait_for_move(self):
        """
        Wait for a move if not in dry run
        """
        if not self.dry_run:
            g.waitfor_move()

    def set_smangle_if_not_none(self, smangle, smblock='SM2'):
        """
        Set the super mirror angle and put it in the beam if not None and not dry run
        :param smangle: super mirror angle; None for do not set and leave it where it is
        :type smangle: float
        :param smblock: block to be set. Expect 'SM2' or 'SM1' (or 'SM' for non-INTER).
        :type smblock: str
        TODO: Tie block options to instrument constants.
        """
        if smangle is not None:
            is_in_beam = "IN" if smangle > 0.0001 else "OUT"
            print("{} angle (in beam?): {} ({})".format(smblock, smangle, is_in_beam))
            if not self.dry_run:
                g.cset("{}INBEAM".format(smblock), is_in_beam)
                if smangle > 0.0001:
                    g.cset("{}ANGLE".format(smblock), smangle)

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

    def count_osc_slit(self, slit_block: str, slit_gap: float = None, slit_extent: float = None,
                       count_uamps: float = None,
                       count_seconds: float = None, count_frames: float = None):
        """
        Starts and ends a measurement with a block oscillating during the measurement. Written as for slit but could be
        any block with minor adjustment. If the gap is not smaller than the extent of the oscillation then it runs a
        normal measurement.
        See osc_slit_setup for setup and defaults.
        Run times will be slightly long as it completes a full oscillation before checking if the requested duration
        has been met.
        A maximum wait is included on the movement in case close to a limit but the maxwait value may need adjusting.
        At end of measurement, the slit centre is set back to its original centre point.
        TODO: Does the gap also need to be reset?

        If multiple counts are non-zero then will take first non-zero in order uamps, seconds, frames.
        Args:
            slit_block: block to be moved during oscillation
            slit_gap: gap of slit during oscillation
            slit_extent: total range of oscillation, based around initial centre (see osc_slit_setup)
            count_uamps: number of uamps to count for; None=count in a different way
            count_seconds: number of seconds to count for; None=count in a different way
            count_frames: number of frames to count for; None=count in a different way
        """
        c_block, c_prior, c_min, c_max = self.osc_slit_setup(slit_block, slit_gap, slit_extent)
        self.wait_for_move()
        count_options = {'g.get_uamps()': count_uamps, 'g.get_time_since_begin(False)': count_seconds,
                         'g.get_frames()': count_frames}
        count_choice_idx = [i for i in count_options if count_options[i] is not None][0]
        print(count_choice_idx)
        # Alternative way to get durations:
        # count_options = {'total_current': count_uamps,'run_time': count_seconds, 'good_frames_total': count_frames}
        # g.get_dashboard()['run_time']; #g.get_dashboard()['good_frames_total']; #g.get_dashboard()['total_current']

        if not self.dry_run:
            if c_min < c_max:
                g.begin()
                current_counts = eval(count_choice_idx)
                print(current_counts)
                while current_counts < count_options[count_choice_idx]:
                    g.cset(c_block, c_min)
                    g.waitfor_block(c_block, c_min, maxwait=40)
                    g.waitfor_time(seconds=1)  ##use sleep or remove?
                    g.cset(c_block, c_max)
                    g.waitfor_block(c_block, c_max, maxwait=40)
                    g.waitfor_time(seconds=1)
                    current_counts = eval(count_choice_idx)
                    print("Continuing run, counts at {}={}".format(count_choice_idx, current_counts))
                g.end()
            else:
                self.count_for(count_uamps=count_uamps, count_seconds=count_seconds, count_frames=count_frames)

            g.cset(c_block, c_prior)
        else:
            print("Run with oscillating {} with gap of {} over a total width of {}.".format(slit_block, slit_gap,
                                                                                            slit_extent))

    def osc_slit_setup(self, slit_block: str, slit_gap: float = None, slit_extent: float = None):
        """
        Setup for the oscillating slit. Sets the slit gap for the oscillation and calculates the min and max movement
        positions for the oscillation. If extent is not provided this is taken from a default list or if not in default
        list then uses current block value. The same is true of the gap value (i.e. would default to not oscillating if
        values not provided).
        The block for the slit centre is taken as the slit_block with the final letter changed to 'C' (i.e. could work
        for HG or VG).
        TODO: tie into instrument defaults.
        Args:
            slit_block: block of slit to oscillate
            slit_gap: gap of slit during oscillation
            slit_extent: range of oscillation movement

        Returns: block to be used as the centre point, prior centre point for resetting, min and max of movement.
        """
        HG_defaults = {'S1HG': 50, 'S2HG': 30, 'S3HG': 60, 'S4HG': 53}
        if not slit_extent:
            try:
                slit_extent = HG_defaults[slit_block]
            except:
                slit_extent = self._get_block_value(slit_block)
        if not slit_gap:
            try:
                slit_gap = HG_defaults[slit_block]
            except:
                slit_gap = self._get_block_value(slit_block)

        block_for_centre = f"{slit_block[:-1]}{'C'}"
        prior_centre = self._get_block_value(block_for_centre)
        print('Settings before oscillating slit measurement: {}={}'.format(block_for_centre, prior_centre))

        centre_min = prior_centre - (slit_extent / 2) + (slit_gap / 2)
        centre_max = prior_centre + (slit_extent / 2) - (slit_gap / 2)

        if not self.dry_run:
            g.cset(slit_block, slit_gap)

        return block_for_centre, prior_centre, centre_min, centre_max

    def is_in_setup(self):
        """
        :Returns True if DAE is in setup; in dry run mode will return True
        """
        if self.dry_run:
            return True
        else:
            return g.get_runstate() == "SETUP"

    def current_mode(self):
        """
        Returns current mode of instrument. General output is in string form.
        (e.g. 'Solid', 'LIQUID', 'VERTICAL')
        """
        mode = g.cget("MODE").get('value')
        print("Instrument mode set to: {}".format(mode))
        return mode

    def setup_measurement(self, mode=None, periods=1):
        """
        Sets up the general instrument settings for the measurement.
        Args:
            mode: changes to this mode if given; else will return current mode.
            periods: allows change of software periods
        Returns:
            instrument constants, updated mode
        """
        self.dry_run_warning()
        constants = get_instrument_constants()
        self.change_to_soft_period_count(count=periods)
        mode_out = self.change_to_mode_if_not_none(mode)
        print("Mode {}".format(mode_out))
        return constants, mode_out

    def sample_setup(self, sample, angle, inst_constants, mode, trans_offset=0.0, smang=0.0, smblock='SM2'):
        """
        Moves to the sample position ready for a measurement.
        Does not set slits as this is not part of sample object, but could be changed.
        Args:
            sample: sample to setup
            angle: angle for measurement, set zero for transmission
            inst_constants: instrument constants for height check
            mode: mode of instrument e.g. Liquid, Solid, PNR
            mode: if LIQUID does not activate phi and psi
            trans_offset: value subtracted from height position default 0.0. Required for transmission.
            smang: angle for supermirror, default to 0.0 to keep out of beam
            smblock: supermirror blocks to use, can be a list for multiple mirrors
        """
        self.set_axis("TRANS", sample.translation, constants=inst_constants)
        smblock_out, smang_out = self._SM_setup(angle, inst_constants, smang, smblock, mode)
        self.set_axis("THETA", angle, constants=inst_constants)
        if mode.upper() != "LIQUID":
            self.set_axis("PSI", sample.psi_offset, constants=inst_constants)
            self.set_axis("PHI", sample.phi_offset + angle, constants=inst_constants)
        if inst_constants.has_height2:
            if angle == 0 and trans_offset > 10:  #i.e. if transmission
                self.set_axis("HEIGHT2", sample.height2_offset - trans_offset, constants=inst_constants)
                self.set_axis("HEIGHT", sample.height_offset, constants=inst_constants)
            else:
                self.set_axis("HEIGHT2", sample.height2_offset, constants=inst_constants)
                self.set_axis("HEIGHT", sample.height_offset - trans_offset, constants=inst_constants)
        else:
            self.set_axis("HEIGHT", sample.height_offset - trans_offset, constants=inst_constants)
        return smblock_out, smang_out

    def _SM_setup(self, angle, inst_constants, smangle=0.0, smblock='SM2', mode=None):
        """
        Setup mirrors in and out of beam and at correct angles.
        Args:
            angle: theta value for calculation
            inst_constants: instrument constants for natural beam angle
            smangle: mirror angle to use, default to 0.0 to be out of beam (overwritten if liquid mode)
            smblock: axis for mirror, can be a list for multiple mirrors
            mode: flag for liquid mode where smangle is determined from angle instead
        """
        if mode.upper() == "LIQUID" and angle != 0.0:
            # In liquid the sample is tilted by the incoming beam angle so that it is level, this is accounted for by
            # adjusting the super mirror
            smang = (inst_constants.incoming_beam_angle - angle) / 2
        else:
            smang = smangle
        # TODO: Need to change the except statement to an error/warning.
        SM_defaults = {'SM1': 0.0, 'SM2': 0.0}
        if type(smblock) == str:
            smblock = [smblock]
        for mirrors in smblock:
            try:
                SM_defaults[mirrors.upper()] = smang / (len(smblock))
            except:
                print('Incorrect SM block given: {}'.format(mirrors.upper()))
        print('SM values to be set: {}'.format(SM_defaults))
        for mir in SM_defaults.keys():
            self.set_smangle_if_not_none(SM_defaults[mir], mir)
        return smblock, smang

    def start_measurement(self, count_uamps: float = None, count_seconds: float = None, count_frames: float = None,
                          osc_slit: bool = False, osc_block: str = 'S2HG', osc_gap: float = None, vgaps: dict = None,
                          hgaps: dict = None):
        """
        Starts a measurement based on count inputs and oscillating inputs.
        Args:
            count_uamps: the current to run the measurement for; None for use count_seconds
            count_seconds: the time to run the measurement for if uamps not set; None for use count_frames
            count_frames: the number of frames to wait for; None for don't count
            osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap extent setting.
            osc_block: block to oscillate
            osc_gap: gap of slit during oscillation. If None then takes defaults (see osc_slit_setup)
            vgaps: vertical gap dict to check for osc_extent
            hgaps: horizonal gap dict to check for osc_extent
        """
        if count_seconds is None and count_uamps is None and count_frames is None:
            print("Setup only - no measurement")
        elif osc_slit:
            # Tries to take the extent for oscillation from the equivalent param e.g. s2hg.
            # Otherwise carries None to osc input.
            hgaps.update(vgaps)
            try:
                use_block = hgaps[osc_block.casefold()]
                print('using block {}={}'.format(osc_block, use_block))
            except:
                use_block = None
            # If the gap isn't specified, this is set to match the extent (i.e. not osc).
            if osc_gap is None:
                osc_gap = use_block
            print('Inputs: osc_block {}, osc_gap {},use_block {}'.format(osc_block, osc_gap, use_block))
            self.count_osc_slit(osc_block, osc_gap, use_block, count_uamps, count_seconds, count_frames)
            # TODO Add to title or leave?
        else:
            # Think this might be redundant but keep for safety.
            self.count_for(count_uamps, count_seconds, count_frames)

