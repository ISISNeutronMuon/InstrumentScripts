# -*- coding: utf-8 -*-
"""The baseline for loading a scanning instrument

Each instrument will have its own module that declares a class
inheriting from ScanningInstrument.  The abstract base class is used
to ensure that the derived classes define the necessary methods to run
any generic scripts.

"""

from abc import ABCMeta, abstractmethod
import ast
import csv
from logging import info, warning
import os.path
from six import add_metaclass
from .genie import gen
from .util import user_script


def _get_times(times):
    for k in ["uamps", "frames", "hours", "minutes", "seconds"]:
        if k in times:
            return k, times[k]
    raise ValueError("No valid time found")


@add_metaclass(ABCMeta)
# pylint: disable=too-many-public-methods
class ScanningInstrument(object):
    """
    The base class for scanning measurement instruments.

    This class can be extended for specific instruments with
    instrument specific implementations of abstract methods
    and overriding of any methods that need instrument specific
    implementations.

    If you would like to create custom implementations of
    begin/waitfor/end function beyond calling gen.begin you can
    define custom function within the instruments script files.

    The function names should end with name of the dae_mode
    that the custom implementation is used for. For example if
    you want a custom begin/waitfor/end for setup_dae_transmission
    then the functions begin_transmission, waitfor_transmission,
    end_transmission will need to be created. If you wish to create
    a new dae_mode then follow the pattern of other dae_mode,
    you must tag the dae mode with the decorator @dae_setter (see dae_setter)
    for more details.

    Attributes
    ----------
    title_footer : str
        Footer appended to the experiment title. This is set through
        dae_setter a function called when setting the dae_mode
    """

    # Property to indicate if a custom dae mode is being used.
    # Used to indicate if a custom begin/wait/end functions should be used
    _dae_mode = None

    _detector_lock = False
    title_footer = ""
    _TIMINGS = ["uamps", "frames", "seconds", "minutes", "hours"]
    # Methods to ignore in method_iterator
    _block_accessors = ["changer_pos_dls", "changer_pos", "method_iterator"]

    _tables_path = ""

    _poslist_dls = []

    def __init__(self):
        sample_positions = self.get_pv("LKUP:SAMPLE:POSITIONS")
        if sample_positions is not None:
            self._poslist = sample_positions.split()
        else:
            warning("Sample positions from PV not available - using default poslist, which may be incorrect.")
        self.setup_sans = self.setup_dae_event
        self.setup_trans = self.setup_dae_transmission

    def method_iterator(self):
        """Iterate through the class's public functions"""
        for method in dir(self):
            if method[0] != "_" and method not in locals() and \
               method not in self._block_accessors and \
               callable(getattr(self, method)):
                yield method

    def set_default_dae(self, mode=None, trans=False):
        """Set the default DAE mode for SANS or TRANS measurements.

        Parameters
        ----------
        mode : str
          The mode is a string, call the function whose name
          is "setup_dae_<mode>" followed by that string.
          You can find a full list of setup_dae_<name> by calling
          enumerate_dae() on the instrument.
        trans : bool
          If true, set the default transmission instead of the default
          SANS mode.

        """
        if mode is None:
            pass
        else:
            try:
                if trans:
                    self.setup_trans = getattr(self, "setup_dae_" + mode)
                else:
                    self.setup_sans = getattr(self, "setup_dae_" + mode)
            except AttributeError:
                print(f"No dae called 'setup_dae_{mode}', "
                      f"you can use setup_dae_custom to create custom daes")

    # I don't like that users can parse any function to create DAE that's sounds bad
    # This would give up some more control over the function that they set but would
    # take away there freedom.
    def create_dae_custom(self, detector, spectra, wiring, tcb, trans):
        """
        A function for setting the default dae with custom
        value for the detector, spectra and wiring tables
        By providing the respective paths and tcb it will
        set up the dae with these parameters.

        This method is intended for the creation of one off
        dae's if you wish to create a new dae configuration
        they should be defined in the instruments script file.

        To create a new dae setup open the instrument file for
        instance Script/instrument/larmor/sans.py. Create a new
        method with the following the naming convention and be
        sure to tag it with the @set_metadata decorator:

        >>> @dae_setter("SANS", "sans")
        >>> def setup_dae_newmode(self):

        You can then define a new dae set up for instance:
        >>> self._generic_scan(detector="newDetector.dat",
        >>>                    spectra="newSpectra.dat",
        >>>                    wiring="newWiring.dat",
        >>>                    tcbs=None)

        You can then use this like any other dae setup:

        >>> set_default_dae("newmode", False)

        Parameters
        ----------
        detector : str
          Path to wiring table

        spectra : str
          Path to wiring table

        wiring : str
          Path to wiring table

        tcb: [dict]
          Time channel settings stored in a array of dictionaries
          >>> [{"low": 3500.0, "high": 43500.0, "step": 0.025, "log": True}]

        trans : bool
          If true, set the default transmission instead of the default
          SANS mode.
        """

        def custom_dae():
            self._generic_scan(detector, spectra, wiring, tcb)

        if trans:
            self.setup_trans = custom_dae
        else:
            self.setup_sans = custom_dae

    @property
    def TIMINGS(self):  # pylint: disable=invalid-name
        """The list of valid waitfor keywords."""
        return self._TIMINGS  # pragma: no cover

    def sanitised_timings(self, kwargs):
        """
        Include only the keyword arguments for run timings.
        The list of accepted keywords can be found in the
        TIMINGS property

        Parameters
        ----------
        kwargs : dict
        A dictionary of keyword arguments

        Returns
        -------
        dict
        Keyword arguments accepted by gen.waitfor
        """
        result = {}
        for k in self.TIMINGS:
            if k in kwargs:
                result[k] = kwargs[k]
        return result

    def _generic_scan(self, detector, spectra, wiring, tcbs):
        """A utility class for setting up dae states

        On its own, it's not particularly useful, but
        letting subclasses provide default parameters
        simplifies creating new dae states.
        """
        detector_path = os.path.join(self._tables_path, detector)
        spectra_path = os.path.join(self._tables_path, spectra)
        wiring_path = os.path.join(self._tables_path, wiring)

        gen.change(nperiods=1)
        gen.change_start()
        for tcb in tcbs:
            gen.change_tcb(**tcb)
        gen.change_finish()
        gen.change_start()
        if self.get_pv("DAE:DETECTOR_FILE") != detector_path:
            gen.change_tables(detector=detector_path)
        if self.get_pv("DAE:SPECTRA_FILE") != spectra_path:
            gen.change_tables(spectra=spectra_path)
        if self.get_pv("DAE:WIRING_FILE") != wiring_path:
            gen.change_tables(wiring=wiring_path)
        gen.change_finish()

    _poslist = ['AB', 'BB', 'CB', 'DB', 'EB', 'FB', 'GB', 'HB', 'IB', 'JB',
                'KB', 'LB', 'MB', 'NB', 'OB', 'PB', 'QB', 'RB', 'SB', 'TB',
                'AT', 'BT', 'CT', 'DT', 'ET', 'FT', 'GT', 'HT', 'IT', 'JT',
                'KT', 'LT', 'MT', 'NT', 'OT', 'PT', 'QT', 'RT', 'ST', 'TT',
                '1CB', '2CB', '3CB', '4CB', '5CB', '6CB', '7CB',
                '8CB', '9CB', '10CB', '11CB', '12CB', '13CB', '14CB',
                '1CT', '2CT', '3CT', '4CT', '5CT', '6CT', '7CT',
                '8CT', '9CT', '10CT', '11CT', '12CT', '13CT', '14CT',
                '1WB', '2WB', '3WB', '4WB', '5WB', '6WB', '7WB',
                '8WB', '9WB', '10WB', '11WB', '12WB', '13WB', '14WB',
                '1WT', '2WT', '3WT', '4WT', '5WT', '6WT', '7WT',
                '8WT', '9WT', '10WT', '11WT', '12WT', '13WT', '14WT',
                '1GT', '2GT', '3GT', '4GT', '5GT', '6GT', '7GT', '8GT', '9GT',
                '10GT', '11GT', '12GT', '1R', '2R', '3R', '4R', '5R', '6R', '7R',
                '1OX', '2OX', '3OX', '4OX', '5OX']

    def _attempt_resume(self, title, pos, thick, dae, **kwargs):
        if gen.get_title() != f"{title}{self.title_footer}":
            raise RuntimeError(
                f'Attempted to continue measurement "{title}", but was already in '
                f'the middle of measurement "{gen.get_title()}".')
        if isinstance(pos, str):
            if pos != self.changer_pos:
                raise RuntimeError(
                    f'Attempted to continue measurement in position "{title}", '
                    f'but was already in position "{gen.get_title()}".')
        elif callable(pos):
            raise RuntimeError(
                'Cannot determine if instrument is in the right place to '
                'resume run. Please manually end the run and restart it.')
        elif pos is not None:
            raise RuntimeError(
                'Cannot determine if instrument is in the right place to '
                'resume run. Please manually end the run and restart it.')

        if dae and self._dae_mode != dae:
            raise RuntimeError(
                f'Cannot resume a measurement with DAE mode {dae} '
                f'since the current running measurement is DAE mode {self._dae_mode}. '
                f'Either check your script or manually stop the '
                f'current run.')

        for arg, val in sorted(kwargs.items()):
            if arg in self.TIMINGS:
                continue
            if gen.cget(arg)["value"] != val:
                raise RuntimeError(
                    f'Expected to resume measurement with position {arg,} '
                    f'at {val}, but instead found it at {gen.cget(val)["value"]}. Please either '
                    f'correct the script or manually end the run.')

        if gen.get_sample_pars()['THICK'] != thick:
            raise RuntimeError(
                f'Expected to resume a run on a sample of thickness {thick}, '
                f'but was already running a measurement on a sample of '
                f'thickness {gen.get_sample_pars()["THICK"]}. Please either correct the script or '
                f'manually end the run')

        times = self.sanitised_timings(kwargs)
        warning(
            "Detected that run was already in progress."
            "Reconnecting to existing run.")
        self._waitfor(**times)
        self._end()

    @property
    def measurement_type(self):
        """Get the measurement type from the journal.

        Changing this property should perform no physical changes to the
        beamline. The only change should be in the MEASUREMENT:TYPE
        value stored in the journal for the next run, which should be
        set to the new value.
        """
        return self.get_pv("PARS:SAMPLE:MEAS:TYPE")

    @measurement_type.setter
    def measurement_type(self, value):
        """Set the measurement type in the journal.

        Parameters
        ----------
        value : str
          The new measurement type

        This function should perform no physical changes to the
        beamline.  The only change should be in the MEASUREMENT:TYPE
        value stored in the journal for the next run, which should be
        set to the new value.
        """
        self.send_pv("PARS:SAMPLE:MEAS:TYPE", value)

    @property
    def measurement_label(self):
        """Get the current measurement label from the journal

        Changing this property should perform no physical changes to the
        beamline. The only change should be in the MEASUREMENT:LABEL
        value stored in the journal for the next run, which should be
        set to the new value.
        """
        return self.get_pv("PARS:SAMPLE:MEAS:LABEL")

    @measurement_label.setter
    def measurement_label(self, value):
        """Set the sample label in the journal.

        Parameters
        ----------
        value : str
          The new sample label

        This function should perform no physical changes to the
        beamline.  The only change should be in the MEASUREMENT:LABEL
        value stored in the journal for the next run, which should be
        set to the new value.
        """
        self.send_pv("PARS:SAMPLE:MEAS:LABEL", value)

    @property
    def measurement_id(self):
        """Get the measurement id from the journal

        Changing this property should perform no physical changes to the
        beamline. The only change should be in the MEASUREMENT:ID
        value stored in the journal for the next run, which should be
        set to the new value.
        """
        return self.get_pv("PARS:SAMPLE:MEAS:ID")

    @measurement_id.setter
    def measurement_id(self, value):  # pragma: no cover
        """Set the measurement id in the journal.

        Parameters
        ----------
        value : str
          The new id

        This function should perform no physical changes to the
        beamline.  The only change should be in the MEASUREMENT:ID
        value stored in the journal for the next run, which should be
        set to the new value.
        """
        self.send_pv("PARS:SAMPLE:MEAS:ID", value)

    def _begin(self, *args, **kwargs):
        """Start a measurement.
        If _dae_mode is set then _begin_<dae_mode> is called.
        Else the run starts with the parameters provided
        """
        if self._dae_mode and hasattr(self, "_begin_" + self._dae_mode):
            getattr(self, "_begin_" + self._dae_mode)(*args, **kwargs)
        else:
            gen.begin(*args, **kwargs)

    def _end(self):
        """End a measurement.
        If _dae_mode is set then _end_<dae_mode> is called.
        Else the run end normally"""
        if self._dae_mode and hasattr(self, "_end_" + self._dae_mode):
            getattr(self, "_end_" + self._dae_mode)()  # pragma: no cover
        else:
            gen.end()

    def _waitfor(self, **kwargs):
        """Await the user's desired statistics.
        If _dae_mode is set then _waitfor_<dae_mode> is called.
        Else the run waits with the parameters provided
        """
        if self._dae_mode and hasattr(self, "_waitfor_" + self._dae_mode):
            getattr(self, "_waitfor_" + self._dae_mode)(**kwargs)
        else:
            gen.waitfor(**kwargs)

    def detector_lock(self, state=None):
        """Query or activate the detector lock

        Parameters
        ----------
        state : bool or None
          If None, return the current lock state.  Otherwise, set the
          new lock state

        Returns
        ----------
        The current lock state as a bool

        Locking the detector prevents turning the detector on or off
        and bypasses the detector checks.

        """
        if state is not None:
            self._detector_lock = state
        return self._detector_lock

    def detector_on(self, powered=None, delay=True):
        """Query and set the detector's electrical state.

        Parameters
        ----------
        powered : bool or None
          If None, then return the detector's current state.  If True,
          turn the detector on.  If False, turn the detector off.
        delay : bool
          If changing the detector state, whether to wait for the
          detector to finish warming up or powering down before
          continuing the script.
        Returns
        ----------
        bool
          If the detector is currently on

        """
        if powered is not None:
            if self.detector_lock():
                raise RuntimeError("The instrument scientist has locked the"
                                   " detector state")
            if powered is True:
                self._detector_turn_on(delay=delay)
            else:
                self._detector_turn_off(delay=delay)
        return self._detector_is_on()

    def check_move_pos(self, pos):
        """Check whether the position is valid and return True or False

        Parameters
        ----------
        pos : str
          The sample changer position

        """
        if pos.upper() not in [pos_name.upper() for pos_name in self._poslist]:
            warning(f"Error in script, position {pos} does not exist")
            return False
        return True

    def check_move_pos_dls(self, pos):
        """Check whether the position is valid for the DLS sample changer and return True or False

        Parameters
        ----------
        pos : str
          The sample changer position

        """
        if self._poslist_dls is None:
            NotImplementedError("DLS sample changer is unsupported on this instrument")
            return False

        elif self._poslist_dls is []:
            self._set_poslist_dls()

        if pos.upper() not in [pos_name.upper() for pos_name in self._poslist_dls]:
            warning(f"Error in script, position {pos} does not exist")
            return False
        return True

    @property
    def changer_pos(self):
        """Get the current sample changer position"""
        return gen.cget("SamplePos")["value"]

    @changer_pos.setter
    def changer_pos(self, pos):
        """Set the current sample changer position

        Parameters
        ----------
        pos : str
          The new dls sample changer position
        """
        for possible_position in self._poslist:
            if pos.upper() == possible_position.upper():
                gen.cset(SamplePos=pos)
                return
        else:
            warning(f"Unable to set changer position to {pos}; invalid position name?")

    @property
    def changer_pos_dls(self):
        """Get the current dls sample changer position
        if dls sample changer available"""
        return gen.cget("sample_position")["value"]

    @changer_pos_dls.setter
    def changer_pos_dls(self, pos):
        """Set the current dls sample changer position

        Parameters
        ----------
        pos : str
          The new dls sample changer position
        """
        for possible_position in self._poslist_dls:
            if pos.upper() == possible_position.upper():
                gen.cset(sample_position=pos)
                return
        else:
            warning(f"Unable to set DLS changer position to {pos}; invalid position name?")

    def _setup_measurement_software(self, trans):
        """It will set the measurement type then sets the up the
        current dae for trans/sans measurement. The measurement
        type (formally set here then reset in the decorator) 
        should be set in the decorator dae_setter of the called method.

        Parameters
        ----------
        trans : bool
          Is this a transmission measurement
        """
        if trans:
            self.setup_trans()

        else:
            self.setup_sans()

    def measure(self, title="", position=None, thickness=1.0, trans=False,
                dae=None, aperture="", time=None,
                period=None, dls_sample_changer=False, **kwargs):
        """Take a sample measurement. If no timing parameter is provided
        then no measurement occurs but experiment setup does happen.

        Parameters
        ----------
        title : str
          The title for the measurement.  This is the only required parameter.
        position : str or func
          The sample position.  This can be a string with the name of
          a sample position, or it can be a function which moves the
          detector into the desired position.  If left undefined, the
          instrument will take the measurement in its current
          position.
          Example of a function that could be passed in:
          >>> def custom_pos_function():
          >>>   gen.cset(SamplePos="new position")
        thickness : float
          The thickness of the sample in millimeters.  The default is 1mm.
        trans : bool
          Whether to perform a transmission run instead of a sans run.
          True for trans run leave blank or False for sans
        dae : str
          This option allows setting the default dae mode.  It takes a
          string that contains the name of the DAE mode to be used as
          the new default. There will be used in subsequence runs for sans
          and trans mode accordingly. For example,
          >>> measure("title=Test", frames=10, dae="event")
          Is equivalent to
          >>> set_default_dae(setup_dae_event)
          >>> measure("Test", frames=10)
          To get a full list of the supported dae modes, run
          >>> enumerate_dae()
          To create custom dae's use create_dae_custom
        aperture : str
          The aperture size.  e.g. "Small" or "Medium" A blank string
          (the default value) results in the aperture not being
          changed from default value for trans/sans.
        time : int
            The number of seconds for the experiment to run.
            To run for different units of time you can included parameters 
            from the TIMINGS property this includes uamps, frames, and hours
            However, these will be ignored if time argument is provided.
        period : int
            The period to collect the dae data
        dls_sample_changer : bool
            If you are currently using the dls sample changer
        **kwargs
          This is a general term for all other arrangements but in
          this case there are some specific thing you can pass:

          If given a time duration from the TIMINGS property you can have
          more control over the time frame of the run Options . However, 
          these will be ignored if time is provided.

          If given a block name, it will move that block to the given
          position.

        Examples
        ----------

        >>> measure(title="H2O", frames=900)

        Perform a SANS measurement in the current position on a 1 mm
        thick water sample until the proton beam has released 900
        proton pulses (approx 15 minutes).

        >>> measure(title="D2O", pos="LT", thickness=2.0, trans=True, CoarseZ=25, uamps=10)

        Move to sample changer position LT, then adjust the CoarseZ
        motor to 25 mm. Finally, take a transmission measurement on a
        2 mm thick deuterium sample for 10 µA hours of proton
        current. (approx 15 minutes).
        """
        if gen.get_runstate() != "SETUP":  # pragma: no cover
            self._attempt_resume(title, position, thickness, dae, **kwargs)
            return

        self._measure(title=title, position=position, thickness=thickness, trans=trans,
                      dae=dae, aperture=aperture, time=time,
                      period=period, _custom=True, dls_sample_changer=dls_sample_changer, **kwargs)

    def _setup(self, title="", position=None, thickness=1.0, trans=False,
               dae=None, aperture="", period=None,
               _custom=True, dls_sample_changer=False, **kwargs):
        # Check detector for sans
        if not self.detector_lock() and not self.detector_on() and not trans:
            raise RuntimeError(
                "The detector is off.  Either turn on the detector or "
                "use the detector_lock(True) to indicate that the detector "
                "is off intentionally")
        # If not called from do_sans/trans do so extra set up
        if _custom:
            self.set_default_dae(dae, trans)
            self._setup_measurement_software(trans)

        self.measurement_label = title
        gen.change(title=title + self.title_footer)

        self.set_aperture(aperture)

        if position:
            self._set_sample_position(position, dls_sample_changer)

        # Check for extra blocks to be at set positions
        for arg, val in sorted(kwargs.items()):
            if arg in self.TIMINGS:
                continue
            info(f"Moving {arg} to {val}")
            gen.cset(arg, val)
        gen.waitfor_move()
        gen.change_sample_par("Thick", thickness)
        info("Using the following Sample Parameters")
        self.print_sample_pars()
        if period:
            gen.change_period(period)

    def _set_sample_position(self, position, dls_sample_changer=False):
        if isinstance(position, str):
            if dls_sample_changer and self.check_move_pos_dls(position):
                info(f"Moving to dls sample changer position {position}")
                self.changer_pos_dls = position
            elif self.check_move_pos(position):
                info(f"Moving to sample changer position {position}")
                self.changer_pos = position
            else:
                raise RuntimeError(
                    f"Position {position} does not exist")
        elif callable(position):
            info(f"Moving to position {position.__name__}")
            position()
        else:
            raise TypeError(f"Cannot understand position {position}")
        gen.waitfor_move()

    def _do_measure(self, title="", time=None, **kwargs):
        if time:
            times = {"seconds": time}
        else:
            times = self.sanitised_timings(kwargs)

        unit, time = _get_times(times)
        info(f"Measuring {title + self.title_footer} for {time} {unit}")
        self._begin()
        self._waitfor(**times)
        self._end()

    def _measure(self, title="", position=None, thickness=1.0, trans=False,
                 dae=None, aperture="", period=None,
                 time=None, _custom=True, **kwargs):

        self._setup(title=title, position=position, thickness=thickness, trans=trans,
                    dae=dae, aperture=aperture, period=period,
                    _custom=_custom, **kwargs)

        # If a time frame given start the experiment
        if time or self.sanitised_timings(kwargs):
            self._do_measure(title=title, time=time, **kwargs)

    def do_sans(self, title="", pos=None, thickness=1.0, dae=None,
                aperture="", period=None, time=None, dls_sample_changer=False, **kwargs):
        """A wrapper around ``measure`` which ensures that the instrument is
        in sans mode before running the measurement if a title is given.
        It ensures that the instrument is set up correctly by running the
        _configure_sans_custom command that is instrument specific.

        Typically, _configure_sans_custom sets up the aperture and appropriate
        monitor. You can override the aperture by setting the aperture parameter,
        similarly you can override specific motors as decide in the measure
        documentation.

        Look at the documentation for ``measure`` to see the full set
        of parameters accepted. """

        if gen.get_runstate() != "SETUP":  # pragma: no cover
            self._attempt_resume(title, pos, thickness, dae, **kwargs)
            return

        info("Set up instrument for sans measurement")
        self._configure_sans_custom()
        gen.waitfor_move()
        self.set_default_dae(mode=dae, trans=False)
        self._setup_measurement_software(trans=False)

        if "trans" in kwargs:
            del kwargs["trans"]
        self._measure(title=title, trans=False, position=pos, thickness=thickness,
                      dae=dae, aperture=aperture, period=period,
                      time=time, _custom=False, dls_sample_changer=dls_sample_changer, **kwargs)

    def do_trans(self, title="", pos=None, thickness=1.0, dae=None,
                 aperture="", period=None, time=None, dls_sample_changer=False, **kwargs):
        """A wrapper around ``measure`` which ensures that the instrument is
         in transition mode before running the measurement if a title is given. It ensures that the
         instrument is set up correctly by running the _configure_trans_custom command that
         is instrument specific.

        Typically, _configure_trans_custom sets up the aperture and appropriate
        monitor. You can override the aperture by setting the aperture parameter,
        similarly you can override specific motors as decide in the measure
        documentation.


        Look at the documentation for ``measure`` to see the full set
        of parameters accepted. """

        if gen.get_runstate() != "SETUP":  # pragma: no cover
            self._attempt_resume(title, pos, thickness, dae, **kwargs)
            return

        info("Set up instrument for trans measurement")
        self._configure_trans_custom()
        gen.waitfor_move()
        self.set_default_dae(mode=dae, trans=True)
        self._setup_measurement_software(trans=True)

        if "trans" in kwargs:
            del kwargs["trans"]
        self._measure(title=title, trans=True, position=pos, thickness=thickness,
                      dae=dae, aperture=aperture, period=period,
                      time=time, _custom=False, dls_sample_changer=dls_sample_changer, **kwargs)

    def measure_file(self, file_path, forever=False):
        """Perform a series of measurements based on a spreadsheet

        The file should contain comma separated values.  Excel can
        easily produce files of this sort.  The first line of the file
        is the header with each field giving the name of a parameter
        to the `measure` function.  As always, the ``title`` parameter
        is mandatory.  Each subsequent line of the file represents a
        single measurement with the fields indicating that values to
        pass to their corresponding keywords.  If a cell is blank, the
        keyword's default parameter it used.  Boolean values are
        represented by `True` and `False` and are not case-sensitive.

        The script is run through the simulator to check for errors
        before attempting a real run.

        Parameters
        ----------
        file_path : str
          The location of the script file
        forever : bool
          If set to True, the instrument will repeatedly run the
          script manually stopped.  This can be useful for an
          overnight run where you want to keep measuring until the
          users return.

        """

        @user_script
        def inner():
            """Actually load and run the script"""
            with open(file_path, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    row = {k: row[k] for k in row if row[k].strip() != ""}
                    for k in row.keys():
                        if row[k].upper() == "TRUE":
                            row[k] = True
                        elif row[k].upper() == "FALSE":
                            row[k] = False
                        else:
                            try:
                                row[k] = ast.literal_eval(row[k])
                            except ValueError:
                                continue
                    self.measure(**row)

        if forever:  # pragma: no cover
            while True:
                inner()
        else:
            inner()

    @staticmethod
    def convert_file(file_path):
        """Turn a CSV run list into a full python script

        This function allows the user to create simple scripts with
        Excel, then turn them into full Python scripts that can be
        edited and customised as needed.

        Parameters
        ----------
        file_path : str
            The path to the file you wish to convert
        """
        with open(file_path, "r") as src, open(file_path + ".py", "w") as out:
            out.write("from SansScripting import *\n")
            out.write("@user_script\n")
            function_name = os.path.splitext(
                os.path.basename(file_path))[0].replace(" ", "_")
            out.write(f"def {function_name}():\n")
            reader = csv.DictReader(src)
            for row in reader:

                if "trans" in row and row["trans"] == "TRUE":
                    header = "do_trans"
                else:
                    header = "do_sans"

                title = row["title"]
                del row["title"]

                if "trans" in row:
                    del row["trans"]

                out.write(f'    {header}(title="{title}", ')

                if "pos" in row:
                    out.write(f'position="{row["pos"]}", ')
                    del row["pos"]

                row = {key: row[key] for key in row if row[key].strip() != ""}
                for key in row.keys():
                    if row[key].upper() == "TRUE":
                        row[key] = True
                    elif row[key].upper() == "FALSE":
                        row[key] = False
                    else:
                        try:
                            row[key] = ast.literal_eval(row[key])
                        except ValueError:
                            row[key] = "\"" + row[key] + "\""
                            continue
                params = ", ".join([key + "=" + str(value)
                                    for (key, value) in sorted(row.items())])
                out.write(f'{params})\n')

    @staticmethod
    def print_sample_pars():
        """Display the basic sample parameters on the console."""
        pars = gen.get_sample_pars()
        for par in ["Geometry", "Width", "Height", "Thick"]:
            info(f"{par}={pars[par.upper()]}")

    def enumerate_dae(self):
        """List the supported DAE modes on this beamline.
        Warning: Some methods may not be implemented from the base class
        """
        setup_dae = "setup_dae_"
        return [x[len(setup_dae):] for x in dir(self) if x.startswith(setup_dae)]

    def get_pv(self, name):
        """Get the given PV within the sub hierarchy of the instrument.

        For example, on Larmor, get_pv("DAE:WIRING_FILE") would return
        the value of the PV for "IN:LARMOR:DAE:WIRING_FILE"

        """
        return gen.get_pv(name, is_local=True)

    def send_pv(self, name, value):
        """Set the given PV within the sub hierarchy of the instrument.

        For example, on Larmor, send_pv("DAE:WIRING_FILE", f) would
        change the value of the PV for "IN:LARMOR:DAE:WIRING_FILE" to
        the value in f.
        """
        return gen.set_pv(name, value, is_local=True)

    @property
    def tables_path(self):
        """Path to folder containing the detector/wiring/spectra
        tables. The default path is normally:
        "C:/Instrument/Settings/config/<instrument>/configurations/tables"
        """
        return self._tables_path

    @tables_path.setter
    def tables_path(self, new_path):
        self._tables_path = new_path

    @abstractmethod
    def setup_dae_event(self):  # pragma: no cover
        """Set the wiring tables for event mode"""

    @abstractmethod
    def setup_dae_histogram(self):  # pragma: no cover
        """Set the wiring tables for histogram mode"""

    @abstractmethod
    def setup_dae_transmission(self):  # pragma: no cover
        """Set the wiring tables for a transmission measurement"""

    @abstractmethod
    def _configure_sans_custom(self):
        """The specific actions required by the instrument
        to run a SANS measurement (e.g. remove the monitor
        from the beam).
        """

    @abstractmethod
    def _configure_trans_custom(self):
        """The specific actions required by the instrument
        to run a SANS measurement (e.g. remove the monitor
        from the beam).
        """

    @abstractmethod
    def _detector_is_on(self):  # pragma: no cover
        """Determine the current state of the detector.

        Returns
        -------
        bool
          True if the detector is powered up.

        """

    @abstractmethod
    def _detector_turn_on(self, delay=True):  # pragma: no cover
        """Power on the detector

        Parameters
        ----------
        delay : bool
          Wait for the detector to warm up before continuing
        """

    @abstractmethod
    def _detector_turn_off(self, delay=True):  # pragma: no cover
        """Remove detector power

        Parameters
        ----------
        delay : bool
          Wait for the detector to cool down before continuing
        """

    @abstractmethod
    def set_aperture(self, size):  # pragma: no cover
        """Set the beam aperture to the desired size

        Parameters
        ----------
        size : str
          The aperture size. e.g. "Small" or "Medium"
          A blank string (the default value) results in
          the aperture not being changed."""

    def _set_poslist_dls(self):
        try:
            self._poslist_dls = self.get_pv("LKUP:DLS:POSITIONS").split()
        except AttributeError:
            warning("No positions found for DLS Sample Changer!")
            self._poslist_dls = []
