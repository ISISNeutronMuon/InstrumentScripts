# Set genie python to simulate
import os
os.environ["GENIE_SIMULATE"] = "1"

# Imports come after to prevent import of genie python not in simulation
import unittest
from technique.muon import muon_begin_end
from genie_python import genie as g
from unittest.mock import patch, MagicMock


class TestRunControl(unittest.TestCase):

    def setUp(self):
        self.get_input_call_count = 0

    @patch.object(g, 'change_title')
    def test_WHEN_begin_pre_cmd_quiet_THEN_change_title(self, _):
        # Act
        muon_begin_end.begin_precmd(quiet=True)

        # Assert
        self.assertTrue(g.change_title.called, "Should not have called g.change_title(title)")

    @patch.object(g, 'change_title')
    @patch.object(muon_begin_end, 'set_label')
    @patch('technique.muon.muon_begin_end.get_input', return_value="my_title")
    def test_WHEN_begin_pre_cmd_not_quiet_THEN_title_changed(self, _, set_label,  __):
        # Act
        muon_begin_end.begin_precmd(quiet=False)

        # Assert
        self.assertTrue(set_label.called, "Should have called muon_begin_end.set_label()")

    @patch.object(g, 'change_title')
    @patch('technique.muon.muon_begin_end.get_input', return_value="my_title")
    def test_WHEN_set_label_with_no_change_called_THEN_title_changed(self, _, __):
        # Act
        muon_begin_end.set_label(sample=False, orient=False, temp=False, field=False,
                                 geometry=False, rb_num=False, exp_team=False, comment=False)
        # Assert
        self.assertTrue(g.change_title.called, "Should have been called to set the title even if nothing changed")

    @patch.object(g, 'change_title')
    @patch('technique.muon.muon_begin_end.get_input', return_value="my_sample_par")
    def test_WHEN_set_label_with_change_called_THEN_title_changed(self, _, __):
        # Act
        muon_begin_end.set_label(sample=True, orient=True, temp=True, field=True,
                                 geometry=False, rb_num=False, exp_team=True, comment=True)
        # Assert
        self.assertTrue(g.change_title.called, "Should have been called to set the title even if nothing changed")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="name")
    def test_WHEN_set_name_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_sample_pars = {"name": "oldname"}
        muon_begin_end.set_name_sample_par(old_sample_pars)

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_name_sample_par_to_empty_THEN_sample_par_not_changed(self, _, __):
        # Act
        old_sample_pars = {"name": "oldname"}
        muon_begin_end.set_name_sample_par(old_sample_pars)

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="orient")
    def test_WHEN_set_orient_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_sample_pars = {"geometry": "oldorient"}
        muon_begin_end.set_orient_sample_par(old_sample_pars)

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_orient_sample_par_to_empty_THEN_sample_par_not_changed(self, _, __):
        # Act
        old_sample_pars = {"geometry": "oldorient"}
        muon_begin_end.set_orient_sample_par(old_sample_pars)

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="temp")
    def test_WHEN_set_temp_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_sample_pars = {"temp": "oldtemp"}
        muon_begin_end.set_temp_sample_par(old_sample_pars)

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_temp_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_samples_pars = {"temp": "oldTemp"}
        muon_begin_end.set_temp_sample_par(old_samples_pars)

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="field")
    def test_WHEN_set_field_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_sample_pars = {"field": "oldfield"}
        muon_begin_end.set_field_sample_par(old_sample_pars)

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_field_sample_par_to_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_sample_pars = {"field": "oldfield"}
        muon_begin_end.set_field_sample_par(old_sample_pars)

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(g, "change_beamline_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="geo")
    def test_WHEN_set_geo_beamline_par_to_non_empty_THEN_beamline_par_changed(self, _, __):
        # Act
        old_beamline_pars = {"geo": "oldGeo"}
        muon_begin_end.set_geometry_beamline_par(old_beamline_pars)

        # Assert
        self.assertTrue(g.change_beamline_par.called, "Should have called to set beamline param")

    @patch.object(g, "change_beamline_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_geo_beamline_par_to_empty_THEN_beamline_par_not_changed(self, _, __):
        # Act
        old_beamline_pars = {}
        muon_begin_end.set_geometry_beamline_par(old_beamline_pars)

        # Assert
        self.assertFalse(g.change_beamline_par.called, "Should not have called to set beamline param")

    @patch.object(g, "change_rb")
    @patch('technique.muon.muon_begin_end.get_input', return_value="rb_num")
    def test_WHEN_set_rb_num_to_non_empty_THEN_rb_num_changed(self, _, __):
        # Act
        muon_begin_end.set_rb_num()

        # Assert
        self.assertTrue(g.change_rb.called, "Should have called to set rb num")

    @patch.object(g, "change_rb")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_rb_num_to_non_empty_THEN_rb_num_changed(self, _, __):
        # Act
        muon_begin_end.set_rb_num()

        # Assert
        self.assertFalse(g.change_rb.called, "Should not have called to set rb num")

    @patch.object(g, "change_users")
    @patch('technique.muon.muon_begin_end.get_input', return_value="new users")
    def test_WHEN_set_users_to_non_empty_THEN_users_changed(self, _, __):
        # Act
        muon_begin_end.set_users()

        # Assert
        self.assertTrue(g.change_users.called, "Should have called to set new users")

    @patch.object(g, "change_users")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_geo_beamline_par_to_non_empty_THEN_beamline_par_changed(self, _, __):
        # Act
        muon_begin_end.set_users()

        # Assert
        self.assertFalse(g.change_users.called, "Should not have called to set new users")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="new comment")
    def test_WHEN_set_comments_sample_par_to_non_empty_THEN_sample_par_changed(self, _, __):
        # Act
        old_sample_pars = {}
        muon_begin_end.set_temp_sample_par(old_sample_pars)

        # Assert
        self.assertTrue(g.change_sample_par.called, "Should have called to set sample param")

    @patch.object(g, "change_sample_par")
    @patch('technique.muon.muon_begin_end.get_input', return_value="")
    def test_WHEN_set_comments_sample_par_to_empty_THEN_sample_par_not_changed(self, _, __):
        # Act
        old_sample_pars = {}
        muon_begin_end.set_temp_sample_par(old_sample_pars)

        # Assert
        self.assertFalse(g.change_sample_par.called, "Should not have called to set sample param")

    @patch.object(muon_begin_end, "set_label")
    @patch('technique.muon.muon_begin_end.get_input', side_effect=["n", "y"])
    def test_WHEN_end_pre_cmd_called_label_incorrect_THEN_change_title_called(self, mock_set_label, _):
        # Act
        muon_begin_end.end_precmd()

        # Assert
        self.assertTrue(mock_set_label.called, "Should have called to set the label")

    @patch.object(g, "change_title")
    @patch('technique.muon.muon_begin_end.get_input', return_value="y")
    def test_WHEN_end_pre_cmd_called_label_correct_THEN_change_title_not_called(self, _, __):
        # Act
        muon_begin_end.end_precmd()

        # Assert
        self.assertFalse(g.change_title.called, "Should not have called to set title")

    def end_pre_cmd_get_input(self, input_prompt):
        if input_prompt == "Is the run information correct (y/n)?":
            self.get_input_call_count += 1
            if self.get_input_call_count > 2:
                return "y"
        return "n"

    @patch.object(muon_begin_end, "set_label")
    def test_WHEN_end_pre_cmd_run_information_incorrect_twice_THEN_set_label_called_twice(self, set_label):
        # Arrange
        muon_begin_end.get_input = MagicMock(side_effect=self.end_pre_cmd_get_input)

        # Act
        muon_begin_end.end_precmd()

        # Assert
        self.assertEqual(set_label.call_count, 2, "Run information rejected twice so should have asked "
                                                   "user to set the labels 2 times")

    @patch('technique.muon.muon_begin_end.get_input', return_value="y")
    def test_WHEN_end_pre_cmd_called_WITH_quiet_set_to_false_THEN_change_title_called(self, mock_get_input):
        # Act
        muon_begin_end.end_precmd(quiet=False)

        # Assert
        self.assertGreater(mock_get_input.call_count, 0, "Set_label method called")

    @patch('technique.muon.muon_begin_end.get_input', return_value="y")
    def test_WHEN_end_pre_cmd_called_WITH_quiet_set_to_true_THEN_change_title_not_called(self, mock_get_input):
        # Act
        muon_begin_end.end_precmd(quiet=True)

        # Assert
        self.assertEqual(mock_get_input.call_count, 0, "Set_label method NOT called")
