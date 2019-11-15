"""This is the instrument implementation for the Zoom beamline."""
from technique.sans.instrument import ScanningInstrument
# pylint: disable=unused-import
from technique.sans.util import dae_setter  # noqa: F401
from general.scans.util import local_wrapper


class Zoom(ScanningInstrument):
    """This class handles the Zoom beamline"""
    _PV_BASE = "IN:ZOOM:"

    @dae_setter("SCAN", "scan")
    def setup_dae_scanning(self):
        raise NotImplementedError("Scanning tables not yet set")

    @dae_setter("SCAN", "scan")
    def setup_dae_nr(self):
        raise NotImplementedError("Neutron reflectivity tables not yet set")

    @dae_setter("SCAN", "scan")
    def setup_dae_nrscanning(self):
        raise NotImplementedError(
            "Neutron reflectivity scanning tables not yet set")

    def _generic_scan(  # pylint: disable=dangerous-default-value
            self,
            detector, spectra,
            wiring=r"detector_1det_1dae3card.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 200.0,
                   "trange": 1, "log": 0}]):
        base = r"C:\Instrument\Settings\config\NDXZOOM\configurations\tables\\"
        self._generic_scan(
            base + detector, base + spectra, base + wiring, tcbs)

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
        self._generic_scan(
            detector=r"detector_1det_1dae3card.dat",
            spectra=r"spec2det_280318_to_test_18_1.txt",
            wiring=r"wiring1det_event_200218.dat")

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        self._generic_scan(
            detector=r"detector_1det_1dae3card.dat",
            spectra=r"spec2det_130218.txt",
            wiring=r"wiring1det_histogram_200218.dat")

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        self._generic_scan(
            spectra=r"spectrum_8mon_1dae3card_00.dat",
            wiring=r"wiring_8mon_1dae3card_00_hist.dat",
            detector=r"detector_8mon_1dae3card_00.dat")

    @dae_setter("SANS", "sans")
    def setup_dae_bsalignment(self):
        raise NotImplementedError("Beam Stop Alignment tables not yet set")

    @staticmethod
    def set_aperture(size):
        if size.upper() == "MEDIUM":
            # change the line below to match ZOOM motors
            # gen.cset(a1hgap=20.0, a1vgap=20.0, s1hgap=14.0, s1vgap=14.0)
            pass

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = all([
            self.get_pv(
                "CAEN:hv0:4:{}:status".format(x)).lower() == "on"
            for x in range(8)])
        return voltage_status

    def _detector_turn_on(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported Zoom")
        # for x in range(8):
        #     self.send_pv("CAEN:hv0:4:{}:pwonoff".format(x), "On")

    def _detector_turn_off(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported on Zoom")
        # for x in range(8):
        #     self.send_pv("CAEN:hv0:4:{}:pwonoff".format(x), "Off")

    def _configure_sans_custom(self):
        # move the transmission monitor out
        self.send_pv("VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

    def _configure_trans_custom(self):
        # move the transmission monitor in
        self.send_pv("VACUUM:MONITOR:4:INSERT", "INSERT")


obj = Zoom()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
