"""This is the instrument implementation for the LOQ beamline."""
from time import sleep
from logging import warning
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
from technique.sans.util import dae_setter
from general.scans.util import local_wrapper


class LOQ(ScanningInstrument):
    """This class handles the LOQ beamline,  it is an extension
    of the Scanning instrument class."""

    def __init__(self):
        super().__init__()
        self._set_poslist_dls()

    def do_sans_large(self, title=None, pos=None, thickness=1.0,
                      dae=None, uamps=None, time=None, **kwargs):
        """
        A wrapper around do_sans with aperture set to large
        Please see measure for full documentation of parameters
        """
        self.do_sans(title=title, pos=pos, thickness=thickness, dae=dae,
                aperture="LARGE", uamps=uamps, time=time, **kwargs)

    def _generic_scan(self,
                      detector="detector35576_M4.dat",
                      spectra="spectra35576_M4.dat",
                      wiring="wiring35576_M4.dat",
                      tcbs=None):
        if tcbs is None:
            tcbs = [{"low": 3500.0, "high": 43500.0, "step": 0.025, "log": True}]
        gen.change_start()
        for trange in range(1, 6):
            gen.change_tcb(low=0, high=0, step=0, log=0,
                           trange=trange, regime=1)
            sleep(1.5)
        gen.change_tcb(low=0, high=0, step=0, log=0,
                       trange=1, regime=2)
        gen.change_finish()
        ScanningInstrument._generic_scan(
            self, detector, spectra, wiring, tcbs)

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_event(self):
        self.setup_dae_normal()

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_histogram(self):
        self.setup_dae_normal()

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        return self._generic_scan(
            detector="detector8.dat",
            spectra="spectra8.dat",
            wiring="wiring8.dat")

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_normal(self):
        """Setup LOQ for normal operation"""
        gen.change_sync("smp")
        gen.change_monitor(2, low=5000.0, high=27000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         # Set ext2=False to DISABLE moderator temperature veto
                         ext0=True, ext1=True, ext2=False, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 3500.0, "high": 43500.0, "step": 0.025,
                   "log": True},
                  {"low": 3500, "high": 43500.0, "step": 40000,
                   "log": False, "trange": 1, "regime": 2}])

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_quiet(self):
        """Setup LOQ for quiet operation"""
        gen.change_sync("internal")
        gen.change_monitor(2, low=5.0, high=20000.0)
        gen.change_vetos(clearall=True, smp=False, TS2=False,
                         ext0=False, ext1=False, ext2=False, ext3=False)
        return self._generic_scan(
            tcbs=[{"low": 5.0, "high": 19995.0, "step": 4000.0,
                   "log": False},
                  {"low": 5, "high": 19995.0, "step": 19990.0, "log": False,
                   "trange": 1, "regime": 2}])

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_50hz_short(self):
        """Setup LOQ for 50hz mode while short"""
        gen.change_sync("isis")
        gen.change_monitor(2, low=6800.0, high=17000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         ext0=True, ext1=True, ext2=True, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 6e3, "high": 1.96e4, "step": 4e2,
                   "log": False, "trange": 1},
                  {"low": 1.96e4, "high": 1.99e4, "step": 3e2,
                   "log": False, "trange": 2},
                  {"low": 1.99e4, "high": 2.08e4, "step": 1e2,
                   "log": False, "trange": 3},
                  {"low": 2.08e4, "high": 2.60e4, "step": 4e2,
                   "log": False, "trange": 4},
                  {"low": 6000, "high": 2.60e4, "step": 20000,
                   "log": False, "trange": 1, "regime": 2}])

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_50hz_long(self):
        """Setup LOQ for 50hz mode while long"""
        gen.change_sync("isis")
        gen.change_monitor(2, low=5000.0, high=27000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         ext0=True, ext1=True, ext2=True, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 2e4, "high": 3.95e4, "step": 2.5e2,
                   "log": False, "trange": 1},
                  {"low": 3.95e4, "high": 4e4, "step": 1e2,
                   "log": False, "trange": 2},
                  {"low": 20000, "high": 40000, "step": 20000,
                   "log": False, "trange": 1, "regime": 2}])

    @property
    def changer_pos(self):
        return gen.cget("Changer")["value"]

    @changer_pos.setter
    def changer_pos(self, pos):
        return gen.cset(Changer=pos)

    @staticmethod
    def set_aperture(size):
        if size == "":
            print("Aperture unchanged")
        elif size.upper() in ["SMALL", "MEDIUM", "LARGE"]:
            gen.cset(Aperture_2=size.upper())
        else:
            raise ValueError(f"Slit size {size} is undefined")

    def _detector_is_on(self):
        """Is the detector currently on?"""
        return self.get_pv("MOXA12XX_02:CH0:AI:RBV") > 2

    def _detector_turn_on(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported LOQ")

    def _detector_turn_off(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported on LOQ")

    def _configure_sans_custom(self):
        gen.cset(Tx_Mon="OUT")
        gen.waitfor_move()

    def _configure_trans_custom(self):
        self.set_aperture("SMALL")
        gen.cset(Tx_Mon="IN")
        gen.waitfor_move()

    def run_off_julabo_1(self, temperature_1, temperature_2):
        """Run off Julabo 1"""
        self.send_pv("JULABO_01:MODE:SP", "OFF")
        sleep(1)
        self.send_pv("JULABO_02:MODE:SP", "OFF")
        gen.waitfor_move()
        gen.cset(Valve="J1")
        gen.waitfor_move()
        gen.cset(Julabo_1_Sensor="External")
        sleep(1)
        gen.cset(Julabo_2_Sensor="Internal")
        gen.waitfor_move()
        gen.cset(Internal_Setpoint_1=temperature_1)
        sleep(1)
        gen.cset(Internal_Setpoint_2=temperature_2)
        gen.waitfor_move()
        self.send_pv("JULABO_01:MODE:SP", "ON")
        sleep(1)
        self.send_pv("JULABO_02:MODE:SP", "ON")
        gen.waitfor_move()

    @staticmethod
    def run_off_julabo_2(temperature_1, temperature_2):
        """Run off Julabo 2"""
        gen.cset(Julabo_1_Circulator="OFF")
        sleep(1)
        gen.cset(Julabo_2_Circulator="OFF")
        gen.waitfor_move()
        gen.cset(Valve="J2")
        gen.waitfor_move()
        gen.cset(Julabo_1_Sensor="Internal")
        sleep(1)
        gen.cset(Julabo_2_Sensor="External")
        gen.waitfor_move()
        gen.cset(Internal_Setpoint_1=temperature_1)
        sleep(1)
        gen.cset(Internal_Setpoint_2=temperature_2)
        gen.waitfor_move()
        gen.cset(Julabo_1_Circulator="ON")
        sleep(1)
        gen.cset(Julabo_2_Circulator="ON")
        gen.waitfor_move()


obj = LOQ()
for method in dir(obj):
    if method[0] != "_" and method not in locals() and \
       method not in obj._block_accessors and \
       callable(getattr(obj, method)):
        locals()[method.lower()] = local_wrapper(obj, method)
        locals()[method.upper()] = local_wrapper(obj, method)
