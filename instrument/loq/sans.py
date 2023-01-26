"""This is the instrument implementation for the LOQ beamline."""
from time import sleep
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
# pylint: disable=unused-import
from technique.sans.util import set_metadata  # noqa: F401
from general.scans.util import local_wrapper


class LOQ(ScanningInstrument):
    """This class handles the LOQ beamline"""

    _PV_BASE = "IN:LOQ:"

    def __init__(self):
        ScanningInstrument.__init__(self)
        self.setup_sans = self.setup_dae_histogram

    _poslist = ['AB', 'BB', 'CB', 'DB', 'EB', 'FB', 'GB', 'HB', 'IB', 'JB',
                'KB', 'LB', 'MB', 'NB', 'OB', 'PB', 'QB', 'RB', 'SB', 'TB',
                '1CB', '2CB', '3CB', '4CB', '5CB', '6CB', '7CB', '8CB', '9CB',
                '10CB', '11CB', '12CB', '13CB', '14CB', '15CB', '16CB', '17CB', '18CB',
                '1WB', '2WB', '3WB', '4WB', '5WB', '6WB', '7WB', '8WB',
                '9WB', '10WB', '11WB', '12WB', '13WB', '14WB', '15WB', '16WB',
                '1DB', '2DB', '3DB', '4DB', '5DB', '6DB',
                '7DB', '8DB', '9DB', '10DB', '11DB', '12DB',
                'DLS2', 'DLS3', 'DLS4', 'DLS5', 'DLS6',
                'FIVE', 'SIX', 'SEVEN', 'EIGHT']

    def _generic_scan(  # pylint: disable=dangerous-default-value
            self,
            detector=r"detector35576_M4.dat",
            spectra=r"spectra35576_M4.dat",
            wiring=r"wiring35576_M4.dat",
            tcbs=[{"low": 3500.0, "high": 43500.0, "step": 0.025,
                   "log": True}]):
        base = r"C:\Instrument\Settings\config\NDXLOQ\configurations\tables\\"
        gen.change_start()
        for trange in range(1, 6):
            gen.change_tcb(low=0, high=0, step=0, log=0,
                           trange=trange, regime=1)
            sleep(1.5)
        gen.change_tcb(low=0, high=0, step=0, log=0,
                       trange=1, regime=2)
        gen.change_finish()
        ScanningInstrument._generic_scan(
            self, base + detector, base + spectra, base + wiring, tcbs)

    @set_metadata("SANS/TRANS", "sans")
    def setup_dae_event(self):
        self.setup_dae_normal()

    @set_metadata("SANS/TRANS", "sans")
    def setup_dae_histogram(self):
        self.setup_dae_normal()

    @set_metadata("TRANS", "transmission")
    def setup_dae_transmission(self):
        return self._generic_scan(
            detector="detector8.dat",
            spectra="spectra8.dat",
            wiring="wiring8.dat")

    @set_metadata("SANS", "sans")
    def setup_dae_bsalignment(self):
        raise NotImplementedError("DAE mode bsalignment unwritten for LOQ")

    @set_metadata("SCAN", "scan")
    def setup_dae_scanning(self):
        # FIXME: LOQ doesn't have a history of scanning, so it's not
        # certain what mode should be used.  For now, we'll guess it
        # to be the same as histogram
        return self._generic_scan()

    @set_metadata("SCAN", "scan")
    def setup_dae_nr(self):
        raise NotImplementedError("LOQ cannot perform reflectometry")

    @set_metadata("SCAN", "scan")
    def setup_dae_nrscanning(self):
        raise NotImplementedError("LOQ cannot perform reflectometry")

    @set_metadata("SANS/TRANS", "sans")
    def setup_dae_normal(self):
        """Setup LOQ for normal operation"""
        gen.change_sync("smp")
        gen.change_monitor(2, low=5000.0, high=27000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         ext0=True, ext1=True, ext2=True, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 3500.0, "high": 43500.0, "step": 0.025,
                   "log": True},
                  {"low": 3500, "high": 43500.0, "step": 40000,
                   "log": False, "trange": 1, "regime": 2}])

    @set_metadata("SANS/TRANS", "sans")
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

    @set_metadata("SANS/TRANS", "sans")
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

    @set_metadata("SANS/TRANS", "sans")
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
            pass
        elif size.upper() == "SMALL":
            gen.cset(Aperture_2="SMALL")
        elif size.upper() == "MEDIUM":
            gen.cset(Aperture_2="MEDIUM")
        elif size.upper() == "LARGE":
            gen.cset(Aperture_2="LARGE")
        else:
            raise RuntimeError("Slit size {} is undefined".format(size))

    def _detector_is_on(self):
        """Is the detector currently on?"""
        return self.get_pv("MOXA12XX_02:CH0:AI:RBV") > 2

    @staticmethod
    def _detector_turn_on(delay=True):
        raise NotImplementedError("Detector toggling is not supported LOQ")
        # for x in range(8):
        #     self.send_pv("CAEN:hv0:4:{}:pwonoff".format(x), "On")

    @staticmethod
    def _detector_turn_off(delay=True):
        raise NotImplementedError("Detector toggling is not supported on LOQ")
        # for x in range(8):
        #     self.send_pv("CAEN:hv0:4:{}:pwonoff".format(x), "Off")

    def _configure_sans_custom(self):
        gen.cset(Tx_Mon="OUT")
        gen.waitfor_move()

    def _configure_trans_custom(self):
        gen.cset(Aperture_2="SMALL")
        gen.cset(Tx_Mon="IN")
        gen.waitfor_move()

    # pylint: disable=invalid-name
    def J1(self, temperature_1, temperature_2):
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
    def J2(temperature_1, temperature_2):
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
