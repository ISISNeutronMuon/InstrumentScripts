"""This is the instrument implementation for the Sans2d beamline."""
from technique.sans.genie import gen
from technique.sans.instrument import ScanningInstrument
# pylint: disable=unused-import
from technique.sans.util import dae_setter  # noqa: F401
from general.scans.util import local_wrapper
from general.utilities.io import alert_on_error
from logging import warning


class Sans2d(ScanningInstrument):
    """This class handles the SANS2D beamline"""

    def __init__(self):
        super().__init__()
        self._poslist_dls = self.get_pv("LKUP:DLS:POSITIONS").split()

    def check_move_pos(self, pos):
        """Check whether the position is valid for the normal
        sample changer and return True or False

        Parameters
        ----------
        pos : str
          The sample changer position

        """
        if pos not in self._poslist:
            warning(f"Error in script, position {pos} does not exist")
            return False
        return True

    def check_move_pos_dls(self, pos):
        """Check whether the position is valid for the DSL sample
         changer and return True or False

        Parameters
        ----------
        pos : str
          The sample changer position

        """
        if pos not in self._poslist_dls:
            warning(f"Error in script, position {pos} does not exist")
            return False
        return True

    def do_sans_large(self, title="", position=None, thickness=1.0, dae=None,
                    period=None, time=None, dls_sample_changer=False, **kwargs):
        """
        A wrapper around do_sans with aperture set to large
        Please see measure for full documentation of parameters
        """
        self.do_sans(title=title, position=position, thickness=thickness, dae=dae,
                period=period, aperture="LARGE", time=time, dls_sample_changer=dls_sample_changer, **kwargs)

    def _generic_scan(
            self,
            detector, spectra,
            wiring, tcbs=[{"low": 5.5, "high":50.0, "step": 44.5, "log": 0, "trange":1, "regime":1},
                          {"low": 50.0, "high":2500.0, "step": 50.0, "log": 0, "trange":2, "regime":1},
                          {"low": 2500.0, "high":14000.0, "step": 0.02, "log": 1, "trange":3, "regime":1},
                          {"low": 14000.0, "high":99750.0, "step": 250.0, "log": 0, "trange":4, "regime":1},
                          {"low": 99750.0, "high":100005.0, "step": 255.0, "log": 0, "trange":5, "regime":1},
                          {"low": 5.5, "high":100005.0, "step": 5.0, "log": 0, "trange":1, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":2, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":3, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":4, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":5, "regime":2}]):
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
        self._generic_scan(
            detector="detector_gastubes_01.dat",
            spectra="spectrum_gastubes_01.dat",
            wiring="wiring_gastubes_01_event.dat")

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        # self._generic_scan(
        #     detector=r"detector_gastubes_02.dat",
        #     spectra=r"spectrum_gastubes_02.dat",
        #     wiring=r"wiring_gastubes_02_hist.dat",
        #     tcbs=[])
        raise NotImplementedError(
            "Neutron reflectivity scanning tables not yet set")

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        self._generic_scan(
            detector="detector_trans8.dat",
            spectra="spectra_trans8.dat",
            wiring="wiring_trans8.dat")

    def set_aperture(self, size):
        """
        Set the beam aperture to the desired size.

        Parameters
        ----------
        size : str
          The aperture size.  e.g. "Small" or "Medium"
          A blank string (the default value) results in
          the aperture not being changed.
        """
        if not size:
            # Empty string means keep the current position
            print("Aperture unchanged")
            return
        size = size.upper()
        if size not in ["SMALL", "MEDIUM", "LARGE", "XLARGE"]:
            raise RuntimeError(f"Unknown slit size: {size}")
        gen.set_pv("LKUP:SCRAPER:POSN:SP", size, is_local=True)
        gen.waitfor_move()

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = [
            self.get_pv(
                f"CAEN:hv0:1:{x}:status").lower() == "on"
            for x in range(10)]
        return all(voltage_status)

    def _detector_turn_on(self, delay=True):
        alert_on_error("SANS2D Detectors must be turned on manually", False)

    def _detector_turn_off(self, delay=True):
        alert_on_error("SANS2D Detectors must be turned off manually", False)

    def _configure_sans_custom(self):
        # move the transmission monitor out
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "OUT", is_local=True)

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "IN", is_local=True)


obj = Sans2d()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
