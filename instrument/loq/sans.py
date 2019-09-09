"""This is the instrument implementation for the LOQ beamline."""
from time import sleep
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
# pylint: disable=unused-import
from technique.sans.util import dae_setter  # noqa: F401
from general.scans.util import local_wrapper


class LOQ(ScanningInstrument):
    """This class handles the LOQ beamline"""

    _PV_BASE = "IN:LOQ:"

    def __init__(self):
        ScanningInstrument.__init__(self)
        self.setup_sans = self.setup_dae_histogram

    _poslist = ['AB', 'BB', 'CB', 'DB', 'EB', 'FB', 'GB', 'HB', 'IB', 'JB',
                'KB', 'LB', 'MB', 'NB', 'OB', 'PB', 'QB', 'RB', 'SB', 'TB',
                'C1B', 'C2B', 'C3B', 'C4B', 'C5B', 'C6B', 'C7B', 'C8B', 'C9B',
                'C10B', 'C11B', 'C12B', 'C13B', 'C14B', 'C15B', 'C16B', 'C17B',
                'C18B', 'C1T', 'C2T', 'C3T', 'C4T', 'C5T', 'C6T', 'C7T',
                'C8T', 'C9T', 'C10T', 'C11T', 'C12T', 'C13T', 'C14T',
                'W1B', 'W2B', 'W3B', 'W4B', 'W5B', 'W6B', 'W7B', 'W8B',
                'W9B', 'W10B', 'W11B', 'W12B', 'W13B', 'W14B', 'W15B', 'W16B',
                'DLS2', 'DLS3', 'DLS4', 'DLS5', 'DLS6']

    def _generic_scan(  # pylint: disable=dangerous-default-value
            self,
            detector=r"detector35576_M4.dat",
            spectra=r"spectra35576_M4.dat",
            wiring=r"wiring35576_M4.dat",
            tcbs=[{"low": 3500.0, "high": 43500.0, "step": 0.025,
                   "log": True}]):
        base = r"C:\Instrument\Settings\config\NDXLOQ\configurations\tables\\"
        self._generic_scan(
            base + detector, base + spectra, base + wiring, tcbs)

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_event(self):
        self.setup_dae_normal()

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_histogram(self):
        self.setup_dae_normal()

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        return self._generic_scan()

    @dae_setter("SANS", "sans")
    def setup_dae_bsalignment(self):
        raise NotImplementedError("DAE mode bsalignment unwritten for LOQ")

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        # FIXME: LOQ doesn't have a history of scanning, so it's not
        # certain what mode should be used.  For now, we'll guess it
        # to be the same as histogram
        return self._generic_scan()

    @dae_setter("SCAN", "scan")
    def setup_dae_nr(self):
        raise NotImplementedError("LOQ cannot perform reflectometry")

    @dae_setter("SCAN", "scan")
    def setup_dae_nrscanning(self):
        raise NotImplementedError("LOQ cannot perform reflectometry")

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_normal(self):
        """Setup LOQ for normal operation"""
        gen.change_sync("smp")
        gen.change_monitor(2, low=5000.0, high=27000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         ext0=True, ext1=True, ext2=True, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 3500.0, "high": 43500.0, "step": 0.025,
                   "log": True}])

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_quiet(self):
        """Setup LOQ for quiet operation"""
        gen.change_sync("internal")
        gen.change_monitor(2, low=5.0, high=20000.0)
        gen.change_vetos(clearall=True, smp=False, TS2=False,
                         ext0=False, ext1=False, ext2=False, ext3=False)
        return self._generic_scan(
            tcbs=[{"low": 5.0, "high": 19995.0, "step": 4000.0,
                   "log": False}])

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_50hz_short(self):
        """Setup LOQ for 50hz mode while short"""
        gen.change_sync("isis")
        gen.change_monitor(2, low=6800.0, high=17000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         ext0=True, ext1=True, ext2=True, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 6e3, "high": 1.96e4, "step": 4e2, "log": False},
                  {"low": 1.96e4, "high": 1.99e4, "step": 3e2, "log": False},
                  {"low": 1.99e4, "high": 2.08e4, "step": 1e2, "log": False},
                  {"low": 2.08e4, "high": 2.60e4, "step": 4e2, "log": False}])

    @dae_setter("SANS/TRANS", "sans")
    def setup_dae_50hz_long(self):
        """Setup LOQ for 50hz mode while long"""
        gen.change_sync("isis")
        gen.change_monitor(2, low=5000.0, high=27000.0)
        gen.change_vetos(clearall=True, smp=True, TS2=True,
                         ext0=True, ext1=True, ext2=True, ext3=True)
        return self._generic_scan(
            tcbs=[{"low": 2e4, "high": 3.95e4, "step": 2.5e2, "log": False},
                  {"low": 3.95e4, "high": 4e4, "step": 1e2, "log": False}])

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
        #     self.set_pv("CAEN:hv0:4:{}:pwonoff".format(x), "On")

    @staticmethod
    def _detector_turn_off(delay=True):
        raise NotImplementedError("Detector toggling is not supported on LOQ")
        # for x in range(8):
        #     self.set_pv("CAEN:hv0:4:{}:pwonoff".format(x), "Off")

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
        self.set_pv("JULABO_01:MODE:SP", "OFF")
        sleep(1)
        self.set_pv("JULABO_02:MODE:SP", "OFF")
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
        self.set_pv("JULABO_01:MODE:SP", "ON")
        sleep(1)
        self.set_pv("JULABO_02:MODE:SP", "ON")
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
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
