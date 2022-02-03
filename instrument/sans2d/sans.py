"""This is the instrument implementation for the Sans2d beamline."""
from technique.sans.genie import gen
from technique.sans.instrument import ScanningInstrument
# pylint: disable=unused-import
from technique.sans.util import set_metadata  # noqa: F401
from general.scans.util import local_wrapper
from genie_python import genie as g
from general.utilities.io import alert_on_error


class Sans2d(ScanningInstrument):
    """This class handles the SANS2D beamline"""
    _PV_BASE = g.my_pv_prefix

    @set_metadata("SCAN", "scan")
    def setup_dae_scanning(self):
        raise NotImplementedError("Scanning tables not yet set")

    @set_metadata("SCAN", "scan")
    def setup_dae_nr(self):
        raise NotImplementedError("Neutron reflectivity tables not yet set")

    @set_metadata("SCAN", "scan")
    def setup_dae_nrscanning(self):
        raise NotImplementedError(
            "Neutron reflectivity scanning tables not yet set")

    def _generic_scan(
            self,
            detector, spectra,
            wiring, tcbs=[{"low": 5.5, "high":50.0, "step": 44.5, "log": 0, "trange":1, "regime":1},
                          {"low": 50.0, "high":2500.0, "step": 50.0, "log": 0, "trange":2, "regime":1}
                          {"low": 2500.0, "high":14000.0, "step": 0.02, "log": 1, "trange":3, "regime":1}
                          {"low": 14000.0, "high":99750.0, "step": 250.0, "log": 0, "trange":4, "regime":1}
                          {"low": 99750.0, "high":100005.0, "step": 255.0, "log": 0, "trange":5, "regime":1}
                          {"low": 5.5, "high":100005.0, "step": 5.0, "log": 0, "trange":1, "regime":2}
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":2, "regime":2}
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":3, "regime":2}
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":4, "regime":2}
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":5, "regime":2}]):
        base = r"C:\Instrument\Settings\config\NDXSANS2D\configurations\tables\\"
        ScanningInstrument._generic_scan(self,
            base + detector, base + spectra, base + wiring, tcbs)

    @set_metadata("SANS", "sans")
    def setup_dae_event(self):
        self._generic_scan(
            detector=r"detector_gastubes_01.dat",
            spectra=r"spectrum_gastubes_01.dat",
            wiring=r"wiring_gastubes_01_event.dat")

    @set_metadata("SANS", "sans")
    def setup_dae_histogram(self):
        raise NotImplementedError(
            "Neutron reflectivity scanning tables not yet set")

    @set_metadata("TRANS", "transmission")
    def setup_dae_transmission(self):
        self._generic_scan(
            spectra=r"spectra_trans8.dat",
            wiring=r"wiring_trans8.dat",
            detector=r"detector_trans8.dat")

    @set_metadata("SANS", "sans")
    def setup_dae_bsalignment(self):
        raise NotImplementedError("Beam Stop Alignment tables not yet set")

    @staticmethod
    def set_aperture(size):
        """
        Set the beam aperture to the desired size.

        Parameters
        ----------
        size : str
          The aperture size.  e.g. "Small" or "Medium"
          A blank string (the default value) results in
          the aperture not being changed."""
        if not size:
            # Empty string means keep the current position
            return
        size = size.upper()
        if size not in ["SMALL", "MEDIUM", "LARGE", "XLARGE"]
            raise RuntimeError("Unknown slit size: {}".format(size))
        gen.set_pv("LKUP:SCRAPER:POSN:SP", size, is_local=True)
        gen.waitfor_move()

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = all([
            self.get_pv(
                "CAEN:hv0:1:{}:status".format(x)).lower() == "on"
            for x in range(10)])
        return voltage_status

    def _detector_turn_on(self, delay=True):
        alert_on_error("SANS2D Detectors must be turned on manually", False)

    def _detector_turn_off(self, delay=True):
        alert_on_error("SANS2D Detectors must be turned off manually", False)

    def _configure_sans_custom(self):
        # close the fast shutter
        gen.set_pv("FINS_VAC:SHUTTER:STATUS:SP", "CLOSE")
        # move the transmission monitor out
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "OUT", is_local=True)

        gen.waitfor_move()

    def _configure_trans_custom(self):
        # close the fast shutter
        gen.set_pv("FINS_VAC:SHUTTER:STATUS:SP", "CLOSE")
        # move the transmission monitor in
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "IN", is_local=True)

        gen.waitfor_move()


obj = Sans2d()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
