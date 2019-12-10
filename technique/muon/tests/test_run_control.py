import unittest
import six.moves
from technique.muon import run_control
from genie_python import genie as g
if six.PY3:
    from unittest.mock import patch
else:
    from mock import patch


class TestRunControl(unittest.TestCase):

    @patch.object(g, 'change_title')
    def test_WHEN_begin_pre_cmd_quiet_THEN_do_not_change_title(self, _):
        # Act
        run_control.begin_precmd(quiet=True)

        # Assert
        self.assertFalse(g.change_title.called, "Should not have called g.change_title(title)")

    @patch.object(g, 'change_title')
    @patch.object(run_control, 'get_input')
    def test_WHEN_begin_pre_cmd_not_quiet_THEN_title_changed(self, _, mock_input):
        # Arrange
        mock_input.return_value = "my_title"

        # Act
        run_control.begin_precmd(quiet=False)

        # Assert
        self.assertTrue(g.change_title.called, "Should have called g.change_title(my_title)")

    @patch.object(run_control, 'get_input')
    def test_WHEN_end_pre_cmd_not_quiet_label_correct_THEN_input_called_once(self, _, ):
