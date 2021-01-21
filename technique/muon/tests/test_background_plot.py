import os

# Set genie python to simulate
os.environ["GENIE_SIMULATE"] = "1"

# Imports come after to prevent import of genie python not in simulation
import datetime
import unittest
import six.moves
from technique.muon.background_plot import BackgroundPlot
if six.PY3:
    from unittest.mock import patch, call
else:
    from mock import patch, call

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestLoadDataFromSave(unittest.TestCase):

    def setUp(self):
        self.background_plot = BackgroundPlot(interval=None, ioc_number=1)

    def tearDown(self):
        pass

    @patch('builtins.print')
    def test_GIVEN_corrupted_file_WHEN_load_data_THEN_display_warnings_and_no_exception(self, m_print):
        pass
        # Arrange
        self.background_plot.data = [[None], [1.0], [None], [26.405517959396146], [17315086336.0]]
        self.background_plot.data_x = [datetime.datetime(2021, 1, 21, 14, 49, 50, 653244)]
        self.background_plot._save_file = os.path.join(THIS_DIR, 'data', 'corrupted_plot_data_01.csv')

        expected_warnings = [
            "WARNING - Save file may be corrupted: list index out of range",
            "WARNING - Save file may be corrupted: Invalid isoformat string: 'asad'",
            "WARNING - Save file may be corrupted: list index out of range",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-1asd5 16:38:16.251768'",
            "WARNING - Save file may be corrupted: list index out of range",
            "WARNING - Save file may be corrupted: list index out of range",
            "WARNING - Save file may be corrupted: list index out of range",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '202123808283406'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 16:41715'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 153728.0'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: ''",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 16:18005667840.0'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 6666666668'",
            "WARNING - Save file may be corrupted: list index out of range",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2139hdia'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: 'ndasdsda'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 16:43:52.24725'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 16:52:15.4546720'",
            "WARNING - Save file may be corrupted: Invalid isoformat string: '2021-01-15 16:55:32.763520.0'",
            "WARNING - Save file may be corrupted: 3 data points could not be appended to the dataset: "
            "['17745444sad21312asczx864.0', '17989844992.02021-01-15 16:55:08.764338', '23.6595523165011.0']"
        ]

        calls = [call(x) for x in expected_warnings]

        # Act
        self.background_plot.load_data_from_save()

        # Assert
        m_print.assert_has_calls(calls, any_order=False)
