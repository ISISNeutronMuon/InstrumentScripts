Proposed Changes
****************

.. highlight:: python
   :linenothreshold: 20

Since v 0.1 which went out on Monday, I've proposed the following
changes.

Default DAE modes
=================

Previously, to perform a sans measurement in something besides event
mode, the user would need to first set the correct event mode, then
call :py:meth:`ScanningInstrument.measure` with the keyword argument
``dae_fixed=True``.  The problem is that it's easy for the user to
forget the keyword argument, then have the instrument revert back to
event mode.

The new proposal has a :py:meth:`ScanningInstrument.set_default_sae`
function, which allows the user to change the default DAE mode for
SANS and TRANS measurements.  This is now a single step process, as
the :py:meth:`ScanningInstrument.measure` function calls the correct
DAE mode without needing an extra argument.

The biggest disadvantage to this setup is that the user might forget
that they've changed the default DAE mode.  A fresh python session
always restores the correct mode.


Custom running modes
====================

The original proposal could not perform actions *during* a
measurement.  The new proposal adds three new hooks to allow certain
modes to override the behaviour of the measure function.  The instrument class now has three members:

  :py:meth:`ScanningInstrument.begin`
      Setup and begin a measurement.  This defaults to ``gen.begin()``
  :py:meth:`ScanningInstrument.waitfor`
      Wait while the instrument collects data.  This defaults to
      ``gen.waitfor(**kwargs)``
  :py:meth:`ScanningInstrument.end`
      End the measurement.  This defaults to ``gen.end()``

However, the instrument scientist can add the function hooks
``_begin_mode``, ``_waitfor_mode``, and ``_end_mode``.  After the user
calls ``setup_dae_mode``, these hooks will be called instead of the
default values.  These hooks can then allow for arbitrary actions to
occur during the measurement.


Move TIMING into ScanningInstrument
===================================

To aid in this process, the old TIMING variable is now a property of
the `ScanningInstrument` class.  Subclasses can override this property
to allow extra timing information and keywords to be passed to
``waitfor``, instead of trying to set a motor block.
