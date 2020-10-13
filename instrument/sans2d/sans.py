"""This is the instrument implementation for the Sans2d beamline."""
from technique.sans.genie import gen
from technique.sans.instrument import ScanningInstrument
# pylint: disable=unused-import
from technique.sans.util import set_metadata  # noqa: F401
from general.scans.util import local_wrapper
from genie_python import genie as g


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

    @set_metadata("SANS", "sans")
    def setup_dae_event(self):
        self._generic_scan(
            detector=r"detector_gastubes_01.dat",
            spectra=r"spectrum_gastubes_01.dat",
            wiring=r"wiring_gastubes_01_event.dat",
            tcbs=[])

    @set_metadata("SANS", "sans")
    def setup_dae_histogram(self):
        self._generic_scan(
            detector=r"wiring_gastubes_02_hist.dat",
            spectra=r"spectrum_gastubes_02.dat",
            wiring=r"detector_gastubes_02.dat",
            tcbs=[])

    @set_metadata("TRANS", "transmission")
    def setup_dae_transmission(self):
        self._generic_scan(
            spectra=r"spectra_trans8.dat",
            wiring=r"wiring_trans8.dat",
            detector=r"detector_trans8.dat",
            tcbs=[])

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
        if size == "":
            pass
        gen.set_pv("LKUP:SCRAPER:POSN:SP", size, is_local=True)

    def _detector_is_on(self):
        return True

    def _detector_turn_on(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported Sans2d")

    def _detector_turn_off(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported on Sans2d")

    def _configure_sans_custom(self):
        # move the transmission monitor out
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "OUT", is_local=True)

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "IN", is_local=True)


obj = Sans2d()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
