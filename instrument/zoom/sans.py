"""This is the instrument implementation for the Zoom beamline."""

from logging import info, warning
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
#from genie_python import genie as gen obsolete and not used by other instrument
from technique.sans.util import dae_setter
from general.scans.util import local_wrapper
from .util import flipper1, flipper_on, flipper_off

def sleep(seconds):
    """Override the sleep function to use genie.

    We need this override to ensure that simulated runs are forced to
    wait for real sleeps."""
    return gen.waitfor(seconds=seconds)

class Zoom(ScanningInstrument):
    """This class handles the Zoom beamline, it is an extension
    of the Scanning instrument class."""
    def __init__(self):
        super().__init__()
        #self._set_poslist_dls()

    def _generic_scan(self, detector, spectra, wiring="detector_1det_1dae3card.dat", tcbs=None):
        # Explicitly check and then set to default value to avoid UB.
        if tcbs is None:
            tcbs = [{"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1,
                   "log": 0, "regime": 2}]
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)

    @property
    def TIMINGS(self):
        if self._dae_mode == "polsans" or self._dae_mode == "poltrans":
            return self._TIMINGS + ["up_state_frames", "down_state_frames"]
        if self._dae_mode == "pasans" or self._dae_mode == "patrans":
            return self._TIMINGS + ["no_flip_state_frames", "flip_state_frames"]    
        return self._TIMINGS         

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
   
        gen.change_sync('ISIS')
        gen.change_vetos(ext0=True) 
        print("Setting DAE into event mode")
        self._generic_scan(
            detector="detector_1det_1dae3card.dat",
            spectra="spec2det_280318_to_test_18_1.txt",
            wiring="wiring1det_event_200218.dat",tcbs = [{"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2}])
     
    @dae_setter("SANS", "sans")
    def setup_dae_event_m5(self):
        gen.change_sync("isis")
        gen.change_vetos(ext0=True)
        print("Setting DAE into event mode")
        self._generic_scan(
            detector="wiring_1det_mon5_event_250925.dat",
            spectra="spec2det_280318_to_test_18_1.txt",
            wiring="wiring1det_event_200218.dat",tcbs = [{"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 5.0, "high": 100000.0, "step": 2.0, "trange": 1,
                   "log": 0, "regime": 2}])       

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        gen.change_sync("isis")
        gen.change_vetos(ext0=True)
        self._generic_scan(
            detector="detector_1det_1dae3card.dat",
            spectra="spec2det_130218.txt",
            wiring="wiring1det_histogram_200218.dat")

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        gen.change_sync("isis")
        gen.change_vetos(ext0=True)
        print("Setting up DAE for trans")
        self._generic_scan(
            detector="detector_8mon_1dae3card_00.dat",
            spectra="spectrum_8mon_1dae3card_00.dat",
            wiring="wiring_8mon_1dae3card_00_hist.dat")
            
    @staticmethod
    def _begin_transmission():
        """Initialise a POLSANS run"""
        gen.change(nperiods=1)            
        gen.begin(paused=0)
        
    @dae_setter("SANS", "sans")
    def setup_dae_event_tshift(self):
        gen.change_sync("isis")
        gen.change_vetos(ext0=True)
        #second frame for 10-25 AA
        self._generic_scan(
            detector="detector_1det_1dae3card.dat",
            spectra="spec2det_280318_to_test_18_1.txt",
            wiring="wiring1det_event_200218.dat",
            tcbs=[{"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1,
                   "log": 0, "regime": 2}])    

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission_tshift(self):
        gen.change_sync("isis")
        gen.change_vetos(ext0=True)
        #second frame for 10-25 AA
        print("Setting up DAE for trans")
        self._generic_scan(
            detector="detector_8mon_1dae3card_00.dat",
            spectra="spectrum_8mon_1dae3card_00.dat",
            wiring="wiring_8mon_1dae3card_00_hist.dat",
            tcbs=[{"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1,
                   "log": 0, "regime": 2}])    

    @dae_setter("SANS", "sans")
    def setup_dae_polsans(self):
        """Setup the instrument for POLSANS measurements."""
        self.setup_dae_event()

    @staticmethod
    def _begin_polsans():
        """Initialise a POLSANS run"""
        gen.change(nperiods=2)
        gen.begin(paused=1)     

    @dae_setter("TRANS", "transmission")
    def setup_dae_poltrans(self):
        """Setup the instrument for POLSANS transmission measurements."""
        self.setup_dae_transmission()
              

    @staticmethod
    def _begin_poltrans():
        """Initialise a POLSANS transmission run"""
        gen.change(nperiods=2)
        gen.begin(paused=1)           

    @staticmethod
    def _waitfor_polsans(up_state_frames=300, down_state_frames=300, **kwargs):
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
            gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            up_state_frames=up_state_frames/10
            down_state_frames=down_state_frames/10
        
        flipper_on()
        while gtotal < kwargs[key]:
            gen.change(period=1)
            print("Flipper On")
            flipper1(1)
            if key == "seconds":
                gen.resume()                
                gen.waitfor(seconds=up_state_frames)
                gen.pause()
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + up_state_frames)
                gen.pause()

            gen.change(period=2)
            print("Flipper Off")
            flipper1(0)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=down_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + down_state_frames)
                gen.pause()
                gtotal = get_total()  

    @staticmethod
    def _waitfor_poltrans(up_state_frames=300, down_state_frames=300, **kwargs):
        """Setup the instrument for POLSANS transmission measurements."""
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
            gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            up_state_frames=up_state_frames/10
            down_state_frames=down_state_frames/10
        
        flipper_on()
        while gtotal < kwargs[key]:
            gen.change(period=1)
            print("Flipper On")
            flipper1(1)
            if key == "seconds":
                gen.resume()                
                gen.waitfor(seconds=up_state_frames)
                gen.pause()
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + up_state_frames)
                gen.pause()

            gen.change(period=2)
            print("Flipper Off")
            flipper1(0)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=down_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + down_state_frames)
                gen.pause()
                gtotal = get_total()          

    @dae_setter("SANS", "sans")
    def setup_dae_pasans(self):
        """Setup the instrument for Polarisation Analysis SANS measurements."""
        self.setup_dae_event()

    @staticmethod
    def _begin_pasans():
        """Initialise a polarisation analysisSANS run"""
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
            gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            no_flip_state_frames=no_flip_state_frames/10
            flip_state_frames=flip_state_frames/10
        
        flipper_on()
        while gtotal < kwargs[key]:
            gen.change(period=1)
            print("Flipper On")
            flipper1(1)
            print("Analyser On State")            
            self.send_pv('3HE:STATE', 1)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=no_flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + no_flip_state_frames)
                gen.pause()

            gen.change(period=2)
            print("Flipper Off")
            flipper1(0)
            print("Analyser On State")            
            self.send_pv('3HE:STATE', 1)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + flip_state_frames)
                gen.pause()     

            gen.change(period=3)
            print("Flipper Off")
            flipper1(0)
            print("Analyser Off State")            
            self.send_pv('3HE:STATE', 0)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=no_flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + no_flip_state_frames)
                gen.pause()                            

            gen.change(period=4)
            print("Flipper On")
            flipper1(1)
            print("Analyser On State")            
            self.send_pv('3HE:STATE', 0)            
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + flip_state_frames)
                gen.pause()
                gtotal = get_total()         

    @dae_setter("TRANS", "trans")
    def setup_dae_patrans(self):
        """Setup the instrument for polarisation analysis SANS transmission measurements."""
        self.setup_dae_transmission()
                        
         
    @staticmethod
    def _begin_patrans():
        """Initialise a polarisation analysis Trans run"""
        gen.change(nperiods=4)
        gen.begin(paused=1)       

    @staticmethod
    def _waitfor_patrans(no_flip_state_frames=600, flip_state_frames=600, **kwargs):
        """Setup the instrument for POLSANS transmission measurements."""
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
            gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            no_flip_state_frames=no_flip_state_frames/10
            flip_state_frames=flip_state_frames/10
        
        flipper_on()
        while gtotal < kwargs[key]:
            gen.change(period=1)
            print("Flipper On")
            flipper1(1)
            print("Analyser On State")            
            #gen.set_pv('3HE:STATE', 1)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=no_flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + no_flip_state_frames)
                gen.pause()

            gen.change(period=2)
            print("Flipper Off")
            flipper1(0)
            print("Analyser On State")            
            #gen.set_pv('3HE:STATE', 1)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + flip_state_frames)
                gen.pause()     

            gen.change(period=3)
            print("Flipper Off")
            flipper1(0)
            print("Analyser Off State")            
            #gen.set_pv('3HE:STATE', 0)
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=no_flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + no_flip_state_frames)
                gen.pause()                            

            gen.change(period=4)
            print("Flipper On")
            flipper1(1)
            print("Analyser On State")            
            #gen.set_pv('3HE:STATE', 0)            
            if key == "seconds":
                gen.resume()
                gen.waitfor(seconds=flip_state_frames)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + flip_state_frames)
                gen.pause()
                gtotal = get_total()        
                
    def set_aperture(self, size):
        if size.upper() == "SMALL":
            # JAWS
            gen.cset(J1_HCENT=0) #Center jaws
            gen.cset(J1_VCENT=0)
            gen.cset(J2_VCENT=0)
            gen.cset(J2_HCENT=0)
            gen.cset(J3_VCENT=0) 
            gen.cset(J3_HCENT=0) 
            gen.cset(J4_VCENT=0)
            gen.cset(J4_HCENT=0)
            #gen.cset(J1_VGAP=16) physical source size
            #gen.cset(J1_HGAP=26)
            gen.cset(J1_VGAP=20)
            gen.cset(J1_HGAP=20)
            gen.cset(J2_VGAP=20)
            gen.cset(J2_HGAP=20)
            gen.cset(J3_VGAP=20) #(widely open ~71x71)
            gen.cset(J3_HGAP=20) #(widely open ~71x71)
            gen.cset(J4_VGAP=12)
            gen.cset(J4_HGAP=12)
        elif size.upper() == "MEDIUM":
            # JAWS
            gen.cset(J1_HCENT=0) #Center jaws
            gen.cset(J1_VCENT=0)
            gen.cset(J2_VCENT=0)
            gen.cset(J2_HCENT=0)
            gen.cset(J3_VCENT=0) 
            gen.cset(J3_HCENT=0) 
            gen.cset(J4_VCENT=0)
            gen.cset(J4_HCENT=0)
            gen.cset(J1_VGAP=20) 
            gen.cset(J1_HGAP=20)
            gen.cset(J2_VGAP=20)
            gen.cset(J2_HGAP=20)
            gen.cset(J3_VGAP=20) #(widely open ~71x71)
            gen.cset(J3_HGAP=20) #(widely open ~71x71)
            gen.cset(J4_VGAP=12)
            gen.cset(J4_HGAP=12)
        elif size.upper() == "LARGE":
            gen.cset(J1_HCENT=0) #Center jaws
            gen.cset(J1_VCENT=0)
            gen.cset(J2_VCENT=0)
            gen.cset(J2_HCENT=0)
            gen.cset(J3_VCENT=0) 
            gen.cset(J3_HCENT=0) 
            gen.cset(J4_VCENT=0)
            gen.cset(J4_HCENT=0)
            gen.cset(J1_VGAP=30) 
            gen.cset(J1_HGAP=30)
            gen.cset(J2_VGAP=30)
            gen.cset(J2_HGAP=30)
            gen.cset(J3_VGAP=30) #(widely open ~71x71)
            gen.cset(J3_HGAP=30) #(widely open ~71x71)
            gen.cset(J4_VGAP=15)
            gen.cset(J4_HGAP=15)
        else:
            info("Apertures unchanged")

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = all([
            self.get_pv(
                "CAEN:hv0:4:{}:status".format(x)).lower() == "on"
            for x in range(8)])
        print(voltage_status)
        return voltage_status

    def _detector_turn_on(self, delay=True):
        for i in range(8):
            self.send_pv(f"CAEN:hv0:4:{i}:pwonoff", "On")
        if delay:
            print("Waiting For Detector To Power Up (120s)")
            gen.waitfor(seconds = 120)    

    def _detector_turn_off(self, delay=True):
        for i in range(8):
            self.send_pv(f"CAEN:hv0:4:{i}:pwonoff", "Off")

        if delay:
            print("Waiting For Detector To Power Down (120s)")
            gen.waitfor(seconds = 120)
                        
    def _configure_sans_custom(self):
        # move the transmission monitor out
        self.send_pv("VACUUM:MONITOR:2:EXTRACT","EXTRACT")
        self.send_pv("VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

    def _configure_trans_custom(self):
        # move the transmission monitor in
        self.send_pv("VACUUM:MONITOR:2:EXTRACT","EXTRACT")
        self.send_pv("VACUUM:MONITOR:4:INSERT", "INSERT")

# These settings has been used for second frame for 10-25 AA
#    def _configure_sans_custom(self): 
#        # move the transmission monitor out
#        self.send_pv("VACUUM:MONITOR:2:INSERT","INSERT")
#        self.send_pv("VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

#    def _configure_trans_custom(self):
#        # move the transmission monitor in
#        self.send_pv("VACUUM:MONITOR:2:INSERT","INSERT")
#        self.send_pv("VACUUM:MONITOR:4:INSERT", "INSERT")        



    def col_8m():
        print("8m configuration:choppers, colimator")
        gen.cset("PGC_Unit",101.45)
        gen.cset("Chopper_Disk2",97000)
        
    def col_10m():
        print("10m configuration:choppers, colimator")
        gen.cset("PGC_Unit",101.45)
        gen.cset("Chopper_Disk2",93000)        
        
    def set_ZOOM_SC_10m_8mm(self, BeamStop_X=27, BeamStop_Y=765):
        #Based on ZOOM setup: 261, scans 2026-5-21 
        print("Setup ZOOM for 8m configuration")
        
        
        # CHOPPERS
        gen.cset(target_chopper_freq=10)
        gen.cset(Chopper_Disk1=3000)
        gen.cset(inst_chopper_freq=10)
        gen.cset(Chopper_Disk2=93000)

        # JAWS
        gen.cset(J1_HCENT=0) #Center jaws
        gen.cset(J1_VCENT=0)
        gen.cset(J2_VCENT=0)
        gen.cset(J2_HCENT=0)
        gen.cset(J3_VCENT=0) 
        gen.cset(J3_HCENT=0) 
        gen.cset(J4_VCENT=0)
        gen.cset(J4_HCENT=0)
        gen.cset(J1_VGAP=20)
        gen.cset(J1_HGAP=30)
        gen.cset(J2_VGAP=16)
        gen.cset(J2_HGAP=16)
        gen.cset(J3_VGAP=16) 
        gen.cset(J3_HGAP=16)
        gen.cset(J4_VGAP=13)
        gen.cset(J4_HGAP=13)
        
        
        # PGC unit (Polariser or Guide or Collimator)
        self.send_pv("IN:ZOOM:LKUP:PGC:POSN:SP","Collimator") #Collimator in
        gen.waitfor_move()
        # BEAMSTOPPERS and MONITOR
        #Small_BS =out
        gen.cset(BeamStop_disc_x=-17.36)# it was -482 and -477
        gen.cset(BeamStop_disc_y=0)

        #Beamstop Monitor in
        gen.cset(BeamStop_monitor_x=BeamStop_X)
        gen.cset(BeamStop_monitor_y=BeamStop_Y)

        #gen.cset(Strip_beamstop=2831)

        # DETECTORS and BAFFLES
        if 9400<gen.cget("Detector_Position")["value"]<9656:
            pass
        else:    
            self._detector_turn_off()
            gen.cset(Detector_Position=9600)
            #gen.wait_formove()
            gen.waitfor_move("Detector_Position") 
            gen.cset(Baffle_Position=2000)
            gen.waitfor_move()
            self._detector_turn_on()
        
        
        print("Set Points for 10m SC_8mm COMPLETED!")            

    def set_ZOOM_SC_8m_8mm(self, BeamStop_X=25, BeamStop_Y=758):
        #Based on ZOOM setup: 261, scans 2026-5-21 
        print("Setup ZOOM for 8m configuration")
        
        
        # CHOPPERS
        gen.cset(target_chopper_freq=10)
        gen.cset(Chopper_Disk1=3000)
        gen.cset(inst_chopper_freq=10)
        gen.cset(Chopper_Disk2=97000)

        # JAWS
        gen.cset(J1_HCENT=0) #Center jaws
        gen.cset(J1_VCENT=0)
        gen.cset(J2_VCENT=0)
        gen.cset(J2_HCENT=0)
        gen.cset(J3_VCENT=0) 
        gen.cset(J3_HCENT=0) 
        gen.cset(J4_VCENT=0)
        gen.cset(J4_HCENT=0)
        gen.cset(J1_VGAP=30)
        gen.cset(J1_HGAP=20)
        gen.cset(J2_VGAP=20)
        gen.cset(J2_HGAP=20)
        gen.cset(J3_VGAP=20) 
        gen.cset(J3_HGAP=20) 
        gen.cset(J4_VGAP=13)
        gen.cset(J4_HGAP=13)
        
        
        # PGC unit (Polariser or Guide or Collimator)
        self.send_pv("IN:ZOOM:LKUP:PGC:POSN:SP","Collimator") #Collimator in
        gen.waitfor_move()
        # BEAMSTOPPERS and MONITOR
        #Small_BS =out
        gen.cset(BeamStop_disc_x=-17.36)# it was -482 and -477
        gen.cset(BeamStop_disc_y=0)

        #Beamstop Monitor in
        gen.cset(BeamStop_monitor_x=BeamStop_X)
        gen.cset(BeamStop_monitor_y=BeamStop_Y)

        #gen.cset(Strip_beamstop=2831)

        # DETECTORS and BAFFLES
        if 7800<gen.cget("Detector_Position")["value"]<8200:
            pass
        else:    
            self._detector_turn_off()
            gen.cset(Detector_Position=8000)
            #gen.wait_formove()
            gen.waitfor_move("Detector_Position") 
            gen.cset(Baffle_Position=2000)
            gen.waitfor_move()
            self._detector_turn_on()
        
        
        print("Set Points for 8m SC_8mm COMPLETED!")        

    def guide_4m():    
        print("4m configuration:choppers, guide")
        gen.cset("PGC_Unit",0)
        gen.cset("Chopper_Disk2",99000)

    def check_detector_on(self):

        print("Check ZOOM detector status")
        self._detector_is_on()
        
    def turn_detector_on(self):

        print("Turn ZOOM detector ON")
        self._detector_turn_on()       

    def turn_detector_off(self):

        print("Turn ZOOM detector OFF")
        self._detector_turn_off()               
    
    def set_ZOOM_SC_4m_8mm(self, BeamStop_X=25, BeamStop_Y=765):
        #Based on ZOOM setup: 261, scans 2026-5-21 
        
        # CHOPPERS	
        gen.cset(target_chopper_freq=10)
        gen.cset(Chopper_Disk1=3000)
        gen.cset(inst_chopper_freq=10)
        gen.cset(Chopper_Disk2=99000)

        # JAWS
        gen.cset(J1_HCENT=0) #Center jaws
        gen.cset(J1_VCENT=0)
        gen.cset(J2_VCENT=0)
        gen.cset(J2_HCENT=0)
        gen.cset(J3_VCENT=0) 
        gen.cset(J3_HCENT=0) 
        gen.cset(J4_VCENT=0)
        gen.cset(J4_HCENT=0)
        gen.cset(J1_VGAP=22) 
        gen.cset(J1_HGAP=30)
        gen.cset(J2_VGAP=25)
        gen.cset(J2_HGAP=25)
        gen.cset(J3_VGAP=22)
        gen.cset(J3_HGAP=22) 
        gen.cset(J4_VGAP=15)
        gen.cset(J4_HGAP=15)
        
        # PGC_Unit (Polariser or Guide or Collimator)
        self.send_pv("IN:ZOOM:LKUP:PGC:POSN:SP","Guide") #Guide in
        gen.waitfor_move()
        # BEAMSTOPPERS and MONITOR
        #Small_BS =out
        gen.cset(BeamStop_disc_x=-17.36)# it was -482 and -477
        gen.cset(BeamStop_disc_y=0)

        #Beamstop Monitor
        gen.cset(BeamStop_monitor_x=BeamStop_X)
        gen.cset(BeamStop_monitor_y=BeamStop_Y)

        #gen.cset(Strip_beamstop=2831) #not in use when in 2831

        # DETECTORS and BAFFLES
        if 3800<gen.cget("Detector_Position")["value"]<4200:
            pass
        else:    
            self._detector_turn_off()
            gen.cset(Baffle_Position=0)  
            gen.waitfor_move('Baffle_Position')
            gen.cset(Detector_Position=4000)     
            gen.waitfor_move('Detector_Position')    
            self._detector_turn_on()
            
        print("Set Points for 4m_20_8mm COMPLETED!")
        
    def set_ZOOM_SC_4m_12mm(self, BeamStop_X=-40.76, BeamStop_Y=765):
        #Based on ZOOM setup: 224D?, Blend1_ZOOM Run 26793
        #Date/Time: 2022-12-01, Checked with logbook/page#: 5/?
        #and more recently:
        #RT5 run 38067; user235C-4m_Small_BS; Date/Time: 2024-02-15 logbook/page#: 7/39
        print("Setup ZOOM for 4m configuration")
        
        # CHOPPERS	
        gen.cset(target_chopper_freq=10)
        gen.cset(Chopper_Disk1=3000)
        gen.cset(inst_chopper_freq=10)
        gen.cset(Chopper_Disk2=99000)

        # JAWS
        gen.cset(J1_HCENT=0) #Center jaws
        gen.cset(J1_VCENT=0)
        gen.cset(J2_VCENT=0)
        gen.cset(J2_HCENT=0)
        gen.cset(J3_VCENT=0) 
        gen.cset(J3_HCENT=0) 
        gen.cset(J4_VCENT=0)
        gen.cset(J4_HCENT=0)
        gen.cset(J1_VGAP=20) 
        gen.cset(J1_HGAP=30)
        gen.cset(J2_VGAP=20)
        gen.cset(J2_HGAP=30)
        gen.cset(J3_VGAP=71) #(widely open ~71x71)
        gen.cset(J3_HGAP=71) #(widely open ~71x71)
        gen.cset(J4_VGAP=15)
        gen.cset(J4_HGAP=15)
        
        # PGC_Unit (Polariser or Guide or Collimator)
        self.send_pv("IN:ZOOM:LKUP:PGC:POSN:SP","Guide") #Guide in
        gen.waitfor_move()
        # BEAMSTOPPERS and MONITOR
        #Small_BS =out
        gen.cset(BeamStop_disc_x=-17.36)# it was -482 and -477
        gen.cset(BeamStop_disc_y=0)

        #Beamstop Monitor
        gen.cset(BeamStop_monitor_x=BeamStop_X)
        gen.cset(BeamStop_monitor_y=BeamStop_Y)

        #gen.cset(Strip_beamstop=2831) #not in use when in 2831

        # DETECTORS and BAFFLES
        if 3800<gen.cget("Detector_Position")["value"]<4200:
            pass
        else:    
            self._detector_turn_off()
            gen.cset(Baffle_Position=0)  
            gen.waitfor_move('Baffle_Position')
            gen.cset(Detector_Position=4000)     
            gen.waitfor_move('Detector_Position')    
            self._detector_turn_on()
            
        print("Set Points for 4m_20_12mm COMPLETED!")        
   

    def polariser_4m(self):
        #Based on ZOOM setup: 261, scans 2026-5-21 
        print("4m configuration:choppers, polariser")
        gen.cset("PGC_Unit",-125.5)
        gen.cset("Chopper_Disk2",99000)
        gen.cset(J1_HCENT=0) #Center jaws
        gen.cset(J1_VCENT=0)
        gen.cset(J2_VCENT=0)
        gen.cset(J2_HCENT=0)
        gen.cset(J3_VCENT=0) 
        gen.cset(J3_HCENT=0) 
        gen.cset(J4_VCENT=0)
        gen.cset(J4_HCENT=0)
        gen.cset("J1_VGAP",30) 
        gen.cset("J1_HGAP",30)
        #reflection for J2 larger than 15x15 from polariser
        gen.cset(J2_VGAP=30)
        gen.cset(J2_HGAP=30)
        gen.cset(J3_VGAP=20) 
        gen.cset(J3_HGAP=20) 
        gen.cset("J4_VGAP",14) 
        gen.cset("J4_HGAP",14)      
        gen.waitfor_move()
        
    def polariser_8m(self):    
        print("8m configuration:choppers, polariser")
        gen.cset("PGC_Unit",-125.5)
        gen.cset("Chopper_Disk2",97000)
        gen.cset(J1_HCENT=0) #Center jaws
        gen.cset(J1_VCENT=0)
        gen.cset(J2_VCENT=0)
        gen.cset(J2_HCENT=0)
        gen.cset(J3_VCENT=0) 
        gen.cset(J3_HCENT=0) 
        gen.cset(J4_VCENT=0)
        gen.cset(J4_HCENT=0)
        gen.cset("J1_VGAP",20) 
        gen.cset("J1_HGAP",20)
        #reflection for J2 larger than 15x15 from polariser
        gen.cset("J2_VGAP",15) 
        gen.cset("J2_HGAP",15)    
        gen.cset(J3_VGAP=15) 
        gen.cset(J3_HGAP=15)        
        gen.cset("J4_VGAP",14) 
        gen.cset("J4_HGAP",14) 
        gen.waitfor_move()
        
#    def reset_sample_stack_limits(self):
#        #Y/Sample Changer Motion
#        self.send_pv("IN:ZOOM:MOT:MTR0402.HLM",300)
#        self.send_pv("IN:ZOOM:MOT:MTR0402.LLM",-300)
#        #Large Z
#        self.send_pv("IN:ZOOM:MOT:MTR0407.HLM",200)
#        self.send_pv("IN:ZOOM:MOT:MTR0407.LLM",-50)   

    def setup_quiet_counts():
        gen.change_sync("internal test clock")
        gen.change_vetos(ext0=False)
        print("Setting DAE for quiet counts")
      

obj = Zoom()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
