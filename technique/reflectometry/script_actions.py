import inspect
import logging
# from termcolor import colored
import os
import re
from datetime import datetime
from datetime import timedelta
from math import fabs

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .mocks import g

# import general.utilities.io
from .sample import Sample
from .NR_motion import _Movement
from .instrument_constants import get_instrument_constants #TODO: update this path as required.

os.system('color')

blocks = g.get_blocks()  # TODO: Need a way to check if blocks are available in config before running.
print(blocks)

# Define MESSAGE log level
RUN = 11
RUN_SM = 12
TRANS = 13
TRANS_SM = 14
CONTRASTCHANGE = 15
INJECT = 16
GO_TO_PRESSURE = 17
GO_TO_AREA = 18

# "Register" new logging level
logging.addLevelName(RUN, 'RUN')
logging.addLevelName(RUN_SM, 'RUN_SM')
logging.addLevelName(TRANS, 'TRANS')
logging.addLevelName(TRANS_SM, 'TRANS_SM')
logging.addLevelName(CONTRASTCHANGE, 'CONTRASTCHANGE')
logging.addLevelName(INJECT, 'INJECT')
logging.addLevelName(GO_TO_PRESSURE, 'GO_TO_PRESSURE')
logging.addLevelName(GO_TO_AREA, 'GO_TO_AREA')


def run_summary():
    # print("\n=== Total time: ", str(int(DryRun.run_time / 60)) + "h " + str(int(DryRun.run_time % 60)) + "min ===\n")

    # Add the scritp time to the current time
    newtime = datetime.now() + timedelta(minutes=DryRun.run_time)
    ETA = newtime.strftime("%d %b %Y, %H:%M")

    volumes = '\033[2;34m Volumes used for contrast changes: ' + \
              str([round(v) for v in DryRun.buffer_volumes]) + " mL \033[0;0m"
    volumes = volumes.center(len(volumes))

    print('\n\t \u2554' + '\u2550' * (len(volumes) - 13) + '\u2557')
    print('\t \u2551' + volumes + '\u2551')
    total_time = ("=== Total time: " + str(int(DryRun.run_time / 60)) + "h " +
                  str(int(DryRun.run_time % 60)) + "min ===").center(len(volumes) - 13)

    print('\t \u2551' + total_time + '\u2551')
    finish = f'Script will finish {ETA}'.center(len(volumes) - 13)
    print('\t \u2551' + finish + '\u2551')
    print('\t \u255A' + '\u2550' * (len(volumes) - 13) + '\u255D')
    print('\n')
    return DryRun.run_time


class DryRun:
    dry_run = False
    counter = 0
    run_time = 0
    buffer_volumes = [0, 0, 0, 0]

    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        if self.__class__.dry_run:
            DryRun.counter += 1
            kwargs['dry_run'] = True

            # find all occurrences of 'g.cset' in order to check if blocks exist
            source_code = inspect.getsource(self.f)
            pattern = r'g\.cset\((["\'])(.*?)\1,'
            matches = re.findall(pattern, source_code)
            absent_blocks = {block for block in [match[1] for match in matches] if g.cget(block) is None}
            if len(absent_blocks):
                # print("The following blocks were not found in config: ", absent_blocks)
                print("\033[1;31;40m>>The following blocks were not found in config: ", absent_blocks, "\033[0;0m")
            try:
                rt, summary = self.f(*args, **kwargs)
            except TypeError:
                rt = 0
                summary = "Only setup"

            # check contrast_change and add to total volume
            list_pattern = r'\[\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*\]'
            vol_pattern = r'\], (\d+)mL,'
            if self.f.__name__ == "contrast_change" or "inject":
                # print(args, '\n', kwargs)
                match_list = re.search(list_pattern, str(summary))
                match_vol = re.search(vol_pattern, str(summary))

                if match_list and match_vol:
                    vol = float(match_vol.group(1))
                    for i, conc in enumerate(match_list.group().strip('][').split(', ')):
                        self.buffer_volumes[i] += int(conc) * vol / 100
                else:
                    pass
                    # print('Error - contrast list not found')

            DryRun.run_time += rt
            newtime = datetime.now() + timedelta(minutes=DryRun.run_time)
            ETA = newtime.strftime("%H:%M")
            hours = str(int(DryRun.run_time / 60)).zfill(2)
            minutes = str(int(DryRun.run_time % 60)).zfill(2)

            tit = (args[0].title + " " + args[0].subtitle) if isinstance(args[0], Sample) else ""

            if self.counter <= 1:
                columns = ["No", "Action", "Title", "Parameters", "Script time", "ETA"]
                print(
                    f"{columns[0]:^2}|{columns[1]:^19}|{columns[2]:^47}|{columns[3]:^44}|{columns[4]:^14}|{columns[5]:^7}")
                now = datetime.now()
            if tit != "":
                # print(f'{DryRun.counter:02}', "Dry run: ",
                #       self.f.__name__, tit, args[1:], "-->|", hours + ":" + minutes, " hh:mm")
                arg = str(args[1:])
                print(f"{DryRun.counter:02}| {str(self.f.__name__)[:15]:17} "
                      f"| {tit[:43]:45} | {summary:39} -->| {hours:2}:{minutes:2}  hh:mm | {ETA}")
            else:
                pars = ''
                arglist = ''
                for a, arg in enumerate(inspect.getfullargspec(self.f)[0]):
                    if a < len(args):
                        print(arg, args[a])
                        arglist += str(arg) + ": " + str(args[a]) + "; "

                for key in kwargs:
                    if key != 'dry_run':
                        pars += str(key) + ": " + str(kwargs[key]) + "; "

                # print(f'{DryRun.counter:02}', "Dry run: ",
                #       self.f.__name__, kwargs, "-->|", hours + ":" + minutes, "hh:mm")
                print(f"{DryRun.counter:02}| {str(self.f.__name__)[:15]:17} | {arglist[:43]:45} | {pars:39} "
                      f"-->| {hours:2}:{minutes:2}  hh:mm | {ETA}")

            # print('\n=================================\n'
            #       'Volumes used for contrast changes:', self.buffer_volumes)

            # volumes = '\033[1;34;40m    Volumes used for contrast changes:' + \
            #           str(DryRun.buffer_volumes) + " mL \033[0;0m"

            # print(' \u2554' + '\u2550' * (len(volumes) - 11) + '\u2557')
            # print(' \u2551' + volumes + ' ' * 5 + '\u2551')
            # total_time = "=== Total time: " + str(int(DryRun.run_time / 60)) + "h " + str(
            #     int(DryRun.run_time % 60)) + "min ==="
            # left = int(len(volumes) / 2 - len(total_time))
            # right = len(volumes) - 20 - left - len(total_time)
            # print(' \u2551' + '    ' + ' ' * left + total_time + ' ' * right + ' ' * 5 + '\u2551')
            # print(' \u255A' + '\u2550' * (len(volumes) - 11) + '\u255D')
            # print('\n')
            return DryRun.run_time
        else:
            print("Running for real...")
            self.f(*args, **kwargs)


class RunActions:

    @staticmethod
    @DryRun
    def run_angle(sample, angle: float, count_uamps: float = None, count_seconds: float = None,
                  count_frames: float = None, vgaps: dict = None, hgaps: dict = None, mode: str = None,
                  dry_run: bool = False, include_gaps_in_title: bool = False, osc_slit: bool = False,
                  osc_block: str = 'Default', osc_gap: float = None, use_beam_blocker: bool = False,
                  s3_beam_blocker_offset: float = None, angle_for_s3_offset: float = None, s3_vgap: float = None,
                  ht_block: str = 'Default'):
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
            ht_block: height stage to be used for measurement. Defaults to stage defined for the sample.
            use_beam_blocker: Use slit 3 vertical gap in asymmetric/beam bloker mode. Requires additional parameters.
            s3_beam_blocker_offset: TBD  # TODO: tbd
            angle_for_s3_offset: TBD  # TODO: tbd
            s3_vgap: ???   # TODO: tbd
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
        # TODO: Add in some optional arguments to work with all S3 beam blocker modes
        # TODO: Streamline Run_angle to deal with all options.
        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({angle}, {count_uamps} uAmps)"  # value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({angle}, {count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({angle}, {count_frames} frames)"
        else:
            # print(colored("** Run angle {} **".format(sample.title), 'white', 'on_blue'))

            movement = _Movement(dry_run)

            mode_out = movement.setup_measurement(mode)  # TODO: make sure we're not in 'LIQUID' mode?

            movement.sample_setup(sample, angle, mode_out, trans_offset=None, ht_block=ht_block)

            if hgaps is None:
                hgaps = sample.hgaps
            movement.set_axis_dict(hgaps)
            movement.set_slit_vgaps(angle, vgaps, sample)

            # TODO: Once set_beam_blocker has been sorted out, change this do deal with different options
            if use_beam_blocker:
                movement.set_beam_blocker(angle, s3_beam_blocker_offset, angle_for_s3_offset, s3_vgap)

            movement.wait_for_move()
            new_title = movement.update_title(sample.title, sample.subtitle, angle,
                                              add_current_gaps=include_gaps_in_title)

            # TODO: Breaks if no count time set (ie setup only)
            # dur_dict = {'uamps': count_uamps, 'sec': count_seconds, 'frames': count_frames}
            # duration = [[dur_dict[dur], dur] for dur in dur_dict if dur_dict[dur] is not None][0]
            # logging.log(RUN, "{} | ** {}, th={}, {}={} **".
                        # format(str(g.get_runnumber()), sample.title, angle, duration[1], duration[0]))
            # TODO use 'coloredlogs' library

            movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps,
                                       hgaps)

    @staticmethod
    @DryRun  # TODO: remove b.KEYENCE, SM2, "HEIGHT"; FINE_HEIGHT_BLOCK should/could be the main height?
    def run_angle_SM(sample, angle, count_uamps=None, count_seconds=None, count_frames=None, vgaps: dict = None,
                     hgaps: dict = None, smangle=0.0, mode=None, do_auto_height=False, laser_offset_block="b.KEYENCE",
                     fine_height_block="HEIGHT", auto_height_target=0.0, continue_on_error=False, dry_run=False,
                     include_gaps_in_title=False, smblock: str = 'Default', osc_slit: bool = False,
                     osc_block: str = 'Default', osc_gap: float = None, ht_block: str = 'Default'):
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
            ht_block: height stage to be used for measurement. Defaults to stage defined for the sample.
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
        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({angle}, {count_uamps} uAmps)"  # value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({angle}, {count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({angle}, {count_frames} frames)"
        else:
            # print(colored("** Run angle {} **".format(sample.title), 'white', 'on_blue'))

            movement = _Movement(dry_run)

            mode_out = movement.setup_measurement(mode)
            smblock_out, smang_out = movement.sample_setup(sample, angle, mode_out, trans_offset=None, sm_ang=smangle)

            if do_auto_height:  # TODO: remove KEYNCE and HEIGHT and make generic
                movement.auto_height(laser_offset_block="KEYENCE", fine_height_block="HEIGHT",
                                     target=auto_height_target,
                                     continue_if_nan=continue_on_error, dry_run=dry_run)

            if hgaps is None:
                hgaps = sample.hgaps
            movement.set_axis_dict(hgaps)
            movement.set_slit_vgaps(angle, vgaps, sample)
            movement.wait_for_move()

            new_title = movement.update_title(sample.title, sample.subtitle, angle, smang_out, smblock_out,
                                              add_current_gaps=include_gaps_in_title)
            logging.log(RUN_SM,
                        "{} | ** {} th={} **".format(str(g.get_runnumber()), sample.title,
                                                     angle))  # TODO use 'coloredlogs' library

            movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps,
                                       hgaps)

    # TODO: Do we want to change the order of the arguments here?

    @staticmethod
    @DryRun
    def transmission(sample, title: str = None, vgaps: dict = None, hgaps: dict = None, count_uamps: float = None,
                     count_seconds: float = None, count_frames: float = None, height_offset: float = 0.0,
                     osc_slit: bool = True, osc_block: str = 'Default', osc_gap: float = None, mode: str = None,
                     at_angle: float = None, ht_block: str = 'Default', dry_run: bool = False,
                     include_gaps_in_title: bool = False):

        """
        Perform a transmission with both supermirrors removed.
        Args:
            sample (techniques.reflectometry.sample.Sample): The sample to measure
            title: Title to set
            vgaps: vertical gaps to be set; for each gap if not specified then determined for angle at_angle
            hgaps: horizontal gaps to be set; for each gap if not specified then remains unchanged
            count_seconds: time to count for in seconds
            count_uamps: number of micro amps to count for
            count_frames: number of frames to count for
            height_offset: Height offset from normal to set the sample to (positive offset lowers the sample)
            mode: mode to run in; None don't change mode
            dry_run: If True just print what would happen; If False, run the transmission
            include_gaps_in_title: Whether current slit gap sizes should be appended to the run title or not
            osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap extent setting.
                    Takes extent from equivalent gap Args if exists otherwise, goes into defaults in osc_slit_setup.
            osc_block: block to oscillate osc_gap: gap of slit during oscillation. If None then takes defaults (see
                    osc_slit_setup) at_angle: angle to calculate slit settings.
            ht_block specifies height stage to be used for transmission, will default to sample default.

        TODO: Need to update examples with oscillation. Add definitions of arguments.
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
        # REVIEW: updated osc_slit default to False (better to explicitly as it to do this?)
        # TODO: Add in a beamline constant to default to true or false oscillating slit gap.

        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({sample.title}, {count_uamps} uAmps)"  # TODO: value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({sample.title},{count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({sample.title},{count_frames} frames)"
        else:
            # print(colored("** Transmission {} **".format(title), 'light_red', attrs=['bold']))

            movement = _Movement(dry_run)
            mode_out = movement.setup_measurement(mode)

            with movement.reset_hgaps_and_sample_height_new(sample):
                movement.sample_setup(sample, 0.0, mode_out, height_offset)

                # if vgaps is None:
                #     vgaps = {}
                # if "S3VG" not in [gg.upper() for gg in vgaps.keys()]:
                #     vgaps.update({"S3VG": constants.s3max}) # TODO: remove constants somehow

                if hgaps is None:
                    hgaps = sample.hgaps
                movement.set_axis_dict(hgaps)
                movement.set_slit_vgaps(at_angle, vgaps, sample)
                # Edit for this to be an instrument default for the angle to be used in calc when vg not defined.
                movement.wait_for_move()

                # REVIEW: If no title is given, takes sample.title, otherwise, uses the string given.
                if title is not None:
                    new_title = movement.update_title(title, "", None, add_current_gaps=include_gaps_in_title)
                else:
                    new_title = movement.update_title(sample.title, "", None, add_current_gaps=include_gaps_in_title)

                logging.log(TRANS,
                            "{} | ** {} **".format(str(g.get_runnumber()), sample.title))  # TODO use 'coloredlogs' library

                movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap,
                                           vgaps,
                                           hgaps)

            # do stuff here


                # Horizontal gaps and height reset by with reset_gaps_and_sample_height

    # TODO: ht_block to default to main height
    # TODO: height_offset to default to TRANSMISSON_HEIGHT_OFFSET
    # TODO: Do we want to change the order of the arguments here?
    @staticmethod
    @DryRun
    def transmission_SM(sample, title: str, vgaps: dict = None, hgaps: dict = None,
                        count_uamps: float = None, count_seconds: float = None, count_frames: float = None,
                        height_offset: float = 0.0, smangle: float = 0.0,
                        mode: str = None, dry_run: bool = False, include_gaps_in_title: bool = True,
                        osc_slit: bool = True,
                        osc_block: str = 'Default', osc_gap: float = None, at_angle: float = None,
                        smblock: str = 'Default', ht_block: str = 'Default'):
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
            ht_block: height stage to be used for transmission. Defaults to stage associated with sample.

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
        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({sample.title}, {count_uamps} uAmps)"  # value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({sample.title},{count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({sample.title},{count_frames} frames)"
        else:
            # print(colored("** Transmission {} **".format(title), 'light_red', attrs=['bold']))

            movement = _Movement(dry_run)
            mode_out = movement.setup_measurement(mode)

            with _Movement.reset_hgaps_and_sample_height_new(movement, sample):

                smblock_out, smang_out = movement.sample_setup(sample, 0.0, mode_out, height_offset, smangle)

                # if vgaps is None:
                #     vgaps = {}
                # if "S3VG" not in [gg.upper() for gg in vgaps.keys()]:
                #     vgaps.update({"S3VG": constants.s3max}) # TODO: remove reference to constants
                if hgaps is None:
                    hgaps = sample.hgaps
                movement.set_axis_dict(hgaps)
                movement.set_slit_vgaps(at_angle, vgaps, sample)
                # Edit for this to be an instrument default for the angle to be used in calc when vg not defined.
                movement.wait_for_move()

                new_title = movement.update_title(title, "", None, smang_out, smblock_out,
                                                  add_current_gaps=include_gaps_in_title)

                logging.log(TRANS_SM,
                            "{} | ** {} **".format(str(g.get_runnumber()),
                                                   sample.title))  # TODO use 'coloredlogs' library

                movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap,
                                           vgaps, hgaps)

    @staticmethod
    @DryRun
    def run_angle_store(sample, angle: float, count_uamps: float = None, count_seconds: float = None,
                  count_frames: float = None, vgaps: dict = None, hgaps: dict = None, mode: str = None,
                  dry_run: bool = False, include_gaps_in_title: bool = False, osc_slit: bool = False,
                  osc_block: str = 'S2HG', osc_gap: float = None, store: bool = False, storerate: float = 120):
        """
        ** Function for testing store option.
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
            store: whether the run should regularly create a nxs file
            storerate: frequency of stored runs in seconds.
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

        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({angle}, {count_uamps} uAmps)"  # value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({angle}, {count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({angle}, {count_frames} frames)"
        else:
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

            movement.start_measurement_store(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps,
                                       hgaps, store, storerate)

# This means they can be typed directly into the IBEX python console:
# _runaction_instance = RunActions()
# run_angle = _runaction_instance.run_angle
# run_angle_SM = _runaction_instance.run_angle_SM
# transmission = _runaction_instance.transmission
# transmission_SM = _runaction_instance.transmission_SM

class SEActions:
    @staticmethod
    @DryRun
    def contrast_change(sample, concentrations, flow=1, volume=None, seconds=None, wait=False, dry_run=False):
        """
        Perform a contrast change.
        Args:
            sample: sample object with valve position to set for the Knauer valve
            concentrations: List of concentrations from A to D, e.g. [10, 20, 30, 40]
            flow: flow rate (as per device usually mL/min)
            volume: volume to pump; if None then pump for a time instead
            seconds: number of seconds to pump; if both volume and seconds set then volume is used
            wait: True wait for completion; False don't wait
            dry_run: True don't do anything just print what it will do; False otherwise
        """
        # TODO: Depreciate this for exposure to users, and just use inject.
        if dry_run:
            if isinstance(sample, int):
                valvepos = sample
                # print("** Contrast change for valve{} **".format(valvepos))
            elif isinstance(sample, Sample):
                valvepos = sample.valve
                # print("** Contrast change for valve{} **".format(valvepos))
            if wait and volume:
                return volume / flow, f"Line {valvepos}, {concentrations}, {volume}mL, {flow}mL/min"
            else:
                return 0, f"Line {valvepos}, {concentrations}, {volume}mL, {flow}mL/min"

        else:
            if isinstance(sample, int):
                valvepos = sample
                print("** Contrast change for valve{} **".format(valvepos))
            elif isinstance(sample, Sample):
                valvepos = sample.valve
                print("** Contrast change for valve{} **".format(valvepos))
            else:
                print("Incorrect form for valve - must be specified as integer or pre-defined sample")

            if len(concentrations) != 4:
                print("There must be 4 concentrations, you provided {}".format(len(concentrations)))
            sum_of_concentrations = sum(concentrations)
            if fabs(100 - sum_of_concentrations) > 0.01:
                print("Concentrations don't add up to 100%! {} = {}".format(concentrations, sum_of_concentrations))
            waiting = "" if wait else "NO "

            # print( "Concentration: Valve {}, concentrations {}, flow {},  volume {}, time {}, and {}waiting for
            # completion" .format(valvepos, concentrations, flow, volume, seconds, waiting) )

            # REVIEW: Added in catch for 2 valve setup, assuming HPLC is always plugged into valve3...
            # TODO: Change block names on all instruments for kanuer0/knauer2 to be the same name....
            try:
                g.cset("knauer2", 3)
            except:
                pass

            g.cset("knauer", valvepos)
            g.cset("Component_A", concentrations[0])
            g.cset("Component_B", concentrations[1])
            g.cset("Component_C", concentrations[2])
            # g.cset("Component_D", concentrations[3]) # JASCO MODIFICATION
            g.cset("hplcflow", flow)
            if volume is not None:
                g.cset("pump_for_volume", volume)
                g.cset("start_pump_for_volume", 1)
            elif seconds is not None:
                g.cset("pump_for_time", seconds)
                g.cset("start_pump_for_time", 1)
            else:
                print("Error concentration not set neither volume or time set!")
                return
            #g.waitfor_block("pump_is_on", "IDLE")
            g.waitfor_block("pump_is_on", "Pumping") # JASCO MODIFICATION

            logging.log(CONTRASTCHANGE,
                        "Valve {}, concentrations {}, flow {},  volume {}, time {}, and {}wait "
                        .format(valvepos, concentrations, flow, volume, seconds,
                                waiting))  # TODO use 'coloredlogs' library

            if wait:
                # g.waitfor_block("pump_is_on", "OFF")
                g.waitfor_block("pump_is_on", "Off") # JASCO MODIFICATION

    @staticmethod
    @DryRun
    def inject(sample, liquid, flow=1.0, volume=None, wait=False, dry_run=False):
        # TODO: Make this robust enough to work with one switch valve so that contrast change can be hidden away to
        #  remove options.
        if dry_run:
            if wait and volume:
                return volume / flow, f"Line {sample.valve}, {liquid}, {volume}mL, {flow}mL/min"
            else:
                return 0, f"Line {sample.valve}, {liquid}, {volume}mL, {flow}mL/min"

        else:
            if isinstance(sample, int):
                valvepos = sample
                print("** Contrast change for valve{} **".format(valvepos))
            elif isinstance(sample, Sample):
                valvepos = sample.valve
                print("** Contrast change for valve{} **".format(valvepos))
            else:
                valvepos = None
                print("Incorrect form for valve - must be specified as integer or pre-defined sample")

            if isinstance(liquid, list):
                try:
                    g.cset("KNAUER2", 3)  # set to take HPLC input from channel 3
                    g.waitfor_time(1)
                except Exception:
                    print("KNAUER2 not present, not a problem.")
                contrast_change(valvepos, liquid, flow=flow, volume=volume, wait=wait)
            elif isinstance(liquid, str) and liquid.upper() in ["SYRINGE_1", "SYRINGE_2"]:
                g.cset("KNAUER", valvepos)
                if liquid.upper() == "SYRINGE_1":
                    g.cset("KNAUER2", 1)
                    g.waitfor_time(1)
                    g.cset("Syringe_ID", 0)  # syringe A or 1
                elif liquid.upper() == "SYRINGE_2":
                    g.cset("KNAUER2", 2)
                    g.waitfor_time(1)
                    g.cset("Syringe_ID", 1)  # syringe B or 2
                # calculate time, set up the syringe parameters and start the injection
                inject_time = volume / flow * 60
                g.cset("Syringe_volume", volume)
                g.cset("Syringe_rate", flow)
                g.cset("Syringe_start", 1)

                waiting = "" if wait else "NO "
                logging.log(INJECT,
                            " {} valve {}, flow {},  volume {}, time {}, and {}wait"
                            .format(liquid, valvepos, flow, volume, inject_time, wait))  # TODO use 'coloredlogs' library

                if wait:
                    g.waitfor_time(inject_time + 2)
            else:
                print("Please specify either Syringe_1 or Syringe_2")
                # break

    @staticmethod
    @DryRun
    def go_to_pressure(pressure, speed=15.0, hold=True, wait=True, dry_run=False, maxwait=1 * 60 * 60):
        """
        Move barriers in order to reach a certain surface pressure.
        Args:
            pressure: The desired surface pressure in mN/m
            speed: Barrier speed in cm/min
            hold: hold pressure after reaching target; otherwise barriers will
                  not move, even if pressure changes
            wait: True wait to reach pressure; False don't wait
            dry_run: True don't do anything just print what it will do; False otherwise
            maxwait: Maximum wait time for reaching requested value in seconds. Use None to be endless. Default 1hr.
        """
        if dry_run:
            return 30, f"Target pressure {pressure}, hold={hold}, wait={wait}. Time only estimate."

        else:
            print(
                "** NIMA trough going to pressure = {} mN/m. Barrier speed = {} cm/min **".format(pressure, speed))
            movement = _Movement(dry_run)
            movement.dry_run_warning()

            g.cset("Speed", 0.0)  # set speed to 0 before going into run control

            g.cset("Nima_mode", "Pressure Control")  # 1 for PRESSURE control, 2 for AREA control
            g.cset("Control", "START")

            g.cset("Pressure", pressure)
            g.cset("Speed", speed)  # start barrie movement
            g.waitfor_block("Target_reached", "NO")
            if wait:
                g.waitfor_block("Target_reached", "YES", maxwait=maxwait)  # not sure what

            if not hold:
                g.cset("Speed", 0.0)  # set speed to 0 to stop barriers moving; pressure may change

    @staticmethod
    @DryRun
    def go_to_area(area, speed=15.0, wait=True, dry_run=False, maxwait=1 * 60 * 60):
        """
        Move barriers in order to reach a certain area
            area: The target area in cm^2
            speed: Barrier speed in cm/min
            wait: True wait to reach target area; False don't wait
            dry_run: True don't do anything just print what it will do; False otherwise
            maxwait: Maximum wait time for reaching requested value in seconds. Use None to be endless. Default 1hr.
        """
        if dry_run:  # TODO: we could interrogate the current area, subtract from target area and divide by speed
            return 10, f"Target area {area}, barrier speed {speed}, wait={wait}. Time only estimate."

        else:
            print("** NIMA trough going to area = {} cm^2. Barrier speed = {} cm/min **".format(area, speed))
            movement = _Movement(dry_run)
            movement.dry_run_warning()

            g.cset("Speed", 0.0)  # set speed to 0 before going into run control

            g.cset("Nima_mode", "Area Control")  # 1 for PRESSURE control, 2 for AREA control
            g.cset("Control", "START")

            g.cset("Area", area)
            g.cset("Speed", speed)  # start barrier movement
            g.waitfor_block("Target_reached", "NO")
            if wait:
                g.waitfor_block("Target_reached", "YES", maxwait=maxwait)  # not sure what

            g.cset("Speed", 0.0)  # set speed to 0 to stop barriers moving; pressure may change


def autoheight(laser_offset_block: str = 'KEYENCE', fine_height_block: str = 'HEIGHT', target: float = 0.0,
               settle_time=0):
    """
    Version for in console window.
    Moves the sample fine height axis so that it is centred on the beam, based on the readout of a laser height gun.

    Args:
        laser_offset_block: The name of the block for the laser offset from centre
        fine_height_block: The name of the block for the sample fine height axis
        target: The target laser offset

        >>> auto_height(b.KEYENCE, b.HEIGHT2)

        Moves HEIGHT2 by (KEYENCE * (-1))

        >>> auto_height(b.KEYENCE, b.HEIGHT2, target=0.5, continue_if_nan=True)

        Moves HEIGHT2 by (target - b.KEYENCE) and does not interrupt script execution if an invalid value is read.
    """
    g.waitfor_time(seconds=settle_time)
    current_laser_offset = g.cget(laser_offset_block)["value"]
    difference = target - current_laser_offset

    current_height = g.cget(fine_height_block)["value"]
    target_height = current_height + difference

    print("Target for fine height axis: {} (current {})".format(target_height, current_height))

    g.cset(fine_height_block, target_height)
    g.waitfor_move()


# THIS MAY BECOME REDUNDANT.
def slit_check(theta, footprint, resolution):
    """
    Check the slits values
    Args:
        theta: theta
        footprint: desired footprint
        resolution:  desired resolution

    """

    movement = _Movement(True)
    calc_dict = movement.calculate_slit_gaps(theta, footprint, resolution)
    print("For a footprint of {} and resolution of {} at an angle {}:".format(footprint, resolution, theta))
    print(calc_dict)


# This means they can be typed directly into the IBEX python console:
_SEaction_instance = SEActions()
contrast_change = _SEaction_instance.contrast_change
inject = _SEaction_instance.inject
go_to_pressure = _SEaction_instance.go_to_pressure
go_to_area = _SEaction_instance.go_to_area
