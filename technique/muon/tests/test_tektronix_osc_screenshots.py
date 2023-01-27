# Set genie python to simulate
import os
os.environ["GENIE_SIMULATE"] = "1"

# Imports come after to prevent import of genie python not in simulation
import unittest
from technique.muon import tektronix_osc_screenshots
from genie_python import genie as g
from unittest.mock import patch, MagicMock

from datetime import datetime

class TestOscScreenshots(unittest.TestCase):
    
    def setUp(self) -> None:
        pass

    @patch("technique.muon.tektronix_osc_screenshots.datetime")
    def test_GIVEN_known_RB_and_time_WHEN_get_filename_called_THEN_correct_format_returned(self, dt):
        rb = "RB101"
        timestamp = datetime(2022, 10, 14, 9, 36, 24, 1204)
        dt.now.return_value = timestamp

        self.assertEqual("RB101_2022-10-14T09-36-24.png", tektronix_osc_screenshots.get_filename(rb))
