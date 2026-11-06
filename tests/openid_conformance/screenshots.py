"""Capture screenshot evidence within the OpenID suite's upload limit."""

from selenium.webdriver.remote.webdriver import WebDriver

# Bound the entire ASCII data URL, which also keeps the decoded image below 500 KB.
MAX_SCREENSHOT_SIZE = 500_000


def capture_screenshot(driver: WebDriver) -> str:
    """Capture actual JPEG data, reduce quality if needed, and restore the window."""
    original_window = driver.get_window_rect()
    try:
        driver.set_window_size(800, 600)
        for quality in (80, 60, 40):
            image = driver.execute_cdp_cmd(
                "Page.captureScreenshot",
                {"format": "jpeg", "quality": quality, "captureBeyondViewport": False},
            )
            screenshot = f"data:image/jpeg;base64,{image['data']}"
            if len(screenshot) <= MAX_SCREENSHOT_SIZE:
                return screenshot
        raise ValueError("Screenshot evidence exceeds the OpenID suite's 500 KB upload limit")
    finally:
        driver.set_window_rect(**original_window)
