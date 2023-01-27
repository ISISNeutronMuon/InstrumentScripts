"""This is the instrument implementation for the Larmor beamline."""
from logging import info
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
from technique.sans.util import dae_setter
from general.scans.util import local_wrapper
from .util import flipper1


def sleep(seconds):
    """Override the sleep function to use genie.

    We need this override to ensure that simularted runs are forced to
    wait for real sleeps."""
    return gen.waitfor(seconds=seconds)


class Larmor(ScanningInstrument):  # pylint: disable=too-many-public-methods
    """This class handles the Larmor beamline, it is an extension
    of the Scanning instrument class.
    """

    _step = 100.0
    _lrange = "0.9-13.25"
    # change the default for Edler June 2019
    # _lrange = "0.65-12.95"

    @property
    def TIMINGS(self):
        if self._dae_mode == "sesans":
            return self._TIMINGS + ["u", "d"]
        return self._TIMINGS

    def get_lrange(self):
        """Return the current wavelength range"""
        return self._lrange

    def set_lrange(self, lrange):
        """Set the current wavelength range"""
        self._dae_mode = ""
        self._lrange = lrange

    def get_tof_step(self):
        """Get the current TOF step for the tcb"""
        return self._step

    def set_tof_step(self, step):
        """Set the current TOF step for the tcb"""
        self._dae_mode = ""
        self._step = step

    @staticmethod
    def _set_choppers(lrange):
        # now set the chopper phasing to the defaults
        # T0 phase checked for November 2015 cycle
        # Running at 5Hz and centering the dip from the T0 at 50ms by
        # setting phase to 48.4ms does not stop the fast flash
        # Setting the T0 phase to 0 (50ms) does
        if lrange == "0.9-13.25":
            gen.cset(T0Phase=0)
            gen.cset(TargetDiskPhase=2750)
            gen.cset(InstrumentDiskPhase=2450)
        elif lrange == "0.65-12.95":
            gen.cset(TargetDiskPhase=1900)
            gen.cset(InstrumentDiskPhase=1600)
        else:
            raise ValueError(
                "The only known lranges for the chopper "
                "are '0.9-13.25' and '0.65-12.95'")

    def _generic_scan(self, detector="detector.dat", spectra="spectra_1To1.dat", wiring="wiring_dae3.dat", tcbs=None):
        # Explicitly check and then set to empty list to avoid UB.
        if tcbs is None:
            tcbs = []
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        self._generic_scan(
            spectra="spectra_scanning_80.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning12(self):
        """Set the wiring tables for performing a scan where the entire main
detector is contained in only two channels."""
        self._generic_scan(
            spectra="spectra_scanning_12.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanningAlanis(self):
        """Set the wiring tables for performing a scan where the entire main
            detector is contained in channel 11 and the Alanis Detector is in channel 12."""
        self._generic_scan(
            spectra="spectra_scanning_Alanis.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning11(self):
        """Set the wiring tables for performing a scan where the entire main
        detector is contained in only one channel now we are using dae 3."""
        self._generic_scan(
            spectra="spectra_scanning_11.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_echoscan(self):
        """Set the wiring tables for performing a spin echo tuning scan.  This
involves only having two spectra covering the entire main detecor."""
        self.setup_dae_scanning12()

    @dae_setter("SCAN", "scan")
    def setup_dae_nr(self):
        self._generic_scan(
            spectra="spectra_nrscanning.dat",
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
            wiring="wiring_dae3_event.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": self._step,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2}])
        self._set_choppers(self._lrange)

    @dae_setter("SANS", "sans")
    def setup_dae_event_fastsave(self):
        """Event mode with reduced detector histogram binning to decrease
        filesize."""
        # Event mode with reduced detector histogram binning to
        # decrease filesize
        # This currently breaks mantid nexus read
        self._generic_scan(
            wiring="wiring_event_fastsave.dat",
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
                  {"low": 5.0, "high": 100000.0, "step": self._step,
                   "trange": 1, "log": 0, "regime": 3},
                  {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2,
                   "log": 0, "regime": 3}])
        self._set_choppers(self._lrange)

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        gen.change_sync('isis')
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])
        self._set_choppers(self._lrange)

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        gen.change_sync('isis')
        self._generic_scan(
            "detector_monitors_only.dat",
            "spectra_monitors_only.dat",
            "wiring_dae3_monitors_only.dat",
            [{"low": 5.0, "high": 100000.0, "step": 100.0,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0}])
        self._set_choppers(self._lrange)

    @dae_setter("TRANS", "transmission")
    def setup_dae_monotest(self):
        """Setup with a mono test?"""
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])
        gen.cset(T0Phase=0)
        self.send_pv("MK3CHOPR_01: CH2: DIR: SP", "CW")
        gen.cset(TargetDiskPhase=8200)
        self.send_pv("MK3CHOPR_01: CH3: DIR: SP", "CCW")
        gen.cset(InstrumentDiskPhase=77650)

    @dae_setter("SANS", "sans")
    def setup_dae_tshift(self, tlowdet=5.0, thighdet=100000.0, tlowmon=5.0,
                         thighmon=100000.0):
        """Allow m1 to count as normal but to shift the rest of the detectors
        in order to allow counting over the frame.

        """
        self._generic_scan(
            wiring="wiring_tshift.dat",
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
            spectra="spectra_phase1.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 20.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])

    @dae_setter("SANS", "sans")
    def setup_dae_resonantimaging(self):
        """Set the wiring table for resonant imaging"""
        self._generic_scan(
            "detector_monitors_only.dat",
            "spectra_monitors_only.dat",
            "wiring_monitors_only.dat",
            [{"low": 5.0, "high": 1500.0, "step": 0.256,
              "trange": 1, "log": 0},
             {"low": 1500.0, "high": 100000.0, "step": 100.0,
              "trange": 2, "log": 0}])

    @staticmethod
    @dae_setter("SANS", "sans")
    def setup_dae_resonantimaging_choppers():
        """Set the wiring thable for resonant imaging choppers"""
        info("Setting Chopper phases")
        gen.cset(T0Phase=49200)
        gen.cset(TargetDiskPhase=0)
        gen.cset(InstrumentDiskPhase=0)

    @dae_setter("SANS", "sans")
    def setup_dae_4periods(self):
        """Setup the instrument with four periods."""
        self._generic_scan(
            "detector.dat",
            "spectra_4To1.dat",
            "wiring.dat",
            [{"low": 5.0, "high": 100000.0, "step": 100.0,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2, "log": 0}])

    @dae_setter("SESANS", "sesans")
    def setup_dae_sesans(self):
        """Setup the instrument for SESANS measurements."""
        # self.setup_dae_event()
        self.setup_dae_alanis()



    @staticmethod
    def _begin_sesans():
        """Initialise a SESANS run"""
        gen.change(nperiods=2)
        gen.begin(paused=1)

    @staticmethod
    def _waitfor_sesans(up_state_frames=600, down_state_frames=600, **kwargs):
        """Perform a SESANS run"""
        if "uamps" in kwargs:
            get_total = gen.get_uamps
            key = "uamps"
        elif "seconds" in kwargs:
            get_total = gen.get_uamps
            key = "seconds"
        else:
            get_total = gen.get_frames
            key = "frames"
        gfrm = gen.get_frames()
        gtotal = get_total()

        if key == "seconds":
            gtotal=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
            up_state_frames=up_state_frames/10
            down_state_frames=down_state_frames/10

        while gtotal < kwargs[key]:
            gen.change(period=1)
            info("Flipper On")
            flipper1(1)
            if key == "seconds":
                gen.resume()
                ttime=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
                gen.waitfor(seconds=(gtotal+up_state_frames)-ttime)
                gen.pause()
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + up_state_frames)
                gen.pause()

            gen.change(period=2)
            info("Flipper Off")
            flipper1(0)
            if key == "seconds":
                gen.resume()
                ttime=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
                gen.waitfor(seconds=(gtotal+up_state_frames+down_state_frames)-ttime)
                gen.pause()
                gtotal=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + down_state_frames)
                gen.pause()
                gtotal = get_total()

    @dae_setter("SEMSANS", "semsans")
    def setup_dae_alanis(self):
        """Setup the instrument for using the Alanis fibre detector"""
        self._generic_scan(
            "Alanis_Detector.dat",
            "Alanis_Spectra.dat",
            "Alanis_Wiring_dae3.dat",
            [{"low": 5.0, "high": 100000.0, "step": self._step,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0},
             {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
              "log": 0, "regime": 2}])

    @dae_setter("SEMSANS", "semsans")
    def setup_dae_semsans(self):
        """Setup the instrument for polarised SEMSANS on the fibre detector"""
        self._generic_scan(
            "Alanis_Detector.dat",
            "Alanis_Spectra.dat",
            "Alanis_Wiring_dae3.dat",
            [{"low": 5.0, "high": 100000.0, "step": self._step,
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
    def _waitfor_semsans(up_state_frames=600, down_state_frames=600, **kwargs):
        """Perform a SESANS run"""
        Larmor._waitfor_sesans(up_state_frames, down_state_frames, **kwargs)

    @staticmethod
    def set_aperture(size):
        if size.upper() == "SMALL":
            pass
        elif size.upper() == "MEDIUM":
            gen.cset(a1hgap=20.0, a1vgap=20.0, s1hgap=14.0, s1vgap=14.0)
        elif size.upper() == "LARGE":
            pass
        else:
            info("Aperture unchanged")


    def _configure_sans_custom(self):
        # move the transmission monitor out
        gen.cset(m4trans=200.0)

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.cset(m4trans=0.0)

    def _detector_is_on(self):
        """Is the detector currently on?"""
        return all(self.get_pv(f"CAEN:hv0:0:{x}:status").lower() == "on" for x in range(8, 12))

    def _detector_turn_on(self, delay=True):
        for i in range(8, 12):
            self.send_pv(f"CAEN:hv0:0:{i}:pwonoff", "On")

        if delay:
            info("Waiting For Detector To Power Up (180s)")
            sleep(180)

    def _detector_turn_off(self, delay=True):
        for i in range(8, 12):
            self.send_pv(f"CAEN:hv0:0:{i}:pwonoff", "Off")

        if delay:
            info("Waiting For Detector To Power Down (60s)")
            sleep(60)

    @staticmethod
    def frame_overload_mirror_in():
        """Put the frame overload mirror into the beam."""
        # gen.cset(pol_trans=0, pol_arc=-1.6)
        # Convert to angle instead of mm
        gen.cset(pol_trans=0, pol_arc=-0.084)

    @staticmethod
    def short_polariser_in():
        """Put the short polariser for long wavelength into the beam."""
        # gen.cset(pol_trans=-100, pol_arc=-1.3)
        # Convert to angle instead of mm
        gen.cset(pol_trans=-100, pol_arc=-0.069)

    @staticmethod
    def long_polariser_in():
        """Put the long polariser for short wavelengths into the beam."""
        # gen.cset(pol_trans=100, pol_arc=-1.3)
        # Convert to angle instead of mm
        gen.cset(pol_trans=100, pol_arc=-0.069)

    @staticmethod
    def beam_stop_in_out(stop_in=True):
        """Move the Beam Stop in and out of the beam.

        Parameters
        ----------
        stop_in : bool
          Whether to move the beam stop in or out
        """
        # move beam stop in or out. The default is to move in
        if stop_in:
            gen.cset(BSY=88.5, BSZ=353.0)
        else:
            gen.cset(BSY=200.0, BSZ=0.0)

    def _generic_home_slit(self, slit):
        # home north and west
        self.send_pv(slit + "JN:MTR.HOMR", 1)
        self.send_pv(slit + "JW:MTR.HOMR", 1)
        gen.waitfor_move()
        self.send_pv(slit + "JN:MTR.VAL", "20")
        self.send_pv(slit + "JW:MTR.VAL", "20")
        # home south and east
        self.send_pv(slit + "JS:MTR.HOMR", 1)
        self.send_pv(slit + "JE:MTR.HOMR", 1)
        gen.waitfor_move()
        self.send_pv(slit + "JS:MTR.VAL", "20")
        self.send_pv(slit + "JE:MTR.VAL", "20")
        gen.waitfor_move()

    def home_coarse_jaws(self):
        """Rehome coarse jaws."""
        info("Homing Coarse Jaws")
        gen.cset(cjhgap=40, cjvgap=40)
        gen.waitfor_move()
        self._generic_home_slit("MOT:JAWS1:")

    def home_a1(self):
        """Rehome aperture 1."""
        info("Homing a1")
        gen.cset(a1hgap=40, a1vgap=40)
        self._generic_home_slit("MOT:JAWS2:")
        gen.waitfor_move()

    def home_s1(self):
        """Rehome slit1."""
        info("Homing s1")
        gen.cset(s1hgap=40, s1vgap=40)
        gen.waitfor_move()
        self._generic_home_slit("MOT:JAWS3:")

    @staticmethod
    def home_s2():
        """Rehome slit2. This is currently a no-op."""
        info("Homing s2. Not implemented.")

    def move_bench(self, angle=0.0, delaydet=True):
        """Safely move the downstream arm"""
        info("Turning Detector Off")
        self.detector_on(False, delay=delaydet)
        self.rotate_bench(angle)
        # turn the detector back on
        info("Turning Detector Back on")
        self.detector_on(True, delay=delaydet)

    def rotate_bench(self, angle=0.0):
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
        self.send_pv("SDTEST_01: P2: COMM", script[0])
        for line in script[1:]:
            sleep(1)
            self.send_pv("SDTEST_01: P2: COMM", line)

    def home_pi_rotation(self):
        """Calibrate the pi flipper."""
        self.send_pv("SDTEST_01: P2: COMM", "FRF 1")


obj = Larmor()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
