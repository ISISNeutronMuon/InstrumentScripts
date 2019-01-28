"""This is the instrument implementation for the LOQ beamline."""
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
# pylint: disable=unused-import
from technique.sans.util import dae_setter  # noqa: F401
from general.scans.util import local_wrapper

pv_origin = "IN:LOQ"


class LOQ(ScanningInstrument):
    """This class handles the LOQ beamline"""

    def set_measurement_type(self, value):
        gen.set_pv(pv_origin + ":PARS:SAMPLE:MEAS:TYPE", value)

    def set_measurement_label(self, value):
        gen.set_pv(pv_origin + ":PARS:SAMPLE:MEAS:LABEL", value)

    def set_measurement_id(self, value):
        gen.set_pv(pv_origin + ":PARS:SAMPLE:MEAS:ID", value)

    # FIXME
    @staticmethod
    def _generic_scan(  # pylint: disable=dangerous-default-value
            detector, spectra,
            wiring=r"card.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 200.0,
                   "trange": 1, "log": 0}]):
        base = r"C:\Instrument\Settings\config\NDXLOQ\configurations\tables\\"
        ScanningInstrument._generic_scan(
            base+detector, base+spectra, base+wiring, tcbs)

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
        pass  # FIXME

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        pass  # FIXME

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        pass  # FIXME

    @dae_setter("SANS", "sans")
    def setup_dae_bsalignment(self):
        pass  # FIXME

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        pass  # FIXME

    @dae_setter("SCAN", "scan")
    def setup_dae_nr(self):
        pass  # FIXME

    @dae_setter("SCAN", "scan")
    def setup_dae_nrscanning(self):
        pass  # FIXME

    @staticmethod
    def set_aperature(size):
        pass

    @staticmethod
    def _detector_is_on():
        """Is the detector currently on?"""
        pass  # FIXME

    @staticmethod
    def _detector_turn_on(delay=True):
        raise NotImplementedError("Detector toggling is not supported LOQ")
        # for x in range(8):
        #     gen.set_pv(pv_origin + ":CAEN:hv0:4:{}:pwonoff".format(x), "On")

    @staticmethod
    def _detector_turn_off(delay=True):
        raise NotImplementedError("Detector toggling is not supported on LOQ")
        # for x in range(8):
        #     gen.set_pv(pv_origin + ":CAEN:hv0:4:{}:pwonoff".format(x), "Off")

    def _configure_sans_custom(self):
        # move the transmission monitor out
        gen.set_pv(pv_origin + ":VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.set_pv(pv_origin + ":VACUUM:MONITOR:4:INSERT", "INSERT")


obj = LOQ()
for method in dir(obj):
    if method[0] != "_" and method not in locals() and \
       callable(getattr(obj, method)):
        locals()[method] = local_wrapper(obj, method)
