# -*- coding: utf-8 -*-
"""The baseline for loading a scanning instrument

Each instrument will have its own module that declares a class
inheriting from ScanningInstrument.  The abstract base class is used
to ensure that the derived classes define the necessary methods to run
any generic scripts.

"""

from abc import ABCMeta, abstractmethod
from logging import info, warning
from six import add_metaclass
from .genie import gen


def _get_times(times):
    for k in ["uamps", "frames", "hours", "minutes", "seconds"]:
        if k in times:
            return k, times[k]
    raise RuntimeError("No valid time found")


@add_metaclass(ABCMeta)  # pylint: disable=too-many-public-methods
class ScanningInstrument(object):
    """The base class for scanning measurement instruments."""

    _dae_mode = None
    _detector_lock = False
    title_footer = ""
    measurement_type = "sans"
    _TIMINGS = ["uamps", "frames", "seconds", "minutes", "hours"]

    def __init__(self):
        self.setup_sans = self.setup_dae_event
        self.setup_trans = self.setup_dae_transmission

    def set_default_dae(self, mode=None, trans=False):
        """Set the default DAE mode for SANS or TRANS measuremnts.

        Parameters
        ----------
        mode : str or function
          If the mode is a function, call that function to set the DAE
          mode.  If the mode is a string, call the function whose name
          is "setup_dae_" followed by that string.
        trans : bool
          If true, set the default transmission instead of the default
          SANS mode.

        """
        if mode is None:
            pass
        elif isinstance(mode, str):
            self.set_default_dae(
                getattr(self, "setup_dae_"+mode),
                trans)
        else:
            if trans:
                self.setup_trans = mode
            else:
                self.setup_sans = mode

    @property
    def TIMINGS(self):  # pylint: disable=invalid-name
        """The list of valid waitfor keywords."""
        return self._TIMINGS  # pragma: no cover

    def sanitised_timings(self, kwargs):
        """Include only the keyword arguments for run timings.

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

    @staticmethod
    def _generic_scan(detector, spectra, wiring, tcbs):
        """A utility class for setting up dae states

        On its own, it's not particularly useful, but
        letting subclasses provide default parameters
        simplifies creating new dae states.
        """
        gen.change(nperiods=1)
        gen.change_start()
        gen.change_tables(detector=detector)
        gen.change_tables(spectra=spectra)
        gen.change_tables(wiring=wiring)
        for tcb in tcbs:
            gen.change_tcb(**tcb)
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
                '8WT', '9WT', '10WT', '11WT', '12WT', '13WT', '14WT']

    @staticmethod
    def _needs_setup():
        if gen.get_runstate() != "SETUP":  # pragma: no cover
            raise RuntimeError("Cannot start a measurement in a measurement")

    @abstractmethod
    def set_measurement_type(self, value):  # pragma: no cover
        """Set the measurement type in the journal.

        Parameters
        ==========
        value : str
          The new measurement type

        This function should perform no physical changes to the
        beamline.  The only change should be in the MEASUREMENT:TYPE
        value stored in the journal for the next run, which should be
        set to the new value.
        """

    @abstractmethod
    def set_measurement_label(self, value):  # pragma: no cover
        """Set the sample label in the journal.

        Parameters
        ==========
        value : str
          The new sample label

        This function should perform no physical changes to the
        beamline.  The only change should be in the MEASUREMENT:LABEL
        value stored in the journal for the next run, which should be
        set to the new value.
        """

    @abstractmethod
    def set_measurement_id(self, value):  # pragma: no cover
        """Set the measurement id in the journal.

        Parameters
        ==========
        value : str
          The new id

        This function should perform no physical changes to the
        beamline.  The only change should be in the MEASUREMENT:ID
        value stored in the journal for the next run, which should be
        set to the new value.
        """

    @abstractmethod
    def setup_dae_scanning(self):  # pragma: no cover
        """Set the wiring tables for a scan"""

    @abstractmethod
    def setup_dae_nr(self):  # pragma: no cover
        """Set the wiring tables for a neutron
        reflectivity measurement"""

    @abstractmethod
    def setup_dae_nrscanning(self):  # pragma: no cover
        """Set the wiring tables for performing
        scans during neutron reflectivity"""

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
    def setup_dae_bsalignment(self):  # pragma: no cover
        """Configure wiring tables for beamstop alignment."""

    def _configure_sans_custom(self):
        """The specific actions required by the instrument
        to run a SANS measurement (e.g. remove the monitor
        from the beam).

        This is a no-op for the default instrument but can be
        overwritten by other instruments to perform any actions they
        need to put the instrument into SANS mode.
        """

    def _configure_trans_custom(self):
        """The specific actions required by the instrument
        to run a SANS measurement (e.g. remove the monitor
        from the beam).

        This is a no-op for the default instrument but can be
        overwritten by other instruments to perform any actions they
        need to put the instrument into SANS mode.
        """

    def _begin(self, *args, **kwargs):
        """Start a measurement."""
        if self._dae_mode and hasattr(self, "_begin_"+self._dae_mode):
            getattr(self, "_begin_"+self._dae_mode)(*args, **kwargs)
        else:
            gen.begin(*args, **kwargs)

    def _end(self):
        """End a measurement."""
        if self._dae_mode and hasattr(self, "_end_"+self._dae_mode):
            getattr(self, "_end_"+self._dae_mode)()  # pragma: no cover
        else:
            gen.end()

    def _waitfor(self, **kwargs):
        """Await the user's desired statistics."""
        if self._dae_mode and hasattr(self, "_waitfor_"+self._dae_mode):
            getattr(self, "_waitfor_"+self._dae_mode)(**kwargs)
        else:
            gen.waitfor(**kwargs)

    @staticmethod
    @abstractmethod
    def set_aperture(size):  # pragma: no cover
        """Set the beam aperture to the desired size

        Parameters
        ----------
        size : str
          The aperture size.  e.g. "Small" or "Medium"
          A blank string (the default value) results in
          the aperture not being changed."""

    def detector_lock(self, state=None):
        """Query or activate the detector lock

        Parameters
        ==========
        state : bool or None
          If None, return the current lock state.  Otherwise, set the
          new lock state

        Returns
        =======
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
        on : bool or None
          If None, then return the detector's current state.  If True,
          turn the detector on.  If False, turn the detector off.
        delay : bool
          If changing the detector state, whether to wait for the
          detector to finish warming up or powering down before
          continuing the script.
        Returns :
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

    @staticmethod
    @abstractmethod
    def _detector_is_on():  # pragma: no cover
        """Determine the current state of the detector.

        Returns
        -------
        bool
          True if the detector is powered up.

        """
        return False

    @staticmethod
    @abstractmethod
    def _detector_turn_on(delay=True):  # pragma: no cover
        """Power on the detector

        Parameters
        ==========
        delay : bool
          Wait for the detector to warm up before continuing
        """
        return False

    @staticmethod
    @abstractmethod
    def _detector_turn_off(delay=True):  # pragma: no cover
        """Remove detector power

        Parameters
        ==========
        delay : bool
          Wait for the detector to cool down before continuing
        """
        return False

    def check_move_pos(self, pos):
        """Check whether the position is valid and return True or False

        Parameters
        ----------
        pos : str
          The sample changer position

        """
        if pos.upper() not in self._poslist:
            warning("Error in script, position {} does not exist".format(pos))
            return False
        return True

    @staticmethod
    def _move_pos(pos):
        """Move the sample changer to a labelled position"""
        return gen.cset(SamplePos=pos)

    def _setup_measurement(self, trans, blank):
        """Perform all of the software setup for a measurement

        Parameters
        ==========
        trans : bool
          Is this a transmission measurement
        blank : bool
          Is this a measurement on a sample blank
        """
        if trans:
            if blank:
                self.set_measurement_type("blank_transmission")
            else:
                self.set_measurement_type("transmission")
            self.setup_trans()
            self._configure_trans_custom()
        else:
            if blank:
                self.set_measurement_type("blank")
            else:
                self.set_measurement_type(self.measurement_type)
            self.setup_sans()
            self._configure_sans_custom()

    def measure(self, title, pos=None, thickness=1.0, trans=False,
                dae=None, blank=False, aperture="", **kwargs):
        """Take a sample measurement.

        Parameters
        ==========
        title : str
          The title for the measurement.  This is the only required parameter.
        pos
          The sample position.  This can be a string with the name of
          a sample position or it can be a function which moves the
          detector into the desired position.  If left undefined, the
          instrument will take the measurement in its current
          position.
        thickness : float
          The thickness of the sample in millimeters.  The default is 1mm.
        trans : bool
          Whether to perform a transmission run instead of a sans run.
        dae : str or func
          This option allows setting the default dae mode.  It takes a
          string that contains the name of the DAE mode to be used as
          the new default.  For example,
          >>> measure("Test", frames=10, dae="event")
          Is equivalent to
          >>> set_default_dae(setup_dae_event)
          >>> measure("Test", frames=10)
          If dae is a function, then the function is set to the default
          >>> measure("Test", frames=10, dae=foo)
          Is equivalent to
          >>> set_default_dae(foo)
          >>> measure("Test", frames=10)
          To get a full list of the supported dae modes, run
          >>> enumerate_dae()
        aperture : str
          The aperture size.  e.g. "Small" or "Medium" A blank string
          (the default value) results in the aperture not being
          changed.
        blank : bool
          If this sample should be considered a blank/can/solvent measurement
        **kwargs
          This function takes two kinds of keyword arguments.  If
          given a block name, it will move that block to the given
          position.  If given a time duration, then that will be the
          duration of the run.

        Examples
        ========

        >>> measure("H2O", frames=900)

        Perform a SANS measurment in the current position on a 1 mm
        thick water sample until the proton beam has released 900
        proton pulses (approx 15 minutes).

        >>> measure("D2O", "LT", thickness=2.0, trans=True, Phi=3, uamps=10)

        Move to sample changer position LT, then adjust the CoarseZ
        motor to 38 mm.  Finally, take a transmission measurement on a
        2 mm thick deuterium sample for 10 µA hours of proton
        current. (approx 15 minutes).

        """
        self._needs_setup()
        if not self.detector_lock() and not self.detector_on() and not trans:
            raise RuntimeError(
                "The detector is off.  Either turn on the detector or "
                "use the detector_lock(True) to indicate that the detector "
                "is off intentionally")
        self.set_default_dae(dae, trans)
        self._setup_measurement(trans, blank)
        self.set_measurement_label(title)
        self.set_aperture(aperture)
        if pos:
            if isinstance(pos, str):
                if self.check_move_pos(pos=pos):
                    info("Moving to sample changer position {}".format(pos))
                    self._move_pos(pos)
                else:
                    raise RuntimeError(
                        "Position {} does not exist".format(pos))
            elif callable(pos):
                info("Moving to position {}".format(pos.__name__))
                pos()
            else:
                raise TypeError("Cannot understand position {}".format(pos))
        for arg, val in sorted(kwargs.items()):
            if arg in self.TIMINGS:
                continue
            info("Moving {} to {}".format(arg, val))
            gen.cset(arg, val)
        times = self.sanitised_timings(kwargs)
        gen.waitfor_move()
        gen.change_sample_par("Thick", thickness)
        info("Using the following Sample Parameters")
        self.printsamplepars()
        gen.change(title=title+self.title_footer)

        self._begin()
        unit, time = _get_times(times)
        info("Measuring {title:} for {time:} {units:}".format(
            title=title+self.title_footer,
            units=unit,
            time=time))
        self._waitfor(**times)
        self._end()

    def do_sans(self, title, pos=None, thickness=1.0, dae=None, blank=False,
                aperture="", **kwargs):
        """A wrapper around ``measure`` which ensures that the instrument is
not in transmission mode

Look at the documentation for ``measure`` to see the full set
of parameters accepted. """
        if "trans" in kwargs:
            del kwargs["trans"]
        self.measure(title, trans=False, pos=pos, thickness=thickness,
                     dae=dae, blank=blank, aperture=aperture,
                     **kwargs)

    def do_trans(self, title, pos=None, thickness=1.0, dae=None, blank=False,
                 aperture="", **kwargs):
        """A wrapper around ``measure`` which ensures that the instrument is
not in transmission mode.

Look at the documentation for ``measure`` to see the full set
of parameters accepted. """
        if "trans" in kwargs:
            del kwargs["trans"]
        self.measure(title, trans=True, pos=pos, thickness=thickness,
                     dae=dae, blank=blank, aperture=aperture,
                     **kwargs)

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
        represented by `True` and `False` and are not case sensitive.

        The script is run through the simulator to check for errors
        before attempting a real run.

        Parameters
        ----------
        file_path : str
          The location of the script file
        forever : bool
          If set to True, the instrument will repeatedly run the
          script manually stopped.  This can be useful for an
          overnight run where you want to keep measureing until the
          users return.

        """
        from .util import user_script

        @user_script
        def inner():
            """Actually load and run the script"""
            import csv
            import ast
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

        """
        import csv
        import ast
        import os.path
        with open(file_path, "r") as src, open(file_path+".py", "w") as out:
            out.write("from SansScripting import *\n")
            out.write("@user_script\n")
            out.write("def {}():\n".format(
                os.path.splitext(
                    os.path.basename(file_path))[0].replace(" ", "_")))
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

                out.write('    {}("{}", '.format(header, title))

                if "pos" in row:
                    out.write('"{}", '.format(row["pos"]))
                    del row["pos"]

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
                            row[k] = "\"" + row[k] + "\""
                            continue
                params = ", ".join([k + "=" + str(v)
                                    for (k, v) in sorted(row.items())])
                out.write('{})\n'.format(params))

    @staticmethod
    def printsamplepars():
        """Display the basic sample parameters on the console."""
        pars = gen.get_sample_pars()
        for par in ["Geometry", "Width", "Height", "Thick"]:
            info("{}={}".format(par, pars[par.upper()]))

    def enumerate_dae(self):
        """List the supported DAE modes on this beamline."""
        return [x[10:] for x in dir(self) if x.startswith("setup_dae_")]
