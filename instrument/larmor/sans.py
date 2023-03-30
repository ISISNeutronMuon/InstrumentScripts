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
    # change for 13-26 AA
    # _lrange = "13-26"

    @property
    def TIMINGS(self):
        if self._dae_mode == "polsans":
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
        elif lrange == "13-26":
            gen.cset(T0Phase=0)
            gen.cset(TargetDiskPhase=39750)
            gen.cset(InstrumentDiskPhase=39450)
        else:
            raise ValueError(
                "The only known lranges for the chopper "
                "are '0.9-13.25', '0.65-12.95' and '13-26AA'")

    def _generic_scan(  # pylint: disable=dangerous-default-value
            self,
            detector=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\detector.dat",
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_1To1.dat",
            wiring=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_dae3.dat",
            tcbs=[]):
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)


    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_scanning_80.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning12(self):
        """Set the wiring tables for performing a scan where the entire main
detector is contained in only two channels."""
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_scanning_12.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanningAlanis(self):  # pylint: disable=no-self-use
        """Set the wiring tables for performing a scan where the entire main
            detector is contained in channel 11 and the Alanis Detector is in channel 12."""
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_scanning_Alanis.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0}])

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning11(self):  # pylint: disable=no-self-use
        """Set the wiring tables for performing a scan where the entire main
        detector is contained in only one channel now we are using dae 3."""
        self._generic_scan(
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_scanning_11.dat",
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
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_nrscanning.dat",
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
        if self._lrange == "13-26":
            self._generic_scan(
                wiring="wiring_dae3_event.dat",
                tcbs=[{"low": 100005.0, "high": 200000.0, "step": self.get_tof_step(),
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": 100005.0, "high": 200000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2},
                  {"low": 100005.0, "high": 200000.0, "step": 100.0,
                   "trange": 1, "log": 0, "regime":3},
                  {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2,
                   "log": 0, "regime": 3}])
        #3rd time regime for monitors to allow flexible binning of detector to reduce
        #file size and decrease file write time    
        else:
        # Normal event mode with full detector binning
            self._generic_scan(
            wiring=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_dae3_event.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": self.get_tof_step(),
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2}])
            #Below is for MIEZE SANS
            # tcbs=[{"low": 5.0, "high": 100000.0, "step": self.get_tof_step(),
                   # "trange": 1, "log": 0},
                  # {"low": 0.0, "high": 0.0, "step": 0.0,
                   # "trange": 2, "log": 0},
                  # {"low": 22222.0, "high": 86222.0, "step": 1.0, "trange": 1,
                   # "log": 0, "regime": 2}])
        self._set_choppers(self._lrange)

    @dae_setter("SANS", "sans")
    def setup_dae_event_tshift(self):
        self._generic_scan(
        wiring="wiring_dae3_event.dat",
        tcbs=[{"low": 7000.0, "high": 107000.0, "step": self.get_tof_step(),
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0},
                  {"low": 7000.0, "high": 107000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2}])
    

    @dae_setter("SANS", "sans")
    def setup_dae_event_fastsave(self):
        """Event mode with reduced detector histogram binning to decrease
        filesize."""
        # Event mode with reduced detector histogram binning to
        # decrease filesize
        # This currently breaks mantid nexus read
        self._generic_scan(
            wiring=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_event_fastsave.dat",
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
                  {"low": 5.0, "high": 100000.0, "step": self.get_tof_step(),
                   "trange": 1, "log": 0, "regime": 3},
                  {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2,
                   "log": 0, "regime": 3}])
        self._set_choppers(self._lrange)

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        #gen.change_sync('isis')
        self._generic_scan(
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 100.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])
        self._set_choppers(self._lrange)

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        #gen.change_sync('isis')
        if self._lrange == "13-26":
            self._generic_scan(
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\detector_monitors_only.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_monitors_only.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_dae3_monitors_only.dat",
            [{"low": 100005.0, "high": 200000.0, "step": 100.0,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0}])
        else:
            self._generic_scan(
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\detector_monitors_only.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_monitors_only.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_dae3_monitors_only.dat",
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
            wiring=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_tshift.dat",
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
            spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_phase1.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 20.0,
                   "trange": 1, "log": 0},
                  {"low": 0.0, "high": 0.0, "step": 0.0,
                   "trange": 2, "log": 0}])

    @dae_setter("SANS", "sans")
    def setup_dae_resonantimaging(self):
        """Set the wiring table for resonant imaging"""
        self._generic_scan(
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\detector_monitors_only.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_monitors_only.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring_monitors_only.dat",
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
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\detector.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_4To1.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\wiring.dat",
            [{"low": 5.0, "high": 100000.0, "step": 100.0,
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0, "trange": 2, "log": 0}])

    @dae_setter("POLSANS", "polsans")
    def setup_dae_polsans(self):
        """Setup the instrument for POLSANS measurements."""
        self.setup_dae_event()


    @staticmethod
    def _begin_polsans():
        """Initialise a POLSANS run"""
        gen.change(nperiods=2)
        gen.begin(paused=1)


    @staticmethod
    def _waitfor_polsans(up_state_frames=600, down_state_frames=600, **kwargs):
        """Perform a POLSANS run"""
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

    @dae_setter("POLTRANS", "poltrans")
    def setup_dae_poltrans(self):
        """Setup the instrument for POLSANS transmission measurements."""
        self.setup_dae_transmission()

    @staticmethod
    def _begin_poltrans():
        """Initialise a POLSANS transmission run"""
        Larmor._begin_polsans()  


    @dae_setter("SEMSANS", "semsans")
    def setup_dae_alanis(self):
        """Setup the instrument for using the Alanis fibre detector"""
        self._generic_scan(
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Detector.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Spectra.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Wiring_dae3.dat",
            [{"low": 5.0, "high": 100000.0, "step": self.get_tof_step(),
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0},
             {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
              "log": 0, "regime": 2}])

    @dae_setter("SEMSANS", "semsans")
    def setup_dae_semsans(self):
        """Setup the instrument for polarised SEMSANS on the fibre detector"""
        self._generic_scan(
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Detector.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Spectra.dat",
            r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Wiring_dae3.dat",
            [{"low": 5.0, "high": 100000.0, "step": self.get_tof_step(),
              "trange": 1, "log": 0},
             {"low": 0.0, "high": 0.0, "step": 0.0,
              "trange": 2, "log": 0},
             {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
              "log": 0, "regime": 2}])

    @dae_setter("SESANS", "sesans")
    def setup_dae_sesans(self):
        """Setup the instrument for SESANS measurements."""
        self.setup_dae_alanis()

    @staticmethod
    def _begin_semsans():
        """Initialise a SEMSANS run"""
        Larmor._begin_polsans()

    @staticmethod
    def _begin_sesans():
        """Initialise a SESANS run"""
        Larmor._begin_polsans()        

    @staticmethod
    def _waitfor_semsans(up_state_frames=600, down_state_frames=600, **kwargs):
        """Perform a SEMSANS run"""
        Larmor._waitfor_polsans(up_state_frames, down_state_frames, **kwargs)

    @staticmethod
    def _waitfor_sesans(up_state_frames=600, down_state_frames=600, **kwargs):
        """Perform a SANSPOL run"""
        Larmor._waitfor_polsans(up_state_frames, down_state_frames, **kwargs)      

    @dae_setter("PASANS", "pasans")
    def setup_dae_pasans(self):
        """Setup the instrument for Polarisation Analysis SANS measurements."""
        #As there is no monitor after the analyser on Larmor a transmisson is 
        #done with an attenuated direct beam measured on main detector with 
        #beamstop removed. This operation needs reversing for scattering mode.
        beam_stop_in_out(stop_in=True)
        gen.waitfor_move()
        gen.cset(A1HGap=25)                
        gen.cset(A1VGap=25)
        gen.waitfor_move()
        self.setup_dae_event()

    @staticmethod
    def _begin_pasans():
        """Initialise a polarisation analysis SANS run"""
        gen.change(nperiods=4)
        gen.begin(paused=1)   

    @staticmethod
    def _waitfor_pasans(no_flip_state_frames=600, flip_state_frames=600, **kwargs):
        """Perform a polarisation analysis SANS run"""
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
            no_flip_state_frames=no_flip_state_frames/10
            flip_state_frames=flip_state_frames/10

        while gtotal < kwargs[key]:
            gen.change(period=1)
            info("Flipper On")
            flipper1(1)
            info("Analyser On State")            
            self.send_pv('3HE:STATE', 1)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=no_flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + no_flip_state_frames)
                gen.pause()

            gen.change(period=2)
            info("Flipper Off")
            flipper1(0)
            info("Analyser On State")            
            self.send_pv('3HE:STATE', 1)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + flip_state_frames)
                gen.pause()     

            gen.change(period=3)
            info("Flipper Off")
            flipper1(0)
            info("Analyser Off State")            
            self.send_pv('3HE:STATE', 0)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=no_flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + no_flip_state_frames)
                gen.pause()                            

            gen.change(period=4)
            info("Flipper On")
            flipper1(1)
            info("Analyser On State")            
            self.send_pv('3HE:STATE', 0)            
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:LARMOR:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + flip_state_frames)
                gen.pause()
                gtotal = get_total()         

    @dae_setter("PATRANS", "patrans")
    def setup_dae_patrans(self):
        """Setup the instrument for polarisation analysis SANS transmission measurements."""
        #As there is no monitor after the analyser on Larmor the attenuated direct beam
        #is measured on main detector and beamstop removed.
        gen.cset(A1HGap=4)                
        gen.cset(A1VGap=4)
        gen.waitfor_move()
        beam_stop_in_out(stop_in=False)
        gen.waitfor_move()
        self.setup_dae_event()


    @staticmethod
    def _begin_patrans():
        """Initialise a polarisation analysis SANS transmission run"""
        Larmor._begin_pasans()                 

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
        gen.waitfor_move()

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.cset(m4trans=0.0)
        gen.waitfor_move()

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = all([
            self.get_pv(
                "CAEN:hv0:0:{}:status".format(x)).lower() == "on"
            for x in [8, 9, 10, 11]])
        return voltage_status

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
            gen.cset(Beamstop_Pos=317)
        else:
            gen.cset(Beamstop_Pos=0)

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

    def laserpost():
        print("Move to the position for aligning the laser using the post")
        print("home x, y, coarse z and fine z.")
        print("leave x and fine z at home positions.")
        cset(translation=-13.8)
        cset(CoarseHeight=-133.5) 


obj = Larmor()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
