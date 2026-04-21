# 🌤️ Weather Application

A production-quality desktop weather application built with **Python** and **Tkinter**, powered by the **OpenWeatherMap API**.

---

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [API Key Setup](#-api-key-setup)
- [How to Run](#-how-to-run)
- [How to Use](#-how-to-use)
- [Running Tests](#-running-tests)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [File Descriptions](#-file-descriptions)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 City Search | Search any city worldwide by name |
| 🌡️ Current Weather | Temperature, feels like, humidity, wind speed |
| 🌈 Temperature Color | Red (hot) → Orange → Green → Blue → Dark Blue (freezing) |
| 🖼️ Weather Icons | Auto-downloaded and cached from OpenWeatherMap |
| 📅 5-Day Forecast | One entry per day shown in a card grid |
| ⭐ Favourite Cities | Save cities to a JSON file; quickly re-select from dropdown |
| 🌙 Dark Mode | Toggle between light and dark themes |
| ⌨️ Keyboard Support | Press **Enter** to search |
| 🔄 Run / Refresh | One-click re-fetch for the currently displayed city |
| 🕐 Live Clock | Date and time updated every second |
| ⚡ Non-blocking UI | All network calls run in a background thread |
| 🔁 Auto Retry | Retries up to 3× on slow/dropped connections |
| 📊 Status Bar | Live progress messages during data fetch |

---

## 📁 Project Structure

```
AntiGravity1/
│
├── main.py                  ← Entry point; wires UI ↔ API; manages threads
├── ui.py                    ← Tkinter layout, widgets, theming
├── weather_api.py           ← OpenWeatherMap API calls + icon helpers
├── utils.py                 ← Favourites JSON, colour coding, date/time
│
├── run.bat                  ← Double-click launcher (Windows)
├── requirements.txt         ← Python dependencies
├── README.md                ← This file
│
├── favorites.json           ← Auto-created; stores your saved cities
├── icons/                   ← Auto-created; cached weather icons
│
└── tests/
    └── test_weather_app.py  ← 31 unit tests (pytest)
```

---

## 📦 Requirements

- **Python 3.8+** — [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- **Internet connection** (for live weather data)

### Python Libraries

| Library | Purpose |
|---|---|
| `requests` | HTTP calls to OpenWeatherMap API |
| `Pillow` | Image processing for weather icons |
| `tkinter` | GUI framework (built into Python standard library) |
| `pytest` | Running the test suite |

---

## 🛠️ Installation

### Step 1 — Clone or download the project

Place all project files in a folder, e.g.:
```
E:\PythonProject\AntiGravity1\
```

### Step 2 — Open a terminal in the project folder

```powershell
cd E:\PythonProject\AntiGravity1
```

### Step 3 — Install dependencies

```powershell
pip install -r requirements.txt
```

> If pip is slow or times out, try:
> ```powershell
> pip install requests Pillow --timeout 60
> ```

---

## 🔑 API Key Setup

This app uses the **OpenWeatherMap free API** (no credit card required).

### Step 1 — Get a free API key

1. Go to [https://openweathermap.org/api](https://openweathermap.org/api)
2. Click **Sign Up** and create a free account
3. Go to **My Profile → API keys**
4. Copy the default key (or generate a new one)

> ⚠️ **Note:** New API keys take **10–60 minutes** to activate after creation.

### Step 2 — Add the key to the app

Open `weather_api.py` and replace line 7:

```python
# Before:
API_KEY = "YOUR_API_KEY_HERE"

# After (example):
API_KEY = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
```

---

## ▶️ How to Run

### Option A — Double-click launcher (easiest)

Double-click `run.bat` in File Explorer.

### Option B — Terminal

```powershell
python main.py
```

### Option C — From VS Code

1. Open `main.py`
2. Press **F5** or click the ▶ Run button

---

## 🧭 How to Use

### Searching for a City
1. Type a city name in the search box (e.g., `London`, `New York`, `Tokyo`)
2. Press **Enter** or click **Search**
3. Weather data and the 5-day forecast appear automatically

### 🔄 Refresh Button
- Click **🔄 Run** to re-fetch data for the city currently displayed
- Useful for getting the latest weather without retyping

### ⭐ Favourite Cities
- Click the **♡** heart button (top right of the weather card) to save a city
- The heart turns **♥** when saved
- Access saved cities from the **dropdown** in the top bar
- Click the heart again to remove from favourites

### 🌙 Dark Mode
- Click **Toggle Dark Mode** at the bottom right
- Click again to switch back to light mode

### 📊 Status Bar (bottom left)
Shows what the app is currently doing:
- `Fetching weather data…`
- `Fetching 5-day forecast…`
- `Loading icons…`
- `Ready` — all done

---

## 🧪 Running Unit Tests

### Install test dependencies

```powershell
pip install pytest requests-mock
```

### Run all 31 tests

```powershell
python -m pytest tests/ -v
```

### Expected output

```
tests/test_weather_app.py::TestGetTempColor::test_cold_temperature     PASSED
tests/test_weather_app.py::TestGetTempColor::test_freezing_temperature PASSED
...
========================= 31 passed in 6.31s =========================
```

### Test coverage summary

| Test Class | What is tested |
|---|---|
| `TestGetTempColor` | All 5 temperature colour bands |
| `TestGetCurrentDatetimeStr` | Date/time format output |
| `TestFavoritesCRUD` | Save, load, remove, duplicate, corrupted file |
| `TestFetchCurrentWeather` | HTTP 200, 404, 401, timeout, connection error |
| `TestFetchForecast` | 5-day fetch, deduplication, connection error |
| `TestFetchIconBytes` | Download success, network failure → None |
| `TestBytesToPhotoimage` | Invalid/empty bytes → None (no crash) |
| `TestLiveAPIIntegration` | Live API smoke test (auto-skipped without key) |

---

## ⚙️ Configuration

All network settings are at the top of `weather_api.py`:

```python
TIMEOUT      = (10, 30)   # (connect seconds, read seconds)
MAX_RETRIES  = 3          # retry attempts on timeout/connection error
RETRY_DELAY  = 2          # seconds between retries (doubles each attempt)
ICON_TIMEOUT = (5, 15)    # shorter timeout for non-critical icon downloads
```

Adjust these if your connection is very slow or you want faster failure.

---

## 🔧 Troubleshooting

### ❌ "City not found"
- Double-check the spelling
- Use English city names (e.g., `Munich` not `München`)
- Try adding the country code: `London,GB`

### ❌ "Request timed out"
- The app retries up to 3 times automatically
- Check your internet connection
- Increase `TIMEOUT` in `weather_api.py` (e.g., change `30` to `60`)

### ❌ "Invalid API key"
- Make sure you pasted the key correctly into `weather_api.py`
- New keys take up to 60 minutes to activate — wait and try again

### ❌ "No module named 'PIL'"
```powershell
pip install Pillow
```

### ❌ "No module named 'requests'"
```powershell
pip install requests
```

### ❌ Icons not showing
- Icons are non-critical — weather data will still display
- Icons are cached in the `icons/` folder after the first download
- Delete the `icons/` folder to force a fresh download

### ❌ App window won't open / crashes immediately
- Run from terminal to see the error message:
  ```powershell
  python main.py
  ```
- Make sure Python 3.8+ is installed:
  ```powershell
  python --version
  ```

---

## 📄 File Descriptions

### `main.py`
Entry point. Creates the Tkinter root window and `WeatherApp` instance.  
Handles the threading pipeline: search → fetch weather → fetch forecast → fetch icons → update UI.  
All `root.after(0, ...)` calls ensure UI updates happen safely on the main thread.

### `ui.py`
Contains the `WeatherAppUI` class — every Tkinter widget lives here.  
Responsibilities: layout, theming (light/dark), loading states, favorites dropdown, live clock.

### `weather_api.py`
All external HTTP calls. Key functions:
- `fetch_current_weather(city)` — returns current weather dict
- `fetch_forecast(city)` — returns list of 5 daily forecast dicts
- `fetch_icon_bytes(code, size)` — downloads icon, caches to disk, returns raw bytes
- `bytes_to_photoimage(bytes)` — converts bytes to `ImageTk.PhotoImage` (main thread only)

### `utils.py`
Pure helper functions with no Tkinter dependency:
- `load_favorites()` / `save_favorite()` / `remove_favorite()` — JSON persistence
- `get_temp_color(temp)` — returns hex colour based on temperature
- `get_current_datetime_str()` — formatted date and time string

### `tests/test_weather_app.py`
31 unit tests using `unittest` and `unittest.mock`. No real network calls are made (all mocked), except for the optional `TestLiveAPIIntegration` class which is skipped if no real API key is set.

### `run.bat`
Windows batch file. Double-click to launch the app. Shows a helpful error if Python is missing or dependencies aren't installed.

### `favorites.json`
Auto-created on first save. Stores a simple JSON list of city strings:
```json
["London, GB", "New York, US", "Tokyo, JP"]
```

### `icons/`
Auto-created directory. Weather icons are cached here as PNG files after first download, named as `{icon_code}_{size}.png` (e.g., `10d_2x.png`).
