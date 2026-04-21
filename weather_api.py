import requests
import os
import io
import time
from PIL import Image, ImageTk

# ── Replace with your OpenWeatherMap API key ──────────────────────────────────
API_KEY = "60b0f6ab7eefc9117a3c55fbee8f0ffb"
BASE_URL = "https://api.openweathermap.org/data/2.5"
ICON_BASE_URL = "https://openweathermap.org/img/wn"

# ── Network settings ──────────────────────────────────────────────────────────
# connect timeout: how long to wait to establish connection
# read timeout:    how long to wait for the server to send data
TIMEOUT       = (10, 30)   # (connect seconds, read seconds)
MAX_RETRIES   = 3          # number of retry attempts on timeout/network error
RETRY_DELAY   = 2          # seconds to wait between retries
ICON_TIMEOUT  = (5, 15)    # shorter timeout for icons (non-critical)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helper: GET with automatic retry
# ─────────────────────────────────────────────────────────────────────────────
def _get_with_retry(url, timeout=TIMEOUT, max_retries=MAX_RETRIES):
    """
    Perform a GET request with exponential-backoff retries on network/timeout errors.
    Returns the Response object on success, raises on final failure.
    """
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            return response           # success – return immediately
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = RETRY_DELAY * attempt   # 2s, 4s, 6s …
                print(f"[weather_api] Attempt {attempt} failed ({exc.__class__.__name__}). "
                      f"Retrying in {wait}s…")
                time.sleep(wait)
    # All retries exhausted – re-raise the last exception
    raise last_exc


# ─────────────────────────────────────────────────────────────────────────────
# Current weather
# ─────────────────────────────────────────────────────────────────────────────
def fetch_current_weather(city_name):
    """
    Fetch current weather data for a given city.
    Returns: (data_dict, None) on success  |  (None, error_str) on failure.
    Retries automatically up to MAX_RETRIES times on slow connections.
    """
    url = f"{BASE_URL}/weather?q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = _get_with_retry(url)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            return None, "City not found. Please check the spelling."
        if response.status_code == 401:
            return None, "Invalid API key. Please check your credentials."
        return None, f"HTTP Error {response.status_code}: {response.reason}"
    except requests.exceptions.ConnectionError:
        return None, ("No internet connection.\n"
                      "Please check your network and try again.")
    except requests.exceptions.Timeout:
        return None, (f"Request timed out after {MAX_RETRIES} attempts.\n"
                      "Your connection may be slow. Please try again.")
    except requests.exceptions.RequestException as err:
        return None, f"An unexpected error occurred:\n{err}"


# ─────────────────────────────────────────────────────────────────────────────
# 5-day forecast
# ─────────────────────────────────────────────────────────────────────────────
def fetch_forecast(city_name):
    """
    Fetch 5-day / 3-hour forecast and return one representative entry per day
    (preferring the slot closest to 12:00).
    Returns: (list_of_items, None) on success  |  (None, error_str) on failure.
    """
    url = f"{BASE_URL}/forecast?q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = _get_with_retry(url)
        response.raise_for_status()
        data = response.json()

        daily, seen = [], set()

        # First pass – prefer the midday entry
        for item in data.get("list", []):
            date_str, time_str = item["dt_txt"].split(" ")
            if date_str not in seen and time_str >= "12:00:00":
                daily.append(item)
                seen.add(date_str)
            if len(daily) == 5:
                break

        # Fallback – just take the first entry for each missing day
        if len(daily) < 5:
            daily, seen = [], set()
            for item in data.get("list", []):
                date_str = item["dt_txt"].split(" ")[0]
                if date_str not in seen:
                    daily.append(item)
                    seen.add(date_str)
                if len(daily) == 5:
                    break

        return daily, None
    except Exception as exc:
        return None, f"Failed to fetch forecast: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Icon helpers – separated so network I/O stays off the main thread
# ─────────────────────────────────────────────────────────────────────────────
def fetch_icon_bytes(icon_code, size="2x"):
    """
    Download a weather icon and cache it to disk.
    Returns raw PNG bytes, or None on failure.
    Safe to call from any background thread.
    Icons are non-critical – a failure here never blocks weather data.
    """
    icons_dir = "icons"
    os.makedirs(icons_dir, exist_ok=True)

    # Use a size suffix in the filename so "2x" and "" don't collide
    suffix = size if size else "1x"
    cache_path = os.path.join(icons_dir, f"{icon_code}_{suffix}.png")

    # Return cached bytes if the file already exists
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return f.read()
        except OSError:
            pass  # fall through to re-download

    # Build URL: size="" → standard 50×50, "2x" → 100×100
    at_suffix = f"@{size}" if size else ""
    url = f"{ICON_BASE_URL}/{icon_code}{at_suffix}.png"
    try:
        # Icons use a shorter timeout and only 1 retry (non-critical)
        resp = _get_with_retry(url, timeout=ICON_TIMEOUT, max_retries=1)
        resp.raise_for_status()
        data = resp.content
        with open(cache_path, "wb") as f:
            f.write(data)
        return data
    except Exception as exc:
        # Icon failure is non-fatal – just log and return None
        print(f"[weather_api] Icon {icon_code} unavailable: {exc.__class__.__name__}")
        return None


def bytes_to_photoimage(png_bytes):
    """
    Convert raw PNG bytes into a Tkinter PhotoImage.
    MUST be called from the main (Tkinter) thread.
    Returns a PhotoImage or None on failure.
    """
    try:
        img = Image.open(io.BytesIO(png_bytes))
        return ImageTk.PhotoImage(img)
    except Exception as exc:
        print(f"[weather_api] Could not create PhotoImage: {exc}")
        return None
