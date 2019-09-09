"""This is the instrument implementation for the Larmor beamline."""
from logging import info
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
# pylint: disable=unused-import
from technique.sans.util import dae_setter, user_script  # noqa: F401
from general.scans.util import local_wrapper
from .util import flipper1


def sleep(seconds):
    """Override the sleep function to use genie.

    We need this override to ensure that simularted runs are forced to
    wait for real sleeps."""
    return gen.waitfor(seconds=seconds)


class Larmor(ScanningInstrument):  # pylint: disable=too-many-public-methods
    """This class handles the Larmor beamline"""

    step = 100.0
    lrange = "0.9-13.25"
    _PV_BASE = "IN:LARMOR:"

    # change the default for Edler June 2019
    # lrange = "0.65-12.95"

    @property
    def TIMINGS(self):
        if self._dae_mode == "sesans":
            return self._TIMINGS + ["u", "d"]
        return self._TIMINGS

    def get_lrange(self):
        """Return the current wavelength range"""
        return self.lrange

    def set_lrange(self, lrange):
        """Set the current wavelength range"""
        self._dae_mode = ""
        self.lrange = lrange

    def get_tof_step(self):
        """Get the current TOF step for the tcb"""
        return self.step

    def set_tof_step(self, step):
        """Set the current TOF step for the tcb"""
        self._dae_mode = ""
        self.step = step

    def _generic_scan(  # pylint: disable=dangerous-default-value
            self,
            detector=r"C:\Instrument\Settings\Tables\detector.dat",
            spectra=r"C:\Instrument\Settings\Tables\spectra_1To1.dat",
            wiring=r"C:\Instrument\Settings\Tables\wiring.dat",
            tcbs=[]):
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)

    @staticmethod
    def _set_choppers(lrange):
        # now set the chopper phasing to the defaults
        # T0 phase checked for November 2015 cycle
        # Running at 5Hz and centering the dip from the T0 at 50ms by
        # setting phase to 48.4ms does not stop the fast flash
        # Setting the T0 phase to 0 (50ms) does
        if lrange == "0.9-13.25":
            # This is for 0.9-13.25
            gen.cset(T0Phase=0)
            gen.cset(TargetDiskPhase=2750)
            gen.cset(InstrumentDiskPhase=2450)
        elif lrange == "0.65-12.95":
            # This is for 0.65-12.95
            gen.cset(TargetDiskPhase=1900)
            gen.cset(InstrumentDiskPhase=1600)
        else:
            raise RuntimeError(
                "The only known lranges for the chopper "
                "are '0.9-13.25' and '0.65-12.95'")

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\Tables\spectra_scanning_80.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning12(self):  # pylint: disable=no-self-use
        """Set the wiring tables for performing a scan where the entire main
detector is contained in only two channels."""
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\Tables\spectra_scanning_12.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_echoscan(self):  # pylint: disable=no-self-use
        """Set the wiring tables for performing a spin echo tuning scan.  This
involves only having two spectra covering the entire main detecor."""
        self.setup_dae_scanning12()

    @dae_setter("SCAN", "scan")
    def setup_dae_nr(self):
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\Tables\spectra_nrscanning.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_nrscanning(self):
        self._generic_scan(
            spectra=r"U:\Users\Masks\spectra_scanning_auto.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
        # Normal event mode with full detector binning
        self._generic_scan(
            wiring=r"C:\Instrument\Settings\Tables\wiring_event.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": self.step,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2}])
        self._set_choppers(self.lrange)

    @dae_setter("SANS", "sans")
    def setup_dae_event_fastsave(self):
        """Event mode with reduced detector histogram binning to decrease
        filesize."""
        # Event mode with reduced detector histogram binning to
        # decrease filesize
        # This currently breaks mantid nexus read
        self._generic_scan(
            wiring=r"C:\Instrument\Settings\Tables\wiring_event_fastsave.dat",
            # change to log binning to reduce number of detector bins
            # by a factor of 10 to decrease write time
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 0.1,
                   "trange": 1, "log": 1},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2},
                  # 3rd time regime for monitors to allow flexible
                  # binning of detector to reduce file size and
                  # decrease file write time
                  {"low": 5.0, "high": 100000.0, "step": self.step,
                   "trange": 1, "log": 0, "regime": 3},
                  {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2,
                   "log": 0, "regime": 3}])
        self._set_choppers(self.lrange)

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        gen.change_sync('isis')
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])
        self._set_choppers(self.lrange)

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        self.set_pv("PARS:SAMPLE:MEAS:TYPE", "transmission")
        gen.change_sync('isis')
        self._generic_scan(
            r"C:\Instrument\Settings\Tables\detector_monitors_only.dat",
            r"C:\Instrument\Settings\Tables\spectra_monitors_only.dat",
            r"C:\Instrument\Settings\Tables\wiring_monitors_only.dat",
            [{"low": 5.0, "high": 100000.0, "step": 100.0,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0}])
        self._set_choppers(self.lrange)

    @dae_setter("TRANS", "transmission")
    def setup_dae_monotest(self):
        """Setup with a mono test?"""
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])
        gen.cset(T0Phase=0)
        self.set_pv("MK3CHOPR_01: CH2: DIR: SP", "CW")
        gen.cset(TargetDiskPhase=8200)
        self.set_pv("MK3CHOPR_01: CH3: DIR: SP", "CCW")
        gen.cset(InstrumentDiskPhase=77650)

    @dae_setter("SANS", "sans")
    def setup_dae_tshift(self, tlowdet=5.0, thighdet=100000.0, tlowmon=5.0,
                         thighmon=100000.0):
        """Allow m1 to count as normal but to shift the rest of the detectors
        in order to allow counting over the frame.

        """
        self._generic_scan(
            wiring=r"C:\Instrument\Settings\Tables\wiring_tshift.dat",
            tcbs=[{"low": tlowdet, "high": thighdet, "step": 100.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": tlowmon, "high": thighmon, "step": 20.0, "trange": 1,
                   "log": 0, "regime": 3}])

    @dae_setter("SANS", "sans")
    def setup_dae_diffraction(self):
        """Set the wiring tables for a diffraction measurement"""
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 0.01,
                   "trange": 1, "log": 1},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])

    @dae_setter("SANS", "sans")
    def setup_dae_polarised(self):
        """Set the wiring tables for a polarisation measurement."""
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0, "trange": 1},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])

    @dae_setter("SANS", "sans")
    def setup_dae_bsalignment(self):
        self._generic_scan(
            tcbs=[{"low": 1000.0, "high": 100000.0, "step": 99000.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])

    @dae_setter("TRANS", "transmission")
    def setup_dae_monitorsonly(self):
        """Set the wiring tables to record only the monitors."""
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\Tables\spectra_phase1.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 20.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])

    @dae_setter("SANS", "sans")
    def setup_dae_resonantimaging(self):
        """Set the wiring table for resonant imaging"""
        self._generic_scan(
            r"C:\Instrument\Settings\Tables\detector_monitors_only.dat",
            r"C:\Instrument\Settings\Tables\spectra_monitors_only.dat",
            r"C:\Instrument\Settings\Tables\wiring_monitors_only.dat",
            [{"low": 5.0, "high": 1500.0, "step": 0.256,
              "trange": 1, "log": 0},
             {"low": 1500.0, "high": 100000.0, "step": 100.0,
              "trange": 2, "log": 0}])

    @staticmethod
    @dae_setter("SANS", "sans")
    def setup_dae_resonantimaging_choppers():  # pylint: disable=invalid-name
        """Set the wiring thable for resonant imaging choppers"""
        info("Setting Chopper phases")
        gen.cset(T0Phase=49200)
        gen.cset(TargetDiskPhase=0)
        gen.cset(InstrumentDiskPhase=0)

    @dae_setter("SANS", "sans")
    def setup_dae_4periods(self):
        """Setup the instrument with four periods."""
        self._generic_scan(
            r"C:\Instrument\Settings\Tables\detector.dat",
            r"C:\Instrument\Settings\Tables\spectra_4To1.dat",
            r"C:\Instrument\Settings\Tables\wiring.dat",
            [{"low": 5.0, "high": 100000.0, "step": 100.0,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2, "log": 0}])

    @dae_setter("SESANS", "sesans")
    def setup_dae_sesans(self):
        """Setup the instrument for SESANS measurements."""
        self.setup_dae_event()

    @staticmethod
    def _begin_sesans():
        """Initialise a SESANS run"""
        gen.change(nperiods=2)
        gen.begin(paused=1)

    @staticmethod
    def _waitfor_sesans(u=600, d=600,
                        **kwargs):  # pylint: disable=invalid-name
        """Perform a SESANS run"""
        if "uamps" in kwargs:
            get_total = gen.get_uamps
            key = "uamps"
        else:
            get_total = gen.get_frames
            key = "frames"
        gfrm = gen.get_frames()
        gtotal = get_total()

        while gtotal < kwargs[key]:
            gen.change(period=1)
            info("Flipper On")
            flipper1(1)
            gfrm = gen.get_frames()
            gen.resume()
            gen.waitfor(frames=gfrm + u)
            gen.pause()

            gen.change(period=2)
            info("Flipper Off")
            flipper1(0)
            gfrm = gen.get_frames()
            gen.resume()
            gen.waitfor(frames=gfrm + d)
            gen.pause()

            gtotal = get_total()

    @dae_setter("SEMSANS", "semsans")
    def setup_dae_alanis(self):
        """Setup the instrument for using the Alanis fibre detector"""
        self._generic_scan(
            r"C:\Instrument\Settings\Tables\Alanis_Detector.dat",
            r"C:\Instrument\Settings\Tables\Alanis_Spectra.dat",
            r"C:\Instrument\Settings\Tables\Alanis_Wiring.dat",
            [{"low": 5.0, "high": 100000.0, "step": self.step,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0},
             {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
              "log": 0, "regime": 2}])

    @dae_setter("SEMSANS", "semsans")
    def setup_dae_semsans(self):
        """Setup the instrument for polarised SEMSANS on the fibre detector"""
        self._generic_scan(
            r"C:\Instrument\Settings\Tables\Alanis_Detector.dat",
            r"C:\Instrument\Settings\Tables\Alanis_Spectra.dat",
            r"C:\Instrument\Settings\Tables\Alanis_Wiring.dat",
            [{"low": 5.0, "high": 100000.0, "step": self.step,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0},
             {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
              "log": 0, "regime": 2}])

    @staticmethod
    def _begin_semsans():
        """Initialise a SEMSANS run"""
        Larmor._begin_sesans()

    @staticmethod
    def _waitfor_semsans(u=600, d=600,
                         **kwargs):  # pylint: disable=invalid-name
        """Perform a SESANS run"""
        Larmor._waitfor_sesans(u, d, **kwargs)

    @staticmethod
    def set_aperture(size):
        if size.upper() == "MEDIUM":
            gen.cset(a1hgap=20.0, a1vgap=20.0, s1hgap=14.0, s1vgap=14.0)

    def _configure_sans_custom(self):
        # move the transmission monitor out
        gen.cset(m4trans=200.0)

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.cset(m4trans=0.0)

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = all([
            self.get_pv(
                "CAEN:hv0:0:{}:status".format(x)).lower() == "on"
            for x in [8, 9, 10, 11]])
        return voltage_status

    def _detector_turn_on(self, delay=True):
        self.set_pv("CAEN:hv0:0:8:pwonoff", "On")
        self.set_pv("CAEN:hv0:0:9:pwonoff", "On")
        self.set_pv("CAEN:hv0:0:10:pwonoff", "On")
        self.set_pv("CAEN:hv0:0:11:pwonoff", "On")
        if delay:
            info("Waiting For Detector To Power Up (180s)")
            sleep(180)

    def _detector_turn_off(self, delay=True):
        self.set_pv("CAEN:hv0:0:8:pwonoff", "Off")
        self.set_pv("CAEN:hv0:0:9:pwonoff", "Off")
        self.set_pv("CAEN:hv0:0:10:pwonoff", "Off")
        self.set_pv("CAEN:hv0:0:11:pwonoff", "Off")
        if delay:
            info("Waiting For Detector To Power Down (60s)")
            sleep(60)

    # Instrument Specific Scripts
    @staticmethod
    def FOMin():  # pylint: disable=invalid-name
        """Put the frame overload mirror into the beam."""
        # gen.cset(pol_trans=0, pol_arc=-1.6)
        # Convert to angle instead of mm
        gen.cset(pol_trans=0, pol_arc=-0.084)

    @staticmethod
    def ShortPolariserin():  # pylint: disable=invalid-name
        """Put the short polariser for long wavelength into the beam."""
        # gen.cset(pol_trans=-100, pol_arc=-1.3)
        # Convert to angle instead of mm
        gen.cset(pol_trans=-100, pol_arc=-0.069)

    @staticmethod
    def LongPolariserin():  # pylint: disable=invalid-name
        """Put the long polariser for short wavelengths into the beam."""
        # gen.cset(pol_trans=100, pol_arc=-1.3)
        # Convert to angle instead of mm
        gen.cset(pol_trans=100, pol_arc=-0.069)

    @staticmethod
    def BSInOut(In=True):  # pylint: disable=invalid-name
        """Move the Beam Stop in and out of the beam.

        Parameters
        ----------
        In : bool
          Whether to move the beam stop in or out
        """
        # move beamstop in or out. The default is to move in
        if In:
            gen.cset(BSY=88.5, BSZ=353.0)
        else:
            gen.cset(BSY=200.0, BSZ=0.0)

    def _generic_home_slit(self, slit):
        # home north and west
        self.set_pv(slit + "JN:MTR.HOMR", 1)
        self.set_pv(slit + "JW:MTR.HOMR", 1)
        gen.waitfor_move()
        self.set_pv(slit + "JN:MTR.VAL", "20")
        self.set_pv(slit + "JW:MTR.VAL", "20")
        # home south and east
        self.set_pv(slit + "JS:MTR.HOMR", 1)
        self.set_pv(slit + "JE:MTR.HOMR", 1)
        gen.waitfor_move()
        self.set_pv(slit + "JS:MTR.VAL", "20")
        self.set_pv(slit + "JE:MTR.VAL", "20")
        gen.waitfor_move()

    def homecoarsejaws(self):
        """Rehome coarse jaws."""
        info("Homing Coarse Jaws")
        gen.cset(cjhgap=40, cjvgap=40)
        gen.waitfor_move()
        self._generic_home_slit("MOT:JAWS1:")

    def homea1(self):
        """Rehome aperture 1."""
        info("Homing a1")
        gen.cset(a1hgap=40, a1vgap=40)
        self._generic_home_slit("MOT:JAWS2:")
        gen.waitfor_move()

    def homes1(self):
        """Rehome slit1."""
        info("Homing s1")
        gen.cset(s1hgap=40, s1vgap=40)
        gen.waitfor_move()
        self._generic_home_slit("MOT:JAWS3:")

    @staticmethod
    def homes2():
        """Rehome slit2.  This is currentl a no-op."""
        info("Homing s2")

    def movebench(self, angle=0.0, delaydet=True):
        """Safely move the downstream arm"""
        info("Turning Detector Off")
        self.detector_on(False, delay=delaydet)
        self.rotatebench(angle)
        # turn the detector back on
        info("Turning Detector Back on")
        self.detector_on(True, delay=delaydet)

    def rotatebench(self, angle=0.0):
        """Move the downstream arm"""
        if self.detector_on():
            info("The detector is not turned off")
            info("Not attempting Move")
            return
        info("The detector is off")

        if angle >= -0.5:
            gen.cset(benchlift=1)
            info("Lifting Bench (20s)")
            sleep(20)

            if self.get_pv("BENCH: STATUS") == 1:
                info("Rotating Bench")
                gen.cset(bench_rot=angle)
                gen.waitfor_move()
                info("Lowering Bench (20s)")
                gen.cset(benchlift=0)
                sleep(20)
            else:
                info("Bench failed to lift")
                info("Move not attempted")

    def setup_pi_rotation(self):
        """Initialise the pi flipper."""
        script = ["*IDN?", "ERR?", "SVO 1 1", "RON 1 1",
                  "VEL 1 180", "ACC 1 90", "DEC 1 90"]
        self.set_pv("SDTEST_01: P2: COMM", script[0])
        for line in script[1:]:
            sleep(1)
            self.set_pv("SDTEST_01: P2: COMM", line)

    def home_pi_rotation(self):
        """Calibrate the pi flipper."""
        self.set_pv("SDTEST_01: P2: COMM", "FRF 1")


obj = Larmor()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
