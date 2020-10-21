Guide for Instrument Scientists
*******************************

.. highlight:: python
   :linenothreshold: 20


Introduction
============


Adding an Instrument
====================

Every instrument should have its own subclass of the
ScanningInstrument class.  This subclass should be defined in the
module ``instrument/name/sans.py``, where `name` is the name of the
instrument.  That class must implement the following abstract methods:

- setup_dae_scanning
     Configure the DAE for performing an intensity
     scan on the main detector.
- setup_dae_nr
      Configure the DAE for reflectometry.
- setup_dae_nrscanning
     Configure the DAE for performing scans
  during reflectometry.
- setup_dae_event
     Configure the DAE for SANS in event mode.
- setup_dae_histogram
     Configure the DAE for SANS in histogram mode.
- setup_dae_transmission
     Configure the DAE for transmission mode.
- setup_dae_bsalignment
     Configure the DAE for beamstop alignment.
- set_aperture
     Change the beam aperture.  The currently accepted
  values are ``"SMALL"``, ``"MEDIUM"``, and ``"LARGE"``.
- _detector_is_on
      Check whether the detector is on.
- _detector_turn_on
      Power on the detector.
- _detector_turn_off
      Power off the detector.

It should be noted that most ``setup_dae_`` functions will benefit
from the :py:meth:`technique.sans.util.set_metadata` decorator.  This
decorator takes two parameters. The first is a suffix to be appended
to the run title.  This is used to distinguish between run types in
the journal (e.g. identifying where a run is a "SANS" or a "TRANS" run).
The second parameter is a similar label for the type of run that will
be recorded in the final nexus file.  This can eventually be used to
automatically generate reduction scripts for simple sample hanger
measurements.

It is also necessary to set the _PV_BASE attribute to the header
string that occurs at the front of every PV for the instrument.  For
example, on ZOOM, this value is ``"IN:ZOOM:"``

It can also be useful, but not mandatory, to override the following methods

- _configure_sans_custom
     Perform any configuration of the
     instrument (not the DAE) that needs to occur when performing a SANS
     measurement.  For example, on LOQ, this function moves the
     transmission monitor out of the beam.
- _configure_trans_custom
     Perform any configuration of the
     instrument (not the DAE) that needs to occur when performing a
     transmission measurement.  For example, on LOQ, this sets the beam
     aperture to small and move the transmission monitor in.
- changer_pos
     This property should read and set the sample changer
     position.
- _generic_scan
     This function takes the detector, spectra, and wiring files,
     along side the timing settings, and passes them to the tcb.  Most
     of the DAE setup functions will wind up calling this method and
     it can be convenient if the default parameters have been
     overwritten and specialised to the instrument, instead of needing
     to repeat them for each DAE mode.

Writing a DAE Mode
==================

Most instruments have their own specific DAE modes that they might
enter for performing unusual or custom measurements.  These modes can
be added by adding another member function to the subclass whose name
starts with ``setup_dae_``.  For example, on LOQ, the function
``setup_dae_50hz_short`` activates the 50hz mode for the instrument in
its short configuration.  The ``setup_dae_`` function should perform
all of the changes to the DAE for this measurement configuration.
However, it should NOT make any physical changes to the instrument.

If this measurement configuration requires more complicated setups,
these can be obtained by overloading the begin, waitfor, and end
methods.  This overloading is performed by adding private methods with
the dae name appended.  For example, Larmor defined ``_begin_sesans``
to set the instrument for two periods and ``_waitfor_sesans`` to
switch between the periods and toggle the flipper during the
measurement.
