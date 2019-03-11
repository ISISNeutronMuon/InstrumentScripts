"""This is the instrument implementation for the LOQ beamline."""
from technique.sans.instrument import ScanningInstrument
from technique.sans.genie import gen
# pylint: disable=unused-import
from technique.sans.util import dae_setter  # noqa: F401
from general.scans.util import local_wrapper

pv_origin = "IN:LOQ"  # FIXME


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
        raise NotImplementedError("LOQ does not support event mode")

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        raise NotImplementedError(
            "DAE mode histogram unwritten for LOQ")  # FIXME

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        raise NotImplementedError(
            "DAE mode transmission unwritten for LOQ")  # FIXME

    @dae_setter("SANS", "sans")
    def setup_dae_bsalignment(self):
        raise NotImplementedError("DAE mode bsalignment unwritten for LOQ")

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        raise NotImplementedError(
            "DAE mode scanning unwritten for LOQ")  # FIXME

    @dae_setter("SCAN", "scan")
    def setup_dae_nr(self):
        raise NotImplementedError("LOQ cannot perform reflectometry")

    @dae_setter("SCAN", "scan")
    def setup_dae_nrscanning(self):
        raise NotImplementedError("LOQ cannot perform reflectometry")

    @staticmethod
    def set_aperture(size):
        if size.upper() == "SMALL":
            gen.cset(Aperture_2="SMALL")
        elif size.upper() == "MEDIUM":
            gen.cset(Aperture_2="MEDIUM")
        elif size.upper() == "LARGE":
            gen.cset(Aperture_2="LARGE")
        else:
            RuntimeError("Slit size {} is undefined".format(size))

    @staticmethod
    def _detector_is_on():
        """Is the detector currently on?"""
        # FIXME
        raise NotImplementedError("Detector testing is not supported on LOQ")

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
        gen.cset(Tx_Mon="OUT")

    def _configure_trans_custom(self):
        gen.cset(Aperture_2="SMALL")
        gen.cset(Tx_Mon="IN")


obj = LOQ()
for method in dir(obj):
    if method[0] != "_" and method not in locals() and \
       callable(getattr(obj, method)):
        locals()[method] = local_wrapper(obj, method)
