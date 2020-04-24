import unittest

from parameterized import parameterized
from hamcrest import *
from mock import patch, Mock

from general.scans.detector import NormalisedIntensityDetector, create_spectra_definition, SPECTRA_RETRY_COUNT
from general.scans.scans import Scan


class MockScan(Scan):

    @property
    def reverse(self):
        pass

    def min(self):
        pass

    def max(self):
        pass

    def map(self, func):
        pass

    def __len__(self):
        return 1



@patch("general.scans.detector.g")
class TestSpectrasWithTimeRange(unittest.TestCase):

    def setup_mock(self, g_mock, initial_frames=0, initial_uamps=0, integrated_spectra=None):
        g_mock.get_runstate = Mock(return_value="SETUP")
        def get_spectrum(specturm, period=1, t_min=None, t_max=None):
            if integrated_spectra is None:
                return 1
            return integrated_spectra[specturm]
        g_mock.integrate_spectrum = Mock(side_effect=get_spectrum)

        g_mock.get_period = Mock(return_value=1)
        g_mock.get_frames = Mock(return_value=initial_frames)
        g_mock.get_uamps = Mock(return_value=initial_uamps)

    def test_GIVEN_no_args_WHEN_detect_THEN_error(self, g_mock):
        detector_routine = NormalisedIntensityDetector()

        assert_that(calling(detector_routine.detector_measurement).with_args(None), raises(ValueError))

    def test_GIVEN_frames_WHEN_detect_THEN_resume_count_for_given_frames_and_pause(self, g_mock):
        initial_frames = 1
        requested_frames = 9
        expected_frame_count = requested_frames + initial_frames
        self.setup_mock(g_mock, initial_frames=initial_frames)

        scan = MockScan()

        detector = NormalisedIntensityDetector()
        with detector(scan, save=False) as detector_routine:

            detector_routine(None, frames=requested_frames)

        g_mock.resume.assert_called_once()
        g_mock.waitfor_frames.assert_called_once_with(expected_frame_count)
        g_mock.pause.assert_called_once()

    def test_GIVEN_upamps_WHEN_detect_THEN_wait_until_correct_upamps(self, g_mock):
        initial_uamps = 1
        requested_uamps = 9
        expected_uamps_count = requested_uamps + initial_uamps
        self.setup_mock(g_mock, initial_uamps=initial_uamps)

        scan = MockScan()

        detector = NormalisedIntensityDetector()
        with detector(scan, save=False) as detector_routine:

            detector_routine(None, uamps=requested_uamps)

        g_mock.waitfor_uamps.assert_called_once_with(expected_uamps_count)

    @parameterized.expand([({"seconds":1}, 1, None, None),
                           ({"minutes":2}, None, 2, None),
                           ({"hours": 3}, None, None, 3),
                           ({"seconds":1, "minutes": 2, "hours": 3}, 1, 2, 3)],)
    def test_GIVEN_seconds_WHEN_detect_THEN_wait_until_correct_upamps(self, g_mock, args, expected_secs, expected_mins, expected_hours):
        self.setup_mock(g_mock)
        scan = MockScan()
        detector = NormalisedIntensityDetector()
        with detector(scan, save=False) as detector_routine:

            detector_routine(None, **args)

        g_mock.waitfor_time.assert_called_once_with(seconds=expected_secs, minutes=expected_mins, hours=expected_hours)

    def test_GIVEN_default_spectra_WHEN_detect_THEN_result_is_default_spectra_average(self, g_mock):
        integrated_detector = 10
        integrated_monitor = 20
        self.setup_mock(g_mock, integrated_spectra={2: integrated_monitor, 3: integrated_detector})

        scan = MockScan()

        detector = NormalisedIntensityDetector()
        with detector(scan, save=False) as detector_routine:

            acc, result = detector_routine(None, frames=1)

        assert_that(result.total, is_(integrated_detector))
        assert_that(result.count, is_(integrated_monitor))

    def test_GIVEN_user_definied_spectra_WHEN_detect_THEN_result_is_user_spectra_average(self, g_mock):
        integrated_detector = 2
        integrated_monitor = 4
        monitor_spectra_number_and_name = 4
        monitor_t_min = 10
        monitor_t_max = 20
        detector_spectra_number_and_name = 5
        detector_t_min = 30
        detector_t_max = 40

        self.setup_mock(g_mock, integrated_spectra={monitor_spectra_number_and_name: integrated_monitor,
                                                    detector_spectra_number_and_name: integrated_detector})
        scan = MockScan()

        detector = NormalisedIntensityDetector(default_detector=detector_spectra_number_and_name,
                                               default_monitor=monitor_spectra_number_and_name,
                                               spectra_definitions=[create_spectra_definition(monitor_spectra_number_and_name, monitor_t_min, monitor_t_max),
                                                              create_spectra_definition(detector_spectra_number_and_name, detector_t_min, detector_t_max)])
        with detector(scan, save=False) as detector_routine:

            acc, result = detector_routine(None, frames=1)

        assert_that(result.total, is_(integrated_detector))
        assert_that(result.count, is_(integrated_monitor))
        g_mock.integrate_spectrum.assert_any_call(monitor_spectra_number_and_name, 1, monitor_t_min, monitor_t_max)
        g_mock.integrate_spectrum.assert_any_call(detector_spectra_number_and_name, 1, detector_t_min, detector_t_max)

    def test_GIVEN_none_returned_by_integrated_spectra_WHEN_detect_THEN_try_again(self, g_mock):

        self.setup_mock(g_mock, integrated_spectra={2: None, 3: None})

        scan = MockScan()

        detector = NormalisedIntensityDetector()
        with detector(scan, save=False) as detector_routine:

            acc, result = detector_routine(None, frames=1)

        assert_that(g_mock.integrate_spectrum.call_count, is_(SPECTRA_RETRY_COUNT * 2),
                    "retry count multiple by two one for detector one for monitor")

    def test_GIVEN_user_definied_spectra_WHEN_detect_using_none_default_monitor_THEN_result_is_user_spectra_average(self, g_mock):
        integrated_detector = 2
        integrated_monitor = 4
        monitor_spectra_number_and_name = 4
        monitor_t_min = 10
        monitor_t_max = 20
        detector_spectra_number = 5
        detector_spectra_name = "myspectra"
        detector_t_min = 30
        detector_t_max = 40

        self.setup_mock(g_mock, integrated_spectra={monitor_spectra_number_and_name: integrated_monitor,
                                                    detector_spectra_number: integrated_detector})
        scan = MockScan()

        detector = NormalisedIntensityDetector(spectra_definitions=[create_spectra_definition(monitor_spectra_number_and_name, monitor_t_min, monitor_t_max),
                                                                    create_spectra_definition(detector_spectra_number, detector_t_min, detector_t_max, detector_spectra_name)])
        with detector(scan, save=False, monitor=monitor_spectra_number_and_name, detector=detector_spectra_name) as detector_routine:

            acc, result = detector_routine(None, frames=1)

        assert_that(result.total, is_(integrated_detector))
        assert_that(result.count, is_(integrated_monitor))


if __name__ == '__main__':
    unittest.main()
