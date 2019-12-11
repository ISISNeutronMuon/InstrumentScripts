# Set genie python to simulate
import os
os.environ["GENIE_SIMULATE"] = "1"

# Imports come after to prevent import of genie python not in simulation
import unittest
import six.moves
from technique.muon import run_control
from genie_python import genie as g
if six.PY3:
    from unittest.mock import patch, MagicMock
else:
    from mock import patch, MagicMock


class TestRunControl(unittest.TestCase):

    def setUp(self):
        self.get_input_call_count = 0

    @patch.object(g, 'change_title')
    def test_WHEN_begin_pre_cmd_quiet_THEN_do_not_change_title(self, _):
        # Act
        run_control.begin_precmd(quiet=True)

        # Assert
        self.assertFalse(g.change_title.called, "Should not have called g.change_title(title)")

    @patch.object(g, 'change_title')
    @patch.object(run_control, 'set_label')
    @patch('technique.muon.run_control.get_input', return_value="my_title")
    def test_WHEN_begin_pre_cmd_not_quiet_THEN_title_changed(self, _, set_label,  __):
        # Act
        run_control.begin_precmd(quiet=False)

        # Assert
        self.assertTrue(g.change_title.called, "Should have called g.change_title(my_title)")
        self.assertTrue(set_label.called, "Should have called run_control.set_label()")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="name")
    def test_WHEN_set_name_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_name_sample_par({"name": "oldname"})

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_name_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_name_sample_par({"name": "oldname"})

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="orient")
    def test_WHEN_set_orient_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_orient_sample_par({"geometry": "oldorient"})

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_orient_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_orient_sample_par({"geometry": "oldorient"})

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="temp")
    def test_WHEN_set_temp_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"temp": "oldtemp"})

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_temp_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"temp": "oldTemp"})

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="field")
    def test_WHEN_set_field_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"field": "oldfield"})

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_field_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"field": "oldfield"})

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_beamline_par")
    @patch('technique.muon.run_control.get_input', return_value="geo")
    def test_WHEN_set_geo_beamline_par_to_non_empty_THEN_beamline_par_changed(self, _, __):
        # Act
        run_control.set_geometry_beamline_par({"geo": "oldGeo"})

        # Assert
        self.assertTrue(g.change_beamline_par.called, "Should have called to set beamline param")

    @patch.object(g, "change_beamline_par")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_geo_beamline_par_to_empty_THEN_beamline_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"field": "oldGeo"})

        # Assert
        self.assertFalse(g.change_beamline_par.called, "Should not have called to set beamline param")

    @patch.object(g, "change_rb")
    @patch('technique.muon.run_control.get_input', return_value="rb_num")
    def test_WHEN_set_rb_num_to_non_empty_THEN_rb_num_changed(self, _, __):
        # Act
        run_control.set_rb_num()

        # Assert
        self.assertTrue(g.change_rb.called, "Should have called to set rb num")

    @patch.object(g, "change_rb")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_rb_num_to_non_empty_THEN_rb_num_changed(self, _, __):
        # Act
        run_control.set_rb_num()

        # Assert
        self.assertFalse(g.change_rb.called, "Should not have called to set rb num")

    @patch.object(g, "change_users")
    @patch('technique.muon.run_control.get_input', return_value="new users")
    def test_WHEN_set_users_to_non_empty_THEN_users_changed(self, _, __):
        # Act
        run_control.set_users()

        # Assert
        self.assertTrue(g.change_users.called, "Should have called to set new users")

    @patch.object(g, "change_users")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_geo_beamline_par_to_non_empty_THEN_beamline_par_changed(self, _, __):
        # Act
        run_control.set_users()

        # Assert
        self.assertFalse(g.change_users.called, "Should not have called to set new users")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="new comment")
    def test_WHEN_set_comments_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"comments": "oldcomments"})

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.run_control.get_input', return_value="")
    def test_WHEN_set_comments_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        run_control.set_temp_sample_par({"comments": "oldcomments"})

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_title")
    @patch('technique.muon.run_control.get_input', return_value="n")
    def test_WHEN_end_pre_cmd_not_quiet_label_correct_THEN_input_called_once(self, _, __):
        # Act
        run_control.end_precmd(quiet=False)

        # Assert
        self.assertTrue(g.change_title.called, "Should have called to set title")

    @patch.object(g, "change_title")
    @patch('technique.muon.run_control.get_input', return_value="y")
    def test_WHEN_end_pre_cmd_not_quiet_label_correct_THEN_input_called_once(self, _, __):
        # Act
        run_control.end_precmd(quiet=False)

        # Assert
        self.assertFalse(g.change_title.called, "Should have called to set title")

    def end_pre_cmd_get_input(self, input_promt):
        if input_promt == "Is the run information correct (y/n)?":
            self.get_input_call_count += 1
            if self.get_input_call_count > 2:
                return "y"
        return "n"

    @patch.object(run_control, "set_label")
    def test_WHEN_end_pre_cmd_run_information_incorrect_twice_THEN_set_label_called_twice(self, set_label):
        # Arrange
        run_control.get_input = MagicMock(side_effect=self.end_pre_cmd_get_input)

        # Act
        run_control.end_precmd(quiet=False)

        # Assert
        self.assertEquals(set_label.call_count, 2, "Run information rejected twice so should have asked "
                                                   "user to set the labels 2 times")

