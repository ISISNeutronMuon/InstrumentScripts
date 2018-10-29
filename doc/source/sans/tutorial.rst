Tutorial
********

.. highlight:: python
   :linenothreshold: 20

.. py:currentmodule:: src.Instrument

.. Boilerplate setup

    The commands below are for creating a simple testing system in the
    tutorial.  This merely guarantees that the tutorial is always in sync
    with the actual behaviour of the software.  The tutorial proper begins
    in the next section.

    >>> import logging
    >>> import sys
    >>> import os
    >>> ch = logging.StreamHandler(sys.stdout)
    >>> ch.setLevel(logging.INFO)
    >>> logging.getLogger().setLevel(logging.INFO)
    >>> logging.getLogger().addHandler(ch)
    >>> from technique.sans.genie import gen

Basic examples
==============

.. py:currentmodule:: technique.sans.instrument

First, we'll just do a simple measurement on the main detector for 600
frames.

>>> from instrument.larmor.sans import *
>>> do_sans("Sample Name", frames=600)
Setup Larmor for event
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample Name_SANS for 600 frames
>>> do_trans("Sample Name", frames=180)
Setup Larmor for transmission
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample Name_TRANS for 180 frames

The :py:meth:`ScanningInstrument.do_sans` and
:py:meth:`ScanningInstrument.do_trans` functions are both simple
wrappers around :py:meth:`ScanningInstrument.measure`.  ``measure`` is
the primary entry point for all types of SANS measurement.  All of the
parameters that will be covered for measure can also be applied to
``do_sans`` and ``do_trans``. Below is an example of the extended
information that can be passed to these functions.

>>> measure("Sample Name", "QT", aperature="Medium", blank=True, uamps=5)
Setup Larmor for event
Moving to sample changer position QT
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample Name_SANS for 5 uamps

A couple of things changed with this new command.

1. I've measured for 5 µamps instead of the 600 frames we did before.
   The measure command will take and of the time commands that
   genie_python's ``waitfor`` command will accept, though ``uamps``,
   ``frames``, and ``seconds`` will almost always be the ones which
   are needed.

2. We've passed sample position QT in as the position parameter and
   the instrument has dutifully moved into position QT before starting
   the measurement.

#. We specified the beam size.  The individual beamlines will have the
   opportunity to decide their own aperature settings, but they should
   hopefully reach a consensus on the names.

#. The sample has been marked as a blank.  The MEASUREMENT:TYPE block
   in the run's journal entry will be set to "blank", instead of
   "sans".  Had this been a transmission measurement, the block would
   have been set to "blank_transmission"

>>> measure("Sample Name", CoarseZ=25, uamps=5, thickness=2.0, trans=True, blank=True)
Setup Larmor for transmission
Moving CoarseZ to 25
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=2.0
Measuring Sample Name_TRANS for 5 uamps

Here we are directly setting the CoarseZ motor on the sample stack to
our desired position, instead of just picking a position for the
sample changer.  We have also recorded that this run is on a 2 mm
sample, unlike our previous 1 mm runs.  Finally, the instrument has
converted into transmission mode, setting the appropriate wiring
tables and moving the M4 monitor into the beam.

>>> measure("Sample Name", "CT", SampleX=10, Julabo1_SP=35, uamps=5)
Setup Larmor for event
Moving to sample changer position CT
Moving Julabo1_SP to 35
Moving SampleX to 10
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample Name_SANS for 5 uamps

We can combine a sample changer position with motor movements.  This
is useful for custom mounting that may not perfectly align with the
sample changer positions.  Alternately, since any block can be set
within the measure command, it is also possible to set temperatures
and other beam-line parameters for a measurement.

>>> def weird_place():
...   gen.cset(Translation=100)
...   gen.cset(CoarseZ=-75)
>>> measure("Sample Name", weird_place, Julabo1_SP=37, uamps=10)
Moving to position weird_place
Moving Julabo1_SP to 37
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample Name_SANS for 10 uamps

Finally, if the experiment requires a large number of custom
positions, they can be set independently in their own functions.
Measure can then move to that position as though it were a standard
sample changer position.  It's still possible to override or amend
these custom positions with measurement specific values, as we have
done above with the Julabo temperature again.

>>> measure("Sample Name", 7, Julabo1_SP=37, uamps=10)
Traceback (most recent call last):
...
TypeError: Cannot understand position 7

If the position is gibberish, the instrument will raise an error and
not try to start a measurement in an unknown position.


>>> set_default_dae(setup_dae_bsalignment)
>>> measure("Beam stop", frames=300)
Setup Larmor for bsalignment
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Beam stop_SANS for 300 frames

The default DAE mode for all SANS measurements is event mode.  This
can be overridden with the
:py:meth:`ScanningInstrument.set_default_dae` function, which will
assign a new default SANS method.  This new event mode will be used
for all future SANS measurements.  For brevity, the
:py:meth:`ScanningInstrument.set_default_dae` will also take a string
argument.  The first line can also be run as

>>> set_default_dae("bsalignment")

It's similarly possible to set the default dae for transmission measurements.

>>> set_default_dae("bsalignment", trans=True)
>>> set_default_dae("transmission", trans=True)

>>> measure("Beam stop", dae="event", frames=300)
Setup Larmor for event
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Beam stop_SANS for 300 frames

The :py:meth:`ScanningInstrument.measure` function also has a ``dae``
keyword parameter that is automatically passed to
:py:meth:`ScanningInstrument.setup_default_dae`.  The above example puts the instrument
back into event mode.

>>> enumerate_dae()
['4periods', 'bsalignment', 'diffraction', 'event', 'event_fastsave', 'histogram', 'monitorsonly', 'monotest', 'nr', 'nrscanning', 'polarised', 'resonantimaging', 'resonantimaging_choppers', 'scanning', 'sesans', 'transmission', 'tshift']

The :py:meth:`ScanningInstrument.enumerate_dae` function will list all
of the supported dae modes on the current beamline.

Automated script checking
=========================

.. py:currentmodule:: technique.sans.util

This module includes a decorator :py:meth:`user_script` that can be
added to the front of any user function.  This will allow the
scripting system to scan the script for common problems before it is
run, ensuring that problems are noticed immediately and not at one in
the morning.  All that's required of the user is putting
``@user_script`` on the line before any functions that they define.

>>> @user_script
... def trial(time, trans):
...     measure("Test1", "BT", uamps=time)
...     measure("Test2", "VT", uamps=time)
...     measure("Test1", "BT", trans=True, uanps=trans)
...     measure("Test2", "VT", trans=True, uamps=trans)
>>> trial(30, trans=10)
Traceback (most recent call last):
...
RuntimeError: Position VT does not exist

What may not be immediately obvious from reading is that this error
message occurs instantly, not forty five minutes into the run after
the first measurement has already been performed.  Fixing the "VT"
positions to "CT" then gives:

>>> @user_script
... def trial():
...     measure("Test1", "BT", uamps=30)
...     measure("Test2", "CT", uamps=30)
...     measure("Test1", "BT", trans=True, uanps=10)
...     measure("Test2", "CT", trans=True, uamps=10)
>>> trial()
Traceback (most recent call last):
...
RuntimeError: Unknown Block uanps

Again, an easy typo to make at midnight that normally would not be
found until two in the morning.

>>> @user_script
... def trial():
...     measure("Test1", "BT", uamps=30)
...     measure("Test2", "CT", uamps=30)
...     measure("Test1", "BT", trans=True, uamps=10)
...     measure("Test2", "CT", trans=True, uamps=10)
>>> trial() #doctest:+ELLIPSIS
The script should finish in 2.0 hours
...
Measuring Test2_TRANS for 10 uamps

Once the script has been validated, which should happen nearly
instantly, the program will print an estimate of the time needed for
the script and the approximate time of completion (not shown).  It
will then run the script for real.

Large script handling
=====================

.. py:currentmodule:: technique.sans.instrument

The :py:meth:`ScanningInstrument.measure_file` function allows the
user to define everything in a CSV file with excel and then run it
through python.

.. csv-table:: test.csv
  :file: test.csv
  :header-rows: 1

>>> measure_file("test/test.csv") #doctest:+ELLIPSIS
The script should finish in 3.0 hours
...
Measuring Sample5_TRANS for 20 uamps

The particular keyword argument to the
:py:meth:`ScanningInstrument.measure` function is given in the header
on the first line of the file.  Each subsequent line represents a
single run with the parameters given in the columns of that row.  If
an argument is left blank, then the keyword's default value is used.
The boolean values ``True`` and ``False`` are case insensitive, but all other
strings retain their case.

.. csv-table:: bad_julabo.csv
  :file: bad_julabo.csv
  :header-rows: 1

>>> measure_file("test/bad_julabo.csv") #doctest:+ELLIPSIS
Traceback (most recent call last):
...
RuntimeError: Unknown Block Julabo

.. py:currentmodule:: src.Util

Each CSV file is run through the :py:func:`user_script`
function defined `above`__, so the script will be checked for errors before being run.
In the example above, the user set the column header to "Julabo", but
the actual block name is "Julabo1_SP".

__ `Automated script checking`_

If we fix the script file

.. csv-table:: good_julabo.csv
  :file: good_julabo.csv
  :header-rows: 1

>>> measure_file("test/good_julabo.csv") #doctest:+ELLIPSIS
The script should finish in 1.0 hours
...
Measuring Sample3_SANS for 6000 frames

The scan then runs as normal.

>>> measure_file("test/good_julabo.csv", forever=True) # doctest: +SKIP

If the users are leaving and you want to ensure that the script keeps
taking data until they return, the ``forever`` flag causes the
instrument to repeatedly cycle through the script until there is a
manual intervention at the keyboard.  The output is not shown above
because there is infinite output.

>>> from __future__ import print_function
>>> convert_file("test/good_julabo.csv")
>>> with open("test/good_julabo.csv.py", "r") as infile:
...     for line in infile:
...         print(line[:-1])
from SansScripting import *
@user_script
def good_julabo():
    do_sans("Sample1", "AT", thickness=1, uamps=10)
    do_trans("Sample2", "AT", thickness=1, uamps=5)
    do_trans("Sample2", "BT", thickness=1, uamps=5)
    do_sans("Sample2", "BT", thickness=1, uamps=10)
    do_trans("Sample3", "CT", frames=3000, thickness=2)
    do_sans("Sample3", "CT", frames=6000, thickness=2)

When the user is ready to take the next step into full python
scripting, the CSV file can be turned into a python source file that
performs identical work.  This file can then be edited and customised
to the user's desires.


Detector Status
===============

As an obvious sanity check, it is possible to check if the detector is on.

>>> detector_on()
True

We can also power cycle the detector.

>>> detector_on(False)
Waiting For Detector To Power Down (60s)
False

If we try to perform a measurement with the detector off, then the
measurement will fail.

>>> measure("Sample", frames=100)
Traceback (most recent call last):
...
RuntimeError: The detector is off.  Either turn on the detector or use the detector_lock(True) to indicate that the detector is off intentionally

Performing transmission measurements does not require the detector

>>> detector_on(False)
Waiting For Detector To Power Down (60s)
False
>>> measure("Sample", trans=True, frames=100)
Setup Larmor for transmission
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample_TRANS for 100 frames
>>> detector_on(True)
Waiting For Detector To Power Up (180s)
True

If the detector needs to run in a special configuration (e.g. due to
electrical problems), the detector state can be locked.  This will
prevent attempts to turn the detector on and off and will bypass any
checks for the detector state:

>>> detector_lock()
False
>>> detector_on(False)
Waiting For Detector To Power Down (60s)
False
>>> detector_lock(True)
True
>>> measure("Sample", frames=100)
Setup Larmor for event
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Sample_SANS for 100 frames
>>> detector_on(True)
Traceback (most recent call last):
...
RuntimeError: The instrument scientist has locked the detector state
>>> detector_lock(False)
False
>>> detector_on(True)
Waiting For Detector To Power Up (180s)
True

Custom Running Modes
====================

Some modes may be much more complicated than a simple sans
measurement.  For example, a SESANS measurement needs to setup the DAE
for two periods, manage the flipper state, and switch between those
periods.  From the user's perspective, this is all handled in the same
manner as a normal measurement.

>>> set_default_dae(setup_dae_sesans)
>>> measure("SESANS Test", frames=6000)
Setup Larmor for sesans
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring SESANS Test_SESANS for 6000 frames
Flipper On
Flipper Off
Flipper On
Flipper Off
Flipper On
Flipper Off
Flipper On
Flipper Off
Flipper On
Flipper Off

.. py:currentmodule:: instruments.larmor.sans

In this example, the instrument scientist has written two functions
:py:meth:`Larmor._begin_sesans` and :py:meth:`Larmor._waitfor_sesans`
which handle the SESANS specific nature of the measurement.

>>> measure("SESANS Test", u=1500, d=1500, uamps=10)
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring SESANS Test_SESANS for 10 uamps
Flipper On
Flipper Off
Flipper On
Flipper Off
Flipper On
Flipper Off

.. py:currentmodule:: technique.sans.instrument

These custom mode also allow more default parameters to be added onto
:py:meth:`ScanningInstrument.measure`.  In this instance, the ``u``
and ``d`` parameters set the number of frames in the up and down
states.

Reduction Script Generation
===========================

.. py:currentmodule:: technique.sans.reduction

A small amount of metadata is attached to each run.  It's possible to
generate a reduction script from this metadata.

>>> from technique.sans.auto_reduction import *
>>> d = sesans_connection(0, 110, path="test/sans.xml")

The variable d will hold every possible sesans measurement that could
be collected from runs 29200 through 29309 in a nested dictionary.
The orders of the keys will be the sample name, the blank name, and
finally the magnet angle.

>>> d["example in pure h2o"]["h2o blank"]["20.0"] == {'Sample': [88, 98, 107], 'P0Trans': [89], 'P0': [90, 99, 108], 'Trans': [87]}
True

Once we've chose out instrument parameters, we get a labelled set of
run numbers which describe the reduction that we want to perform.

>>> sesans_reduction("test/sesans_out.py", d, {"example in pure h2o": "h2o blank"})

:py:meth:`sesans_reduction` take a file name, the connected sesans data, and a
dictionary where the keys are the sample names and the values are the
appropriate blanks for those samples.  A python script is written to
the file which will perform the data reduction in Mantid for those
given runs.


  .. literalinclude:: sesans_out.py
     :caption: sesans_out.py

.. test
   >>> with open("test/sesans_out.py", "r") as infile:
   ...     len(infile.readlines())
   3

The above code can use the sesans reduction library to create .SES
files for all of the desired runs.

.. comment
   The function below can be safely ignored.  It exists as part of our
   testing framework to automate the interactive parts of our tests.

   >>> def test_oracle(sample, blanks):
   ...    print("What is the blank for the sample: {}".format(sample))
   ...    for idx, blank in enumerate(blanks):
   ...        print("{}: {}".format(idx+1, blank))
   ...    if "solution" in sample:
   ...       print("2")
   ...       return "example solvent 1mm cell"
   ...    elif "h2o" in sample:
   ...        print("3")
   ...        return "h2o blank"
   ...    elif "bear" in sample:
   ...        print("1")
   ...        return "air blank"

For the majority of simple cases, we can use the
:py:meth:`identify_pairs` to save us on much of the boiler plate of
reducing samples.

>>> d = sans_connection(70, 110, path="test/sesans.xml")
>>> pairs = identify_pairs(d, oracle=test_oracle)
What is the blank for the sample: example in pure h2o
1: air blank
2: example solvent 1mm cell
3: h2o blank
3
What is the blank for the sample: example solution 23 1mm cell
1: air blank
2: example solvent 1mm cell
3: h2o blank
2
What is the blank for the sample: polar bear p1 across hairs
1: air blank
2: example solvent 1mm cell
3: h2o blank
1
What is the blank for the sample: polar bear p1 along hairs
1: air blank
2: example solvent 1mm cell
3: h2o blank
1
What is the blank for the sample: polar bear p2 across hairs
1: air blank
2: example solvent 1mm cell
3: h2o blank
1
What is the blank for the sample: polar bear p2 along hairs
1: air blank
2: example solvent 1mm cell
3: h2o blank
1

In the above, :py:meth:`identify pairs` asked the user to find the
correct blank for each sample, which the user gave by submitting a
number.  This then creates the pairs dictionary, like the one manually
created above, but with less effort and typing.  This can then be used
in the sans_reduction or sesans_reduction, as normal.

.. note:: The `oracle` parameter was only needed in this instance
   because we're inside the test framework.  Under normal conditions,
   that parameter can be ignored.

>>> sans_reduction("test/sans_out.py", d, pairs, "Mask.txt", direct=85)

The :py:meth:`sans_reduction` function takes the same parameters as
:py:meth:`sesans_reduction`, plus two more.  The first is a mask file,
as is used by all SANS reduction scripts.  The second is the run
number for the direct run.

  .. literalinclude:: sans_out.py
     :caption: sans_out.py

.. test
   >>> with open("test/sans_out.py", "r") as infile:
   ...     len(infile.readlines())
   40

Under the hood
==============

>>> gen.reset_mock()
>>> measure("Test", "BT", dae="event", aperature="Medium", uamps=15)
Setup Larmor for event
Moving to sample changer position BT
Using the following Sample Parameters
Geometry=Flat Plate
Width=10
Height=10
Thick=1.0
Measuring Test_SANS for 15 uamps

This command returns no result, but should cause a large number of
actions to be run through genie-python.  We can verify those actions
through the mock genie object that's created when the actual
genie-python isn't found.

>>> print(gen.mock_calls)
[call.get_runstate(),
 call.get_pv('IN:LARMOR:CAEN:hv0:0:8:status'),
 call.get_pv('IN:LARMOR:CAEN:hv0:0:9:status'),
 call.get_pv('IN:LARMOR:CAEN:hv0:0:10:status'),
 call.get_pv('IN:LARMOR:CAEN:hv0:0:11:status'),
 call.set_pv('IN:LARMOR:PARS:SAMPLE:MEAS:TYPE', 'sesans'),
 call.change(nperiods=1),
 call.change_start(),
 call.change_tables(detector='C:\\Instrument\\Settings\\Tables\\detector.dat'),
 call.change_tables(spectra='C:\\Instrument\\Settings\\Tables\\spectra_1To1.dat'),
 call.change_tables(wiring='C:\\Instrument\\Settings\\Tables\\wiring_event.dat'),
 call.change_tcb(high=100000.0, log=0, low=5.0, step=100.0, trange=1),
 call.change_tcb(high=0.0, log=0, low=0.0, step=0.0, trange=2),
 call.change_tcb(high=100000.0, log=0, low=5.0, regime=2, step=2.0, trange=1),
 call.change_finish(),
 call.cset(T0Phase=0),
 call.cset(TargetDiskPhase=2750),
 call.cset(InstrumentDiskPhase=2450),
 call.cset(m4trans=200.0),
 call.set_pv('IN:LARMOR:PARS:SAMPLE:MEAS:LABEL', 'Test'),
 call.cset(a1hgap=20.0, a1vgap=20.0, s1hgap=14.0, s1vgap=14.0),
 call.cset(SamplePos='BT'),
 call.waitfor_move(),
 call.change_sample_par('Thick', 1.0),
 call.get_sample_pars(),
 call.change(title='Test_SANS'),
 call.begin(),
 call.waitfor(uamps=15),
 call.end()]

That's quite a few commands, so it's worth running through them.

:2: Ensure that the instrument is ready to start a measurement
:3-6: Check that the detector is on
:7: Check that the detector is on
:8-19: Put the instrument in event mode
:20: Move the M4 transmission monitor out of the beam
:21: Set the upstream slits
:22: Move the sample into position
:23: Let motors finish moving.
:24: Set the sample thickness
:25: Print and log the sample parameters
:26: Set the sample title
:27: Start the measurement.
:28: Wait the requested time
:29: Stop the measurement.
