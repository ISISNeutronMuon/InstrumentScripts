"""This is the instrument implementation for the Sans2d beamline."""
from technique.sans.genie import gen
from technique.sans.instrument import ScanningInstrument
# pylint: disable=unused-import
from technique.sans.util import set_metadata  # noqa: F401
from general.scans.util import local_wrapper
from genie_python import genie as g
from general.utilities.io import alert_on_error
from logging import warning


class Sans2d(ScanningInstrument):
    """This class handles the SANS2D beamline"""
    _PV_BASE = g.my_pv_prefix
    _poslist = ['AB', 'BB', 'CB', 'DB', 'EB', 'FB', 'GB', 'HB', 'IB', 'JB',
                'KB', 'LB', 'MB', 'NB', 'OB', 'PB', 'QB', 'RB', 'SB', 'TB',
                'AT', 'BT', 'CT', 'DT', 'ET', 'FT', 'GT', 'HT', 'IT', 'JT',
                'KT', 'LT', 'MT', 'NT', 'OT', 'PT', 'QT', 'RT', 'ST', 'TT',
                '1CB', '2CB', '3CB', '4CB', '5CB', '6CB', '7CB','8CB', '9CB',
                '10CB', '11CB', '12CB', '13CB', '14CB','15CB', '16CB', '17CB', '18CB',
                '1CT', '2CT', '3CT', '4CT', '5CT', '6CT', '7CT','8CT', '9CT',
                '10CT', '11CT', '12CT', '13CT', '14CT','15CT', '16CT', '17CT', '18CT',
                '1GT', '2GT', '3GT', '4GT', '5GT', '6GT', '7GT',
                '8GT', '9GT', '10GT', '11GT', '12GT', '13GT', '14GT',
                '1WB', '2WB', '3WB', '4WB', '5WB', '6WB', '7WB',
                '8WB', '9WB', '10WB', '11WB', '12WB', '13WB', '14WB',
                '1WT', '2WT', '3WT', '4WT', '5WT', '6WT', '7WT',
                '8WT', '9WT', '10WT', '11WT', '12WT', '13WT', '14WT',
                '1GT', '2GT', '3GT', '4GT', '5GT', '6GT', '7GT', '8GT', '9GT',
                '10GT', '11GT', '12GT',
                '1GB', '2GB', '3GB', '4GB', '5GB', '6GB', '7GB', '8GB', '9GB',
                '10GB', '11GB', '12GB',
                '8WBL', '9WBL', '10WBL', '11WBL', '12WBL', '13WBL', '14WBL',
                'ATrod', 'BTrod', 'CTrod', 'DTrod', 'ETrod', 'FTrod', 'GTrod', 'HTrod', 'ITrod', 'JTrod',
                'KTrod', 'LTrod', 'MTrod', 'NTrod', 'OTrod', 'PTrod', 'QTrod', 'RTrod', 'STrod', 'TTrod',
                'ABrod', 'BBrod', 'CBrod', 'DBrod', 'EBrod', 'FBrod', 'GBrod', 'HBrod', 'IBrod', 'JBrod',
                'KBrod', 'LBrod', 'MBrod', 'NBrod', 'OBrod', 'PBrod', 'QBrod', 'RBrod', 'SBrod', 'TBrod',
                '1CBrod', '2CBrod', '3CBrod', '4CBrod', '5CBrod', '6CBrod', '7CBrod',
                '8CBrod', '9CBrod', '10CBrod', '11CBrod', '12CBrod', '13CBrod', '14CBrod',
                '15CBrod', '16CBrod', '17CBrod', '18CBrod',
                '1CTrod', '2CTrod', '3CTrod', '4CTrod', '5CTrod', '6CTrod', '7CTrod',
                '8CTrod', '9CTrod', '10CTrod', '11CTrod', '12CTrod', '13CTrod', '14CTrod',
                '15CTrod', '16CTrod', '17CTrod', '18CTrod',
                '1WBrod', '2WBrod', '3WBrod', '4WBrod', '5WBrod', '6WBrod', '7WBrod',
                '8WBrod', '9WBrod', '10WBrod', '11WBrod', '12WBrod', '13WBrod', '14WBrod',
                '1WTrod', '2WTrod', '3WTrod', '4WTrod', '5WTrod', '6WTrod', '7WTrod',
                '8WTrod', '9WTrod', '10WTrod', '11WTrod', '12WTrod', '13WTrod', '14WTrod',
                '1RR', '2RR', '3RR', '4RR', '5RR', '6RR', '7RR',
                '1W7', '2W7', '3W7', '4W7', '5W7', '6W7', '7W7',
                'XSF',
                'ASFT', 'BSFT', 'CSFT', 'DSFT', 'ESFT', 'FSFT', 'GSFT', 'HSFT', 'ISFT', 'JSFT',
                '1SFA', '2SFA', '3SFA', '4SFA', '5SFA', '6SFA', '7SFA', 
                'DLS2',  'DLS3',  'DLS4',  'DLS5',  'DLS6',
                ]

    def check_move_pos(self, pos):
        """Check whether the position is valid and return True or False

        Parameters
        ----------
        pos : str
          The sample changer position

        """
        if pos not in self._poslist:
            warning("Error in script, position {} does not exist".format(pos))
            return False
        return True

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
                          {"low": 50.0, "high":2500.0, "step": 50.0, "log": 0, "trange":2, "regime":1},
                          {"low": 2500.0, "high":14000.0, "step": 0.02, "log": 1, "trange":3, "regime":1},
                          {"low": 14000.0, "high":99750.0, "step": 250.0, "log": 0, "trange":4, "regime":1},
                          {"low": 99750.0, "high":100005.0, "step": 255.0, "log": 0, "trange":5, "regime":1},
                          {"low": 5.5, "high":100005.0, "step": 5.0, "log": 0, "trange":1, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":2, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":3, "regime":2},
                          {"low": 0.0, "high":0.0, "step": 0.0, "log": 0, "trange":4, "regime":2},
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
        if size not in ["SMALL", "MEDIUM", "LARGE", "XLARGE"]:
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
        # move the transmission monitor out
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "OUT", is_local=True)

        gen.waitfor_move()

    def _configure_trans_custom(self):
        # move the transmission monitor in
        gen.set_pv("FINS_VAC:MONITOR3:STATUS:SP", "IN", is_local=True)

        gen.waitfor_move()


obj = Sans2d()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
