"""This is the instrument implementation for the Zoom beamline."""
from .Instrument import ScanningInstrument
from .genie import gen
from .Util import dae_setter


class Zoom(ScanningInstrument):
    """This class handles the Zoom beamline"""

    _poslist = ['AB', 'BB', 'CB', 'DB', 'EB', 'FB', 'GB', 'HB', 'IB', 'JB',
                'KB', 'LB', 'MB', 'NB', 'OB', 'PB', 'QB', 'RB', 'SB', 'TB',
                'AT', 'BT', 'CT', 'DT', 'ET', 'FT', 'GT', 'HT', 'IT', 'JT',
                'KT', 'LT', 'MT', 'NT', 'OT', 'PT', 'QT', 'RT', 'ST', 'TT',
                '1CB', '2CB', '3CB', '4CB', '5CB', '6CB', '7CB',
                '8CB', '9CB', '10CB', '11CB', '12CB', '13CB', '14CB',
                '1CT', '2CT', '3CT', '4CT', '5CT', '6CT', '7CT',
                '8CT', '9CT', '10CT', '11CT', '12CT', '13CT', '14CT',
                '1WB', '2WB', '3WB', '4WB', '5WB', '6WB', '7WB',
                '8WB', '9WB', '10WB', '11WB', '12WB', '13WB', '14WB',
                '1WT', '2WT', '3WT', '4WT', '5WT', '6WT', '7WT',
                '8WT', '9WT', '10WT', '11WT', '12WT', '13WT', '14WT']

    def set_measurement_type(self, value):
        gen.set_pv("IN:ZOOM:PARS:SAMPLE:MEAS:TYPE", value)

    def set_measurement_label(self, value):
        gen.set_pv("IN:ZOOM:PARS:SAMPLE:MEAS:LABEL", value)

    def set_measurement_id(self, value):
        gen.set_pv("IN:ZOOM:PARS:SAMPLE:MEAS:ID", value)

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

    @staticmethod
    def _generic_scan(  # pylint: disable=dangerous-default-value
            detector, spectra,
            wiring=r"detector_1det_1dae3card.dat",
            tcbs=[{"low": 5.0, "high": 100000.0, "step": 200.0,
                   "trange": 1, "log": 0}]):
        base = r"C:\Instrument\Settings\config\NDXZOOM\configurations\tables\\"
        ScanningInstrument._generic_scan(
            base+detector, base+spectra, base+wiring, tcbs)

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
        self._generic_scan(
            r"spec2det_280318_to_test_18_1.txt",
            r"wiring1det_event_200218.dat")

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        self._generic_scan(
            r"spec2det_130218.txt",
            r"wiring1det_histogram_200218.dat")

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        self._generic_scan(
            r"spectrum_8mon_1dae3card_00.dat",
            r"wiring_8mon_1dae3card_00_hist.dat",
            r"detector_8mon_1dae3card_00.dat")

    @dae_setter("SANS", "sans")
    def setup_dae_bsalignment(self):
        raise NotImplementedError("Beam Stop Alignment tables not yet set")

    @staticmethod
    def set_aperature(size):
        if size.upper() == "MEDIUM":
            # change the line below to match ZOOM motors
            # gen.cset(a1hgap=20.0, a1vgap=20.0, s1hgap=14.0, s1vgap=14.0)
            pass

    @staticmethod
    def _detector_is_on():
        """Is the detector currently on?"""
        voltage_status = all([
            gen.get_pv(
                "IN:ZOOM:CAEN:hv0:4:{}:status".format(x)).lower() == "on"
            for x in range(8)])
        return voltage_status

    @staticmethod
    def _detector_turn_on(delay=True):
        raise NotImplementedError("Detector toggling is not supported Zoom")
        # for x in range(8):
        #     gen.set_pv("IN:ZOOM:CAEN:hv0:4:{}:pwonoff".format(x), "On")

    @staticmethod
    def _detector_turn_off(delay=True):
        raise NotImplementedError("Detector toggling is not supported on Zoom")
        # for x in range(8):
        #     gen.set_pv("IN:ZOOM:CAEN:hv0:4:{}:pwonoff".format(x), "Off")

    def _configure_sans_custom(self):
        # move the transmission monitor out
        gen.set_pv("IN:ZOOM:VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.set_pv("IN:ZOOM:VACUUM:MONITOR:4:INSERT", "INSERT")
