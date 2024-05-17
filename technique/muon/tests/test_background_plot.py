import os

# Set genie python to simulate
os.environ["GENIE_SIMULATE"] = "1"

# Imports come after to prevent import of genie python not in simulation
import datetime
import unittest
from technique.muon.background_plot import BackgroundPlot
from unittest.mock import patch, mock_open


THIS_DIR = os.path.dirname(os.path.abspath(__file__))

CORRECT_DATA = "2021-01-15 15:27:59.567993,1.1,1.0,1.0,37.698516011455354,17845047296.0"

DATA_WITH_EMPTY_FIELDS = '2021-01-15 15:27:59.567993,,1.0,,37.698516011455354,17845047296.0'

WRONG_DATE_FORMAT = "20-21-01-15 15:27:595.6567993,1.1,1.0,1.0,37.698516011455354,17845047296.0"

CORRUPT_DATA_POINT = "2021-01-15 15:27:59.567993,1a.1,1.0,1.0,37.698516xxxcz011455354,17845047296.0"


class TestLoadDataFromSave(unittest.TestCase):

    def setUp(self):
        self.background_plot = BackgroundPlot(interval=None, ioc_number=1)
        self.background_plot.data = [[1.0], [2.0], [3.0], [4.0], [5.0]]
        self.background_plot.data_x = [datetime.datetime(2021, 1, 21, 14, 49, 50, 653244)]

    @patch("builtins.open", new_callable=mock_open, read_data=CORRECT_DATA)
    @patch('builtins.print')
    def test_GIVEN_correct_data_WHEN_load_data_THEN_no_warnings_or_exception(self, m_print, m_file):
        # Act
        self.background_plot.load_data_from_save()

        # Assert
        m_print.assert_not_called()

    @patch("builtins.open", new_callable=mock_open, read_data=DATA_WITH_EMPTY_FIELDS)
    @patch('builtins.print')
    def test_GIVEN_empty_fields_WHEN_appending_data_point_THEN_no_warnings_or_exception(self, m_print, m_file):
        # Act
        self.background_plot.load_data_from_save()

        # Assert
        m_print.assert_not_called()

    @patch("builtins.open", new_callable=mock_open, read_data=WRONG_DATE_FORMAT)
    @patch('builtins.print')
    def test_GIVEN_wrong_date_format_WHEN_load_data_THEN_display_warnings_and_no_exception(self, m_print, m_file):
        # Act
        self.background_plot.load_data_from_save()

        # Assert
        m_print.assert_called_with("WARNING - Save file may be corrupted: Invalid isoformat string: "
                                   "'20-21-01-15 15:27:595.6567993'")

    @patch("builtins.open", new_callable=mock_open, read_data=CORRUPT_DATA_POINT)
    @patch('builtins.print')
    def test_GIVEN_corrupt_data_point_WHEN_load_data_THEN_display_warnings_and_no_exception(self, m_print, m_file):
        # Act
        self.background_plot.load_data_from_save()

        # Assert
        m_print.assert_called_with("WARNING - Save file may be corrupted: 2 data points could not be appended "
                                   "to the dataset: ['1a.1', '37.698516xxxcz011455354']")
