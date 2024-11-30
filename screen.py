import time
from selenium import webdriver
from datetime import datetime
from PIL import Image
from pathlib import Path

URL = (
    "https://airelib.re"
)

SCREENSHOTS_DIR = Path.cwd().joinpath("screenshots")
if not SCREENSHOTS_DIR.exists():
    SCREENSHOTS_DIR.mkdir()


def get_screenshot():
    # Headless Chrome/Selenium setup
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("disable-infobars")  # disabling infobars
    options.add_argument("--disable-extensions")  # disabling extensions
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")  # Bypass OS security model
    # Thanks to https://stackoverflow.com/a/50642913/2291648 for explaining the arguments above

    timestamp_str = datetime.now().strftime("%b%d-%H")
    screenshot_path = SCREENSHOTS_DIR.joinpath(f"screen_{timestamp_str}.png")
    print(screenshot_path)
    try:
        with webdriver.Chrome(options=options) as driver:
            driver.set_window_size(900, 900)
            driver.execute_cdp_cmd(
                "Browser.grantPermissions",
                {
                    "origin": "https://airelib.re/",
                    "permissions": ["geolocation"],
                },
            )
            driver.execute_cdp_cmd(
                "Emulation.setGeolocationOverride",
                {
                    "latitude": -25.250,
                    "longitude": -57.536,
                    "accuracy": 100,
                },
            )
            driver.get(URL)
            time.sleep(6)
            driver.save_screenshot(screenshot_path._str)

        im = Image.open(screenshot_path)
        # Set box coordinates to crop (in pixels)
        left, top, right, bottom = 200, 170, 700, 550
        cropped_img = im.crop((left, top, right, bottom))
        cropped_img.save(screenshot_path)
    except Exception as e:
        print(type(e), e)
        return None

    return screenshot_path


if __name__ == "__main__":
    get_screenshot()