import tkinter as tk
from tkinter import messagebox
import threading
from datetime import datetime
import io

import weather_api
import utils
from ui import WeatherAppUI


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.ui = WeatherAppUI(
            root,
            search_callback=self.handle_search,
            toggle_fav_callback=self.handle_toggle_fav,
            theme_callback=self.handle_theme_change
        )

        # Keep references to PhotoImages to prevent garbage collection
        self.current_icon = None
        self.forecast_icons = []

    # ─────────────────────────────────────────────
    # Search trigger → spawn a single background thread
    # ─────────────────────────────────────────────
    def handle_search(self, city):
        """Kick off the whole data-fetch pipeline in a daemon thread."""
        thread = threading.Thread(target=self._fetch_all, args=(city,), daemon=True)
        thread.start()

    # ─────────────────────────────────────────────
    # Background thread: fetch data + icons, then
    # hand results back to the main thread safely.
    # ─────────────────────────────────────────────
    def _set_status(self, msg):
        """Thread-safe status label update."""
        self.root.after(0, self.ui.status_label.config, {"text": msg, "fg": "#1a73e8"})

    def _fetch_all(self, city):
        """
        All network I/O runs here – never touch Tkinter widgets from
        this method.  Use root.after(0, ...) to schedule UI updates.
        """
        # 1. Current weather ──────────────────────
        self._set_status("Fetching weather data…")
        current_data, error = weather_api.fetch_current_weather(city)
        if error:
            self.root.after(0, self.ui.set_loading, False)
            self.root.after(0, messagebox.showerror, "Error", error)
            return

        # 2. Forecast data ────────────────────────
        self._set_status("Fetching 5-day forecast…")
        forecast_data, _ = weather_api.fetch_forecast(city)

        # 3. Fetch current-weather icon (network, returns raw bytes) ──
        self._set_status("Loading icons…")
        current_icon_code = current_data['weather'][0]['icon']
        current_icon_bytes = weather_api.fetch_icon_bytes(current_icon_code, size="2x")

        # 4. Fetch forecast icons (network) ───────
        forecast_icon_bytes_list = []
        if forecast_data:
            for item in forecast_data[:5]:
                icon_code = item['weather'][0]['icon']
                icon_bytes = weather_api.fetch_icon_bytes(icon_code, size="")
                forecast_icon_bytes_list.append(icon_bytes)

        # 5. Schedule UI update on main thread ────
        self.root.after(0, self._update_ui,
                        current_data, current_icon_bytes,
                        forecast_data, forecast_icon_bytes_list)

    # ─────────────────────────────────────────────
    # Main thread: build PhotoImages + update widgets
    # ─────────────────────────────────────────────
    def _update_ui(self, current_data, current_icon_bytes,
                   forecast_data, forecast_icon_bytes_list):
        """Called on the main thread – safe to touch all Tkinter widgets."""
        # --- Current weather card ----------------
        city_name = f"{current_data['name']}, {current_data['sys']['country']}"
        temp      = current_data['main']['temp']
        desc      = current_data['weather'][0]['description'].capitalize()
        humidity  = current_data['main']['humidity']
        wind      = current_data['wind']['speed']
        feels     = current_data['main']['feels_like']

        self.ui.city_label.config(text=city_name)
        self.ui.desc_label.config(text=desc)
        self.ui.humidity_label.config(text=f"Humidity: {humidity}%")
        self.ui.wind_label.config(text=f"Wind: {wind} m/s")
        self.ui.feels_label.config(text=f"Feels like: {feels:.1f}°C")

        # Temperature with color coding
        self.ui.temp_label.config(text=f"{temp:.1f}°C")
        color = utils.get_temp_color(temp)
        self.ui.temp_label.config(fg=color if not self.ui.is_dark_mode else "#ffffff")

        # Build PhotoImage for current icon (must be on main thread)
        if current_icon_bytes:
            self.current_icon = weather_api.bytes_to_photoimage(current_icon_bytes)
            if self.current_icon:
                self.ui.icon_label.config(image=self.current_icon)

        # Favourite heart button
        favs = utils.load_favorites()
        self.ui.fav_btn.config(text="♥" if city_name in favs else "♡")

        # --- 5-Day Forecast ----------------------
        if forecast_data:
            self.forecast_icons = []   # drop old references
            for i, item in enumerate(forecast_data[:5]):
                date_obj = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
                day_name = date_obj.strftime("%a")
                f_temp   = item['main']['temp']

                card = self.ui.forecast_cards[i]
                card['day'].config(text=day_name)
                card['temp'].config(text=f"{f_temp:.1f}°C")

                # Build PhotoImage for forecast icon
                if i < len(forecast_icon_bytes_list) and forecast_icon_bytes_list[i]:
                    photo = weather_api.bytes_to_photoimage(forecast_icon_bytes_list[i])
                    if photo:
                        self.forecast_icons.append(photo)
                        card['icon'].config(image=photo)

        self.ui.set_loading(False)

    # ─────────────────────────────────────────────
    # Favourites
    # ─────────────────────────────────────────────
    def handle_toggle_fav(self, city):
        """Add or remove the current city from favourites."""
        favs = utils.load_favorites()
        if city in favs:
            utils.remove_favorite(city)
            self.ui.fav_btn.config(text="♡")
        else:
            utils.save_favorite(city)
            self.ui.fav_btn.config(text="♥")
        self.ui.update_favorites_dropdown()

    # ─────────────────────────────────────────────
    # Theme change
    # ─────────────────────────────────────────────
    def handle_theme_change(self):
        """Re-apply temperature colour in light mode after theme switch."""
        if not self.ui.is_dark_mode:
            temp_text = self.ui.temp_label.cget("text")
            if temp_text not in ("--°C", ""):
                try:
                    temp_val = float(temp_text.replace("°C", ""))
                    self.ui.temp_label.config(fg=utils.get_temp_color(temp_val))
                except ValueError:
                    pass


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
