"""Screenshot uploads remain bounded without dropping required evidence."""

from unittest import TestCase
from unittest.mock import Mock

from selenium.webdriver.remote.webdriver import WebDriver

from tests.openid_conformance.screenshots import MAX_SCREENSHOT_SIZE, capture_screenshot


class TestScreenshots(TestCase):
    def setUp(self):
        self.driver = Mock(spec=WebDriver)
        self.original_window = {"x": 20, "y": 30, "width": 1280, "height": 960}
        self.driver.get_window_rect.return_value = self.original_window
        self.addCleanup(self.driver.set_window_rect.assert_called_once_with, **self.original_window)

    def test_jpeg_capture(self):
        self.driver.execute_cdp_cmd.return_value = {"data": "/9j/2Q=="}
        self.assertEqual(capture_screenshot(self.driver), "data:image/jpeg;base64,/9j/2Q==")
        self.driver.set_window_size.assert_called_once_with(800, 600)
        self.driver.execute_cdp_cmd.assert_called_once_with(
            "Page.captureScreenshot",
            {"format": "jpeg", "quality": 80, "captureBeyondViewport": False},
        )

    def test_reduces_quality_when_encoded_payload_is_too_large(self):
        self.driver.execute_cdp_cmd.side_effect = [
            {"data": "A" * MAX_SCREENSHOT_SIZE},
            {"data": "/9j/2Q=="},
        ]
        self.assertLessEqual(len(capture_screenshot(self.driver)), MAX_SCREENSHOT_SIZE)
        self.assertEqual(
            [call.args[1]["quality"] for call in self.driver.execute_cdp_cmd.call_args_list],
            [80, 60],
        )

    def test_oversized_evidence_is_an_error(self):
        self.driver.execute_cdp_cmd.return_value = {"data": "A" * MAX_SCREENSHOT_SIZE}
        with self.assertRaisesRegex(ValueError, "500 KB upload limit"):
            capture_screenshot(self.driver)
        self.assertEqual(self.driver.execute_cdp_cmd.call_count, 3)

    def test_capture_error_restores_window(self):
        self.driver.execute_cdp_cmd.side_effect = RuntimeError("Browser capture failed")
        with self.assertRaisesRegex(RuntimeError, "Browser capture failed"):
            capture_screenshot(self.driver)
