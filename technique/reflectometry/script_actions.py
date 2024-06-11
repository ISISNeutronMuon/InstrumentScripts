from datetime import datetime, timedelta
from contextlib2 import contextmanager
from datetime import datetime
from future.moves import itertools
from math import tan, radians, sin, fabs

from six.moves import input

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g

# import general.utilities.io
from .sample import Sample, SampleGenerator
from .NR_motion import _Movement
from .instrument_constants import get_instrument_constants


class DryRun:
    dry_run = False
    counter = 0
    run_time = 0

    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        if self.__class__.dry_run:
            DryRun.counter += 1
            kwargs['dry_run'] = True
            rt, summary = self.f(*args, **kwargs)

            DryRun.run_time += rt
            newtime = datetime.now() + timedelta(minutes=DryRun.run_time)
            ETA = newtime.strftime("%H:%M")
            hours = str(int(DryRun.run_time / 60)).zfill(2)
            minutes = str(int(DryRun.run_time % 60)).zfill(2)
            tit = args[0].title if isinstance(args[0], Sample) else ""
            if self.counter <= 1:
                columns = ["No", "Action", "Title", "Parameters", "Elapsed time", "ETA"]
                print(
                    f"{columns[0]:^3}|{columns[1]:^17}|{columns[2]:^45}|{columns[3]:^34}|{columns[4]:^14}|{columns[5]:^7}")
                now = datetime.now()
            if tit != "":
                # print(f'{DryRun.counter:02}', "Dry run: ",
                #       self.f.__name__, tit, args[1:], "-->|", hours + ":" + minutes, " hh:mm")
                arg = str(args[1:])
                print(f"{DryRun.counter:02}: {str(self.f.__name__)[:15]:17} "
                      f"{tit[:43]:45} {summary:30} -->| {hours:2}:{minutes:2}  hh:mm | {ETA}")
            else:
                # print(f'{DryRun.counter:02}', "Dry run: ",
                #       self.f.__name__, kwargs, "-->|", hours + ":" + minutes, "hh:mm")
                print(f"{DryRun.counter:02} Dry run: {self.f.__name__} {kwargs[50]:52} "
                      f"-->| {hours:2}:{minutes:2} hh:mm")
        else:
            print("Running for real...")
            self.f(*args, **kwargs)


class RunActions:
    
    @staticmethod
    @DryRun
    def run_angle(sample, angle: float, count_uamps: float = None, count_seconds: float = None,
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

            movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps,
                                       hgaps)

    @staticmethod
    @DryRun
    def run_angle_SM(sample, angle, count_uamps=None, count_seconds=None, count_frames=None, vgaps: dict = None,
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
            smblock_out, smang_out = movement.sample_setup(sample, angle, constants, mode_out, smang=smangle,
                                                           smblock=smblock)

            if do_auto_height:
                movement.auto_height(laser_offset_block="KEYENCE", fine_height_block="HEIGHT", target=auto_height_target,
                                      continue_if_nan=continue_on_error, dry_run=dry_run)
                g.waitfor_time(seconds=2)
                movement.auto_height(laser_offset_block="KEYENCE", fine_height_block="HEIGHT", target=auto_height_target,
                                      continue_if_nan=continue_on_error, dry_run=dry_run)

            if hgaps is None:
                hgaps = sample.hgaps
            movement.set_axis_dict(hgaps)
            movement.set_slit_vgaps(angle, constants, vgaps, sample)
            movement.wait_for_move()

            movement.update_title(sample.title, sample.subtitle, angle, smang_out, smblock_out,
                                  add_current_gaps=include_gaps_in_title)

            movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps, hgaps)

    # TODO: Do we want to change the order of the arguments here?

    @staticmethod
    @DryRun
    def transmission(sample, title: str, vgaps: dict = None, hgaps: dict = None, count_uamps: float = None,
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
        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({sample.title}, {count_uamps} uAmps)"  # value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({sample.title},{count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({sample.title},{count_frames} frames)"
        else:
            print("** Transmission {} **".format(title))

            movement = _Movement(dry_run)
            constants, mode_out = movement.setup_measurement(mode)

            with movement.reset_hgaps_and_sample_height_new(sample, constants):
                movement.sample_setup(sample, 0.0, constants, mode_out, height_offset)

                if vgaps is None:
                    vgaps = {}
                if "S3VG" not in [g.upper() for g in vgaps.keys()]:
                    vgaps.update({"S3VG": constants.s3max})

                if hgaps is None:
                    hgaps = sample.hgaps
                movement.set_axis_dict(hgaps)
                movement.set_slit_vgaps(at_angle, constants, vgaps, sample)
                # Edit for this to be an instrument default for the angle to be used in calc when vg not defined.
                movement.wait_for_move()

                movement.update_title(title, "", None, add_current_gaps=include_gaps_in_title)
                movement.start_measurement(count_uamps, count_seconds, count_frames, osc_slit, osc_block, osc_gap, vgaps,
                                           hgaps)

                # Horizontal gaps and height reset by with reset_gaps_and_sample_height

    # TODO: Do we want to change the order of the arguments here?
    @staticmethod
    @DryRun
    def transmission_SM(sample, title: str, vgaps: dict = None, hgaps: dict = None,
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
        if dry_run:
            if count_uamps:
                return count_uamps / 40 * 60, f"({sample.title}, {count_uamps} uAmps)"  # value for TS2, needs instrument check
            elif count_seconds:
                return count_seconds / 60, f"({sample.title},{count_seconds} s)"
            elif count_frames:
                return count_frames / 36000, f"({sample.title},{count_frames} frames)"
        else:
            print("** Transmission {} **".format(title))

            movement = _Movement(dry_run)
            constants, mode_out = movement.setup_measurement(mode)

            with _Movement.reset_hgaps_and_sample_height_new(movement, sample, constants):

                smblock_out, smang_out = movement.sample_setup(sample, 0.0, constants, mode_out, height_offset, smangle,
                                                               smblock)

                if vgaps is None:
                    vgaps = {}
                if "S3VG" not in [g.upper() for g in vgaps.keys()]:
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
        
        if dry_run:
            if isinstance(sample, int):
                valvepos = sample
                print("** Contrast change for valve{} **".format(valvepos))
            elif isinstance(sample, Sample):
                valvepos = sample.valve
                print("** Contrast change for valve{} **".format(valvepos))
            if wait and volume:
                return volume/flow, f"Line {valvepos}, {concentrations}, {volume}mL, {flow}mL/min"
            else:
                return 0, f"Line {valvepos}, {concentrations}, {volume}mL, {flow}mL/min"

        else:
            if isinstance(sample, int):
                print('Here')
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
            waiting = "" if wait else "NOT "

            print("Concentration: Valve {}, concentrations {}, flow {},  volume {}, time {}, and {}waiting for completion"
                  .format(valvepos, concentrations, flow, volume, seconds, waiting))


            g.cset("knauer", valvepos)
            g.cset("Component_A", concentrations[0])
            g.cset("Component_B", concentrations[1])
            g.cset("Component_C", concentrations[2])
            #g.cset("Component_D", concentrations[3])
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
            g.waitfor_block("pump_is", "Pumping")

            if wait:
                g.waitfor_block("pump_is", "Off")

    @staticmethod
    @DryRun
    def inject(sample, liquid, flow=1.0, volume=None, wait=False, dry_run=False):
        if dry_run:
            if wait and volume:
                return volume/flow, f"Line {sample.valve}, {liquid}, {volume}mL, {flow}mL/min"
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
                print("Incorrect form for valve - must be specified as integer or pre-defined sample")

            if isinstance(liquid, list):
                g.cset("KNAUER2",3) # set to take HPLC input from channel 3
                g.waitfor_time(1)
                contrast_change(valvepos, liquid, flow=flow, volume=volume, wait=wait)
            elif isinstance(liquid,str) and liquid.upper() in ["SYRINGE_1", "SYRINGE_2"]:
                g.cset("KNAUER",valvepos)
                if liquid.upper() == "SYRINGE_1":
                    g.cset("KNAUER2",1)
                    g.waitfor_time(1)
                    g.cset("Syringe_ID",0) # syringe A or 1
                elif liquid.upper() == "SYRINGE_2":
                    g.cset("KNAUER2",2)
                    g.waitfor_time(1)
                    g.cset("Syringe_ID",1) # syringe B or 2 
                # calculate time, set up the syringe parameters and start the injection
                inject_time = volume / flow * 60
                g.cset("Syringe_volume", volume)
                g.cset("Syringe_rate", flow)
                g.cset("Syringe_start",1)

                if wait:
                    g.waitfor_time(inject_time + 2)
            else:
                print("Please specify either Syringe_1 or Syringe_2")
                    #break

    @staticmethod
    @DryRun
    def go_to_pressure(pressure, speed=15.0, hold=True, wait=True, dry_run=False, maxwait=1*60*60):
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
        print("** NIMA trough going to pressure = {} mN/m. Barrier speed = {} cm/min **".format(pressure, speed))
        # need to add dryrun part.
        #movement = _Movement(dry_run)
        #movement.dry_run_warning()
        
        g.cset("Speed", 0.0) # set speed to 0 before going into run control
        
        g.cset("Nima_mode", "Pressure Control")  # 1 for PRESSURE control, 2 for AREA control
        g.cset("Control", "START")

        g.cset("Pressure", pressure)
        g.cset("Speed", speed) # start barrie movement
        g.waitfor_block("Target_reached", "NO")
        if wait:
            g.waitfor_block("Target_reached", "YES", maxwait=maxwait) # not sure what
            
        if not hold:
            g.cset("Speed", 0.0) # set speed to 0 to stop barriers moving; pressure may change

    @staticmethod
    @DryRun
    def go_to_area(area, speed=15.0, wait=True, dry_run=False, maxwait=1*60*60):
        """
        Move barriers in order to reach a certain area
            area: The target area in cm^2
            speed: Barrier speed in cm/min
            wait: True wait to reach target area; False don't wait
            dry_run: True don't do anything just print what it will do; False otherwise
            maxwait: Maximum wait time for reaching requested value in seconds. Use None to be endless. Default 1hr.
        """
        print("** NIMA trough going to area = {} cm^2. Barrier speed = {} cm/min **".format(area, speed))
        #need to add dry run part.
        #movement = _Movement(dry_run)
        #movement.dry_run_warning()

        g.cset("Speed", 0.0)  # set speed to 0 before going into run control

        g.cset("Nima_mode", "Area Control")  # 1 for PRESSURE control, 2 for AREA control
        g.cset("Control", "START")

        g.cset("Area", area)
        g.cset("Speed", speed)  # start barrier movement
        g.waitfor_block("Target_reached", "NO")
        if wait:
            g.waitfor_block("Target_reached", "YES", maxwait=maxwait)  # not sure what

        g.cset("Speed", 0.0)  # set speed to 0 to stop barriers moving; pressure may change
        


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
    print("For a footprint of {} and resolution of {} at an angle {}:".format(footprint, resolution, theta))
    print(calc_dict)

# This means they can be typed directly into the IBEX python console:
_SEaction_instance = SEActions()
contrast_change = _SEaction_instance.contrast_change
inject = _SEaction_instance.inject
go_to_pressure = _SEaction_instance.go_to_pressure
go_to_area = _SEaction_instance.go_to_area
