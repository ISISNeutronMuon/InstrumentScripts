import sys
from collections import OrderedDict
from contextlib2 import contextmanager
# from termcolor import colored

from future.moves import itertools
from math import tan, radians, sin

from six.moves import input

import logging

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g

# import general.utilities.io
from .sample import Sample
from .instrument_constants import get_instrument_constants ##TODO: need to update import

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
        special_axes = ['HEIGHT2']  #left explicit for now as true for all but could be changed to instrument constants
        if axis.upper() in special_axes and not constants.has_height2:
            # print(colored("ERROR: Height 2 offset is being ignored", "red"))
            logging.error("Height 2 offset is being ignored")
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

    def get_gaps(self, vertical: bool, centres: bool = False, slitrange: list = None):
        """
        :param vertical: True for vertical gaps; False for Horizontal gaps
        :param centres: True to return centres; False to return gaps
        :param slitrange: string list to iterate over (index of slits)
        :return: dictionary of gaps
        """
        v_or_h = "V" if vertical else "H"
        g_or_c = "C" if centres else "G"
        gaps = {}
        if slitrange is not None:
            for slit_num in slitrange:
                gap_pv = "S{}{}{}".format(slit_num, v_or_h, g_or_c)
                gaps[gap_pv.lower()] = self._get_block_value(gap_pv)
        else:
            print("No list of slit indices provided. Gaps not set.")
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

    def update_title(self, title, subtitle, theta, smangle=None, smblock=constants.smblock, add_current_gaps=False):
        """
        Update the current title with or without gaps if not in dry run
        :param title: title to set
        :param subtitle: sub title to set
        :param theta: theta for the experiment
        :param smangle: sm angle; if None it doesn't appear in the title
        :param smblock: prefix appended to title for specifying supermirror
        :param add_current_gaps: current gaps
        """
        new_title = "{} {}".format(title, subtitle)

        if theta is not None:
            new_title = "{} th={:.4g}".format(new_title, theta)
        else:
            new_title = "{} transmission".format(new_title)
        if smangle is not None:
            new_title = "{} {}={:.4g}".format(new_title, smblock, smangle)

        if add_current_gaps:
            vgaps = self.get_gaps(vertical=True, slitrange=constants.vslits)
            hgaps = self.get_gaps(vertical=False, slitrange=constants.hslits)
            for i, k in vgaps.items():
                new_title = "{} {}={:.4g}".format(new_title, i, k)
            for i, k in hgaps.items():
                new_title = "{} {}={:.3g}".format(new_title, i, k)

        if self.dry_run:
            g.change_title(new_title)
            print("New Title: {}".format(new_title))
        else:
            g.change_title(new_title)
        return new_title

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
        ## TODO: Add None handling for when s1s2 and s2sa are not properly defined.

        factor = theta / constants.max_theta
        s3 = constants.s3max * factor
        calc_dict.update({'S3VG': s3})

        g.cset('S3VC', 0)
        self.wait_for_move()

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
        if constants.s1s2 is None or constants.s2sa is None or theta is None:
            print("Warning: Default instrument constants not provided. Check s1s2, s1sa distances and trans_angle.")
            return None
        else:
            s1sa = constants.s1s2 + constants.s2sa
            footprint_at_theta = footprint * sin(radians(theta))
            s1 = 2 * s1sa * tan(radians(resolution * theta)) - footprint_at_theta
            s2 = (constants.s1s2 * (footprint_at_theta + s1) / s1sa) - s1
            if s2 > s1:
                print("Warning: Calculation gives s2vg larger than s1vg. The script will continue.")
            elif s1 < 0 or s2 < 0:
                raise ValueError("The slit calculation gives a negative gap. Check the footprint and resolution values.")
            return {'S1VG': s1, 'S2VG': s2}

    # Horizontal gaps and height reset by with reset_gaps_and_sample_height
    # Added extra part for centres too.
    @contextmanager
    def reset_hgaps_and_sample_height_new(self, sample, constants):
        """
        After the context is over reset the gaps back to the value before and set the height to the default sample height.
        Edited to reset the gap centres too.
        If keyboard interrupt give options for what to do.
        Args:
            movement(_Movement): object that does movement required (or pronts message for a dry run)
            sample: sample to get the sample offset from
            constants: instrument constants

        """
        horizontal_gaps = self.get_gaps(vertical=False, centres=False, slitrange=constants.hslits)
        horizontal_cens = self.get_gaps(vertical=False, centres=True, slitrange=constants.hslits)

        def _reset_gaps():
            print("Reset horizontal centres to {}".format(list(horizontal_cens.values())))
            self.set_axis_dict(horizontal_cens)
            print("Reset horizontal gaps to {}".format(list(horizontal_gaps.values())))
            self.set_axis_dict(horizontal_gaps)
            # TODO join the above together?

            self.set_axis(sample.ht_block, sample.height_offset, constants)
            self.set_axis("HEIGHT2", sample.height2_offset, constants) #only operates if has_height2 True so can be left like this.
            #TODO: check ok with POLREF - probably need sample.height2_offset default to 0.
            self.wait_for_move()

        try:
            yield
            _reset_gaps()
        except KeyboardInterrupt:
            running_on_entry = not self.is_in_setup()
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
                print("Setting horizontal slit gaps to pre-transmission values.")
                _reset_gaps()

            elif choice.upper() == "E":
                if running_on_entry:
                    g.end()
                _reset_gaps()

            elif choice.upper() == "K":
                print("Continuing counting, remember to set back horizontal slit gaps when the run is ended.")
                if running_on_entry:
                    g.resume()

            self.wait_for_seconds(5)
            print("\n\n PRESS ctl + c to get the prompt back \n\n")  # This is because there is a bug in pydev
            raise  # reraise the exception so that any running script will be aborted

    def change_to_soft_period_count(self, count=constants.periods):
        """
        Change the number of soft periods if not in dry run
        :param count: number of periods
        """
        if count is None:
            print("Periods not changed as no default periods set in instrument constants.")
        elif not self.dry_run:
            g.change_number_soft_periods(count)
        else:
            print("Number of periods set to {}".format(count))

    def wait_for_move(self):
        """
        Wait for a move if not in dry run
        """
        if not self.dry_run:
            g.waitfor_move()

    def set_smangle_if_not_none(self, smangle, smblock=constants.smblock):
        """
        Set the super mirror angle and put it in the beam if not None and not dry run
        :param smangle: super mirror angle; None for do not set and leave it where it is
        :type smangle: float
        :param smblock: block to be set. Expect 'SM2' or 'SM1' (or 'SM' for non-INTER).
        :type smblock: str
        """
        if smangle is not None and smblock is not None:
            is_in_beam = "IN" if smangle > 0.0001 else "OUT"
            print("{} angle (in beam?): {} ({})".format(smblock, smangle, is_in_beam))
            if not self.dry_run:
                g.cset("{}INBEAM".format(smblock), is_in_beam)
                if smangle > 0.0001:
                    g.cset("{}ANGLE".format(smblock), smangle)
        elif smblock is None and smangle is not None:
            print("Supermirror not set as block name not provided. Check instrument constants.")

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

    def _check_if_done(self, count_uamps: float = None, count_seconds: float = None, count_frames: float = None):
        """
        Checks if the counting condition has been met. If it hasn't, returns False and if it has, returns True.
        Counting condition can be specified as uamps, seconds or frames.

        If multiple counts are non-zero then will take first non-zero in order uamps, seconds, frames.
        Args:
            count_uamps: number of uamps to count for; None=count in a different way
            count_seconds: number of seconds to count for; None=count in a different way
            count_frames: number of frames to count for; None=count in a different way
        """
        stop = False
        finish_condition = None
        if count_uamps is not None:
            finish_condition = count_uamps
            counter = g.get_uamps()
        elif count_seconds is not None:
            finish_condition = count_seconds
            counter = g.get_time_since_begin(False)
        elif count_frames is not None:
            finish_condition = count_frames
            counter = g.get_frames()
        else:
            print("Counts in uamps, seconds or frames must be defined.")
            counter = None

        if finish_condition is not None and counter >= finish_condition:
            stop = True
        return stop

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

        if not self.dry_run:
            if c_min < c_max:
                g.begin()
                stop_test = self._check_if_done(count_uamps, count_seconds, count_frames)
                # print(current_counts)
                while stop_test is False:
                    g.cset(c_block, c_min)
                    g.waitfor_block(c_block, c_min, maxwait=40)
                    g.waitfor_time(seconds=1)  ##use sleep or remove?
                    g.cset(c_block, c_max)
                    g.waitfor_block(c_block, c_max, maxwait=40)
                    g.waitfor_time(seconds=1)
                    stop_test = self._check_if_done(count_uamps, count_seconds, count_frames)
                    ###print("Continuing run, counts at {}={}".format(count_choice_idx, current_counts))
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
        Args:
            slit_block: block of slit to oscillate
            slit_gap: gap of slit during oscillation
            slit_extent: range of oscillation movement

        Returns: block to be used as the centre point, prior centre point for resetting, min and max of movement.
        """
        HG_defaults = constants.hg_defaults
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

    def setup_measurement(self, mode=None, periods=constants.periods):
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
        ##TODO: this constants path might need changing depending how constants setup. Does it need to be set separately here?
        if periods is not None:
            self.change_to_soft_period_count(count=periods)
        else:
            print("Periods not changed as no default periods set in instrument constants.")
        try:
            g.cset("MONITOR", "IN")
        except:
            print("Monitor not found")

        mode_out = self.change_to_mode_if_not_none(mode)
        print("Mode {}".format(mode_out))
        return constants, mode_out

    def sample_setup(self, sample, angle, inst_constants, mode, trans_offset=0.0, smang=0.0, smblock=constants.smblock,
                     ht_block=sample.ht_block):
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
            smblock: supermirror blocks to use, can be a list for multiple mirrors. Defaults to entry in instrument constants file.
            ht_block: motor to be used for height movement. If height offset greater than instrument-specific maximum height offset then height2 is used.
        """
        #TODO: check special mode label on SURF.
        self.set_axis("TRANS", sample.translation, constants=inst_constants)
        smblock_out, smang_out = self._SM_setup(angle, inst_constants, smang, smblock, mode)
        self.set_axis("THETA", angle, constants=inst_constants)
        self.wait_for_move()
        if mode.upper() != "LIQUID":
            self.set_axis("PSI", sample.psi_offset, constants=inst_constants)
            self.set_axis("PHI", sample.phi_offset + angle, constants=inst_constants)
        if inst_constants.has_height2:
            if angle == 0 and abs(trans_offset) > constants.max_fine_trans:  # i.e. if transmission
                self.set_axis("HEIGHT2", sample.height2_offset - trans_offset, constants=inst_constants)
                self.set_axis(ht_block, sample.height_offset, constants=inst_constants)
            else:
                self.set_axis("HEIGHT2", sample.height2_offset, constants=inst_constants)
                self.set_axis(ht_block, sample.height_offset - trans_offset, constants=inst_constants)
        else:
            self.set_axis(ht_block, sample.height_offset - trans_offset, constants=inst_constants)
        self.wait_for_move()
        return smblock_out, smang_out

    def _SM_setup(self, angle, inst_constants, smangle=0.0, smblock=constants.smblock, mode=None):
        """
        Setup mirrors in and out of beam and at correct angles.
        Args:
            angle: theta value for calculation
            inst_constants: instrument constants for natural beam angle
            smangle: mirror angle to use, default to 0.0 to be out of beam (overwritten if liquid mode)
            smblock: axis for mirror, can be a list for multiple mirrors. Defaults to entry in instrument constants file.
            mode: flag for liquid mode where smangle is determined from angle instead
        """
        if smblock is None and smangle != 0.0:
            print("Supermirror not set as no block name provided. Check instrument constants file.")
            smang = smangle
        else:
            protect_modes = ["LIQUID", "OIL-WATER"]
            #TODO: check this mode matches on SURF.
            if mode.upper() in protect_modes and angle != 0.0:
                # In liquid the sample is tilted by the incoming beam angle so that it is level, this is accounted for by
                # adjusting the super mirror
                smang = (inst_constants.incoming_beam_angle - angle) / 2
            else:
                smang = smangle
            # TODO: Need to change the except statement to an error/warning?
            SM_defaults = constants.smdefaults
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
                          osc_slit: bool = False, osc_block: str = constants.oscblock, osc_gap: float = None, vgaps: dict = None,
                          hgaps: dict = None):
        """
        Starts a measurement based on count inputs and oscillating inputs.
        Args:
            count_uamps: the current to run the measurement for; None for use count_seconds
            count_seconds: the time to run the measurement for if uamps not set; None for use count_frames
            count_frames: the number of frames to wait for; None for don't count
            osc_slit: whether slit oscillates during measurement; only osc if osc_gap < total gap extent setting.
            osc_block: block to oscillate. Defaults to value from instrument constants file.
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

    def auto_height(self, laser_offset_block: str, fine_height_block: str = sample.ht_block, target: float = 0.0,
                    continue_if_nan: bool = False,
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
            target_height, current_height = self._calculate_target_auto_height(laser_offset_block, fine_height_block,
                                                                               target)
            if not dry_run:
                g.cset(fine_height_block, target_height)
                self._auto_height_check_alarms(fine_height_block)
                g.waitfor_move()
        except TypeError as e:
            prompt_user = not (continue_if_nan or dry_run)
            general.utilities.io.alert_on_error("ERROR: cannot set auto height (invalid block value): {}".format(e),
                                                prompt_user)

    def _auto_height_check_alarms(self, fine_height_block):
        """
        Checks whether a given block for the fine height axis is in alarm after a move and sends an alert if not.

        Args:
            fine_height_block: The name of the fine height axis block
        """
        alarm_lists = g.check_alarms(fine_height_block)
        if any(fine_height_block in alarm_list for alarm_list in alarm_lists):
            general.utilities.io.alert_on_error(
                "ERROR: cannot set auto height (target outside of range for fine height axis?)", True)

    def _calculate_target_auto_height(self, laser_offset_block, fine_height_block, target):
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

    def set_beam_blocker(self, angle, constants, s3_beam_blocker_offset, angle_for_s3_offset, vgap):
        '''
        Sets up the bottom blade of slit 3 as a beam blocker to block the direct beam.

        Args:
            angle: current theta position, used for scaling the position of S3S
            contants: Pulls in the instrument constants from constants.py
            s3_beam_blocker_offset: The nominal offset of S3South. If None, will take value from instrument constants.
            angle_for_s3_offset: The angle at which s3_beam_blocker_offset will block the direct beam, used for scaling the position of S3S
                                 If None, will take value from instrument constants.
            vgap: S3vg before S3South is moved in.

        '''
        # REVIEW: Check compatibility with other instruments
        # TODO: Add in three S3 modes:
        #        - normal tracking gap
        #        - blocking direct beam (plus flare) to a certain definable extent (change this function to drive the individual blades, a la POLREF)
        #        - lower blade only at scaling gap, top blade wide open
        # TODO: Need two default parameters in constants.py to deal with this 'maximum s3 gap' and the original use for s3max
        offset = s3_beam_blocker_offset if s3_beam_blocker_offset is not None else constants.s3_beam_blocker_offset
        nominal_angle = angle_for_s3_offset if angle_for_s3_offset is not None else constants.angle_for_s3_offset
        vgap = vgap if vgap is not None else constants.s3max

        s3s_value = abs(offset * angle / nominal_angle)*(-1)

        g.cset("S3VC", 0)
        # self.wait_for_move()
        g.waitfor_move()
        g.cset("S3VG", vgap) # TODO: Change so directly drive S3N... g.cset('S3North', vgap / 2)
        g.waitfor_move()
        g.cset("S3South", s3s_value)


