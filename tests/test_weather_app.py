"""
tests/test_weather_app.py
=========================
Unit tests for the Weather Application.

Run with:
    python -m pytest tests/ -v
or
    python -m pytest tests/test_weather_app.py -v

Dependencies:
    pip install pytest requests-mock
"""

import json
import os
import sys
import io
import unittest
from unittest.mock import patch, MagicMock, mock_open

# ── Make sure the project root is on the path ─────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import utils
import weather_api


# ═════════════════════════════════════════════════════════════════════════════
# utils.py Tests
# ═════════════════════════════════════════════════════════════════════════════
class TestGetTempColor(unittest.TestCase):
    """Temperature colour-coding helper."""

    def test_freezing_temperature(self):
        """Temp ≤ 0 should return the dark-blue freezing colour."""
        self.assertEqual(utils.get_temp_color(0), "#005c99")
        self.assertEqual(utils.get_temp_color(-10), "#005c99")

    def test_cold_temperature(self):
        """Temp between 1 and 10 should return light blue."""
        self.assertEqual(utils.get_temp_color(5), "#3399ff")
        self.assertEqual(utils.get_temp_color(10), "#3399ff")

    def test_mild_temperature(self):
        """Temp between 11 and 20 should return green."""
        self.assertEqual(utils.get_temp_color(15), "#00b300")
        self.assertEqual(utils.get_temp_color(20), "#00b300")

    def test_warm_temperature(self):
        """Temp between 21 and 30 should return orange."""
        self.assertEqual(utils.get_temp_color(25), "#e68a00")
        self.assertEqual(utils.get_temp_color(30), "#e68a00")

    def test_hot_temperature(self):
        """Temp above 30 should return red."""
        self.assertEqual(utils.get_temp_color(35), "#cc0000")
        self.assertEqual(utils.get_temp_color(50), "#cc0000")


class TestGetCurrentDatetimeStr(unittest.TestCase):
    """Date/time formatting helper."""

    def test_returns_non_empty_string(self):
        result = utils.get_current_datetime_str()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_contains_pipe_separator(self):
        """Ensure the format includes the ' | ' separator between date and time."""
        result = utils.get_current_datetime_str()
        self.assertIn(" | ", result)


class TestFavoritesCRUD(unittest.TestCase):
    """JSON favorites persistence."""

    FAKE_FILE = "test_favorites.json"

    def setUp(self):
        """Patch FAVORITES_FILE so real disk files are untouched."""
        self.patcher = patch.object(utils, "FAVORITES_FILE", self.FAKE_FILE)
        self.patcher.start()
        # Clean slate
        if os.path.exists(self.FAKE_FILE):
            os.remove(self.FAKE_FILE)

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.FAKE_FILE):
            os.remove(self.FAKE_FILE)

    def test_load_favorites_returns_empty_list_when_file_missing(self):
        result = utils.load_favorites()
        self.assertEqual(result, [])

    def test_save_and_load_favorite(self):
        utils.save_favorite("London")
        result = utils.load_favorites()
        self.assertIn("London", result)

    def test_save_duplicate_city_not_added(self):
        utils.save_favorite("Paris")
        utils.save_favorite("Paris")
        result = utils.load_favorites()
        self.assertEqual(result.count("Paris"), 1)

    def test_save_multiple_cities(self):
        for city in ["Tokyo", "Berlin", "Cairo"]:
            utils.save_favorite(city)
        result = utils.load_favorites()
        self.assertEqual(set(result), {"Tokyo", "Berlin", "Cairo"})

    def test_remove_existing_city(self):
        utils.save_favorite("Sydney")
        utils.remove_favorite("Sydney")
        self.assertNotIn("Sydney", utils.load_favorites())

    def test_remove_non_existent_city_does_not_raise(self):
        """Removing a city not in the list should be a no-op."""
        utils.save_favorite("Oslo")
        utils.remove_favorite("NonExistentCity")   # should not raise
        self.assertIn("Oslo", utils.load_favorites())

    def test_save_empty_string_not_added(self):
        utils.save_favorite("")
        self.assertEqual(utils.load_favorites(), [])

    def test_load_favorites_handles_corrupted_file(self):
        """If the JSON file is corrupted, load should return []."""
        with open(self.FAKE_FILE, "w") as f:
            f.write("NOT VALID JSON!!!")
        result = utils.load_favorites()
        self.assertEqual(result, [])


# ═════════════════════════════════════════════════════════════════════════════
# weather_api.py Tests
# ═════════════════════════════════════════════════════════════════════════════

# ── Shared mock API response payloads ─────────────────────────────────────────
MOCK_CURRENT_WEATHER = {
    "name": "London",
    "sys": {"country": "GB"},
    "main": {
        "temp": 15.3,
        "feels_like": 14.0,
        "humidity": 72
    },
    "weather": [{"description": "light rain", "icon": "10d"}],
    "wind": {"speed": 5.2}
}

MOCK_FORECAST = {
    "list": [
        {
            "dt_txt": "2026-04-22 12:00:00",
            "main": {"temp": 16.0, "feels_like": 14.5, "humidity": 70},
            "weather": [{"description": "cloudy", "icon": "04d"}],
            "wind": {"speed": 4.0}
        },
        {
            "dt_txt": "2026-04-23 12:00:00",
            "main": {"temp": 18.0, "feels_like": 17.0, "humidity": 60},
            "weather": [{"description": "sunny", "icon": "01d"}],
            "wind": {"speed": 3.0}
        },
        {
            "dt_txt": "2026-04-24 12:00:00",
            "main": {"temp": 12.0, "feels_like": 11.0, "humidity": 80},
            "weather": [{"description": "rain", "icon": "09d"}],
            "wind": {"speed": 6.0}
        },
        {
            "dt_txt": "2026-04-25 12:00:00",
            "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 85},
            "weather": [{"description": "drizzle", "icon": "09d"}],
            "wind": {"speed": 5.5}
        },
        {
            "dt_txt": "2026-04-26 12:00:00",
            "main": {"temp": 20.0, "feels_like": 19.0, "humidity": 55},
            "weather": [{"description": "clear sky", "icon": "01d"}],
            "wind": {"speed": 2.0}
        },
    ]
}


class TestFetchCurrentWeather(unittest.TestCase):
    """Tests for the current-weather API call."""

    @patch("weather_api.requests.get")
    def test_successful_fetch_returns_data(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_CURRENT_WEATHER
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_current_weather("London")

        self.assertIsNone(error)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "London")

    @patch("weather_api.requests.get")
    def test_city_not_found_returns_error_string(self, mock_get):
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError()
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_current_weather("Zzzzzz")

        self.assertIsNone(data)
        self.assertIn("not found", error.lower())

    @patch("weather_api.requests.get")
    def test_invalid_api_key_returns_error_string(self, mock_get):
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError()
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_current_weather("London")

        self.assertIsNone(data)
        self.assertIn("api key", error.lower())

    @patch("weather_api.requests.get")
    def test_connection_error_returns_error_string(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError()

        data, error = weather_api.fetch_current_weather("London")

        self.assertIsNone(data)
        self.assertIn("connection", error.lower())

    @patch("weather_api.requests.get")
    def test_timeout_returns_error_string(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout()

        data, error = weather_api.fetch_current_weather("London")

        self.assertIsNone(data)
        self.assertIn("timed out", error.lower())

    @patch("weather_api.requests.get")
    def test_data_fields_present(self, mock_get):
        """Ensure the key fields expected by the UI are present."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_CURRENT_WEATHER
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_current_weather("London")

        self.assertIsNone(error)
        self.assertIn("main", data)
        self.assertIn("temp", data["main"])
        self.assertIn("humidity", data["main"])
        self.assertIn("feels_like", data["main"])
        self.assertIn("wind", data)
        self.assertIn("weather", data)


class TestFetchForecast(unittest.TestCase):
    """Tests for the 5-day forecast API call."""

    @patch("weather_api.requests.get")
    def test_successful_forecast_returns_five_days(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_FORECAST
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_forecast("London")

        self.assertIsNone(error)
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 5)

    @patch("weather_api.requests.get")
    def test_forecast_items_have_required_keys(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_FORECAST
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_forecast("London")

        self.assertIsNone(error)
        for item in data:
            self.assertIn("dt_txt", item)
            self.assertIn("main", item)
            self.assertIn("weather", item)

    @patch("weather_api.requests.get")
    def test_forecast_deduplicates_days(self, mock_get):
        """Duplicate timestamps for the same day should only appear once."""
        duplicated = {
            "list": MOCK_FORECAST["list"] + MOCK_FORECAST["list"]   # 10 entries, 5 unique days
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = duplicated
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data, error = weather_api.fetch_forecast("London")

        self.assertIsNone(error)
        dates = [item["dt_txt"].split(" ")[0] for item in data]
        self.assertEqual(len(dates), len(set(dates)), "Dates should be unique")

    @patch("weather_api.requests.get")
    def test_forecast_connection_error(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError()

        data, error = weather_api.fetch_forecast("London")

        self.assertIsNone(data)
        self.assertIsNotNone(error)


class TestFetchIconBytes(unittest.TestCase):
    """Tests for the icon download helper."""

    def setUp(self):
        self.test_icons_dir = "test_icons_tmp"
        self.original_makedirs = os.makedirs

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_icons_dir):
            shutil.rmtree(self.test_icons_dir)

    @patch("weather_api.requests.get")
    @patch("weather_api.os.makedirs")
    @patch("weather_api.os.path.exists", return_value=False)
    def test_icon_downloaded_and_returned(self, mock_exists, mock_makedirs, mock_get):
        fake_png = b"\x89PNG\r\nFAKEDATA"
        mock_resp = MagicMock()
        mock_resp.content = fake_png
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        m = mock_open()
        with patch("builtins.open", m):
            result = weather_api.fetch_icon_bytes("10d", size="2x")

        self.assertEqual(result, fake_png)

    @patch("weather_api.requests.get")
    @patch("weather_api.os.makedirs")
    @patch("weather_api.os.path.exists", return_value=False)
    def test_returns_none_on_network_error(self, mock_exists, mock_makedirs, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError()

        result = weather_api.fetch_icon_bytes("10d", size="2x")

        self.assertIsNone(result)


class TestBytesToPhotoimage(unittest.TestCase):
    """Tests for the bytes→PhotoImage converter."""

    def test_returns_none_for_invalid_bytes(self):
        """Garbage bytes should not raise – just return None."""
        result = weather_api.bytes_to_photoimage(b"this is not a PNG")
        self.assertIsNone(result)

    def test_returns_none_for_empty_bytes(self):
        result = weather_api.bytes_to_photoimage(b"")
        self.assertIsNone(result)


# ═════════════════════════════════════════════════════════════════════════════
# Integration smoke test (requires real network & API key)
# ═════════════════════════════════════════════════════════════════════════════
class TestLiveAPIIntegration(unittest.TestCase):
    """
    Smoke tests that hit the real OpenWeatherMap API.
    Skipped automatically if the key is still the placeholder.
    """

    def setUp(self):
        if weather_api.API_KEY in ("YOUR_API_KEY_HERE", "", None):
            self.skipTest("Real API key not configured – skipping live tests.")

    def test_fetch_current_weather_live(self):
        data, error = weather_api.fetch_current_weather("London")
        self.assertIsNone(error, f"Live API error: {error}")
        self.assertIsNotNone(data)
        self.assertIn("name", data)

    def test_fetch_forecast_live(self):
        data, error = weather_api.fetch_forecast("London")
        self.assertIsNone(error, f"Live API error: {error}")
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
