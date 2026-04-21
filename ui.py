import tkinter as tk
from tkinter import ttk, messagebox
import utils

class WeatherAppUI:
    def __init__(self, root, search_callback, toggle_fav_callback, theme_callback):
        self.root = root
        self.search_callback = search_callback
        self.toggle_fav_callback = toggle_fav_callback
        self.theme_callback = theme_callback
        
        self.is_dark_mode = False
        
        # Colors
        self.bg_color = "#f0f0f0"
        self.fg_color = "#333333"
        self.card_bg = "#ffffff"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize all UI components."""
        self.root.title("Weather Application")
        self.root.geometry("600x700")
        self.root.configure(bg=self.bg_color)
        self.root.resizable(False, False)
        
        # --- Top Bar (Search & Favorites) ---
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.city_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.city_var, font=("Helvetica", 14))
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        # Bind Enter key to search
        self.search_entry.bind('<Return>', lambda event: self.on_search_clicked())
        
        self.search_btn = ttk.Button(top_frame, text="Search", command=self.on_search_clicked)
        self.search_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Refresh button – re-fetches weather for the current city
        self.refresh_btn = ttk.Button(top_frame, text="🔄 Run", command=self.on_refresh_clicked)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Favorites Dropdown
        self.fav_var = tk.StringVar()
        self.fav_dropdown = ttk.Combobox(top_frame, textvariable=self.fav_var, state="readonly", width=15)
        self.fav_dropdown.pack(side=tk.LEFT)
        self.fav_dropdown.bind("<<ComboboxSelected>>", self.on_favorite_selected)
        self.update_favorites_dropdown()
        
        # --- Date & Time ---
        self.time_label = tk.Label(self.root, text="", font=("Helvetica", 10), bg=self.bg_color, fg=self.fg_color)
        self.time_label.pack(pady=(0, 10))
        self.update_time()
        
        # --- Main Weather Card ---
        self.main_card = tk.Frame(self.root, bg=self.card_bg, bd=2, relief=tk.GROOVE)
        self.main_card.pack(fill=tk.X, padx=20, pady=10)
        
        # City Name & Fav Button
        header_frame = tk.Frame(self.main_card, bg=self.card_bg)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.city_label = tk.Label(header_frame, text="City Name", font=("Helvetica", 24, "bold"), bg=self.card_bg, fg=self.fg_color)
        self.city_label.pack(side=tk.LEFT)
        
        self.fav_btn = tk.Button(header_frame, text="♡", font=("Helvetica", 16), bd=0, bg=self.card_bg, fg="red", cursor="hand2", command=self.on_fav_clicked)
        self.fav_btn.pack(side=tk.RIGHT)
        
        # Weather Icon & Temp
        center_frame = tk.Frame(self.main_card, bg=self.card_bg)
        center_frame.pack(pady=10)
        
        self.icon_label = tk.Label(center_frame, bg=self.card_bg)
        self.icon_label.pack(side=tk.LEFT, padx=10)
        
        self.temp_label = tk.Label(center_frame, text="--°C", font=("Helvetica", 48, "bold"), bg=self.card_bg, fg=self.fg_color)
        self.temp_label.pack(side=tk.LEFT, padx=10)
        
        self.desc_label = tk.Label(self.main_card, text="--", font=("Helvetica", 16), bg=self.card_bg, fg=self.fg_color)
        self.desc_label.pack(pady=(0, 10))
        
        # Details (Humidity, Wind, Feels like)
        details_frame = tk.Frame(self.main_card, bg=self.card_bg)
        details_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.feels_label = tk.Label(details_frame, text="Feels like: --°C", font=("Helvetica", 12), bg=self.card_bg, fg=self.fg_color)
        self.feels_label.pack(side=tk.LEFT, expand=True)
        
        self.humidity_label = tk.Label(details_frame, text="Humidity: --%", font=("Helvetica", 12), bg=self.card_bg, fg=self.fg_color)
        self.humidity_label.pack(side=tk.LEFT, expand=True)
        
        self.wind_label = tk.Label(details_frame, text="Wind: -- m/s", font=("Helvetica", 12), bg=self.card_bg, fg=self.fg_color)
        self.wind_label.pack(side=tk.LEFT, expand=True)
        
        # --- Forecast Section ---
        forecast_lbl = tk.Label(self.root, text="5-Day Forecast", font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.fg_color)
        forecast_lbl.pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        self.forecast_frame = tk.Frame(self.root, bg=self.bg_color)
        self.forecast_frame.pack(fill=tk.X, padx=20)
        
        self.forecast_cards = []
        for i in range(5):
            card = tk.Frame(self.forecast_frame, bg=self.card_bg, bd=1, relief=tk.GROOVE)
            card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            
            day_lbl = tk.Label(card, text="-", font=("Helvetica", 10, "bold"), bg=self.card_bg, fg=self.fg_color)
            day_lbl.pack(pady=(5, 0))
            
            icon_lbl = tk.Label(card, bg=self.card_bg)
            icon_lbl.pack(pady=5)
            
            temp_lbl = tk.Label(card, text="-°C", font=("Helvetica", 12), bg=self.card_bg, fg=self.fg_color)
            temp_lbl.pack(pady=(0, 5))
            
            self.forecast_cards.append({'day': day_lbl, 'icon': icon_lbl, 'temp': temp_lbl, 'frame': card})
            
        # --- Bottom Bar ---
        bottom_frame = tk.Frame(self.root, bg=self.bg_color)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
        
        self.status_label = tk.Label(bottom_frame, text="Ready", font=("Helvetica", 10), bg=self.bg_color, fg="gray")
        self.status_label.pack(side=tk.LEFT)
        
        self.theme_btn = ttk.Button(bottom_frame, text="Toggle Dark Mode", command=self.on_theme_toggled)
        self.theme_btn.pack(side=tk.RIGHT)
        
    def update_time(self):
        """Update the displayed time every second."""
        self.time_label.config(text=utils.get_current_datetime_str())
        self.root.after(1000, self.update_time)
        
    def on_search_clicked(self):
        city = self.city_var.get().strip()
        if city:
            self.set_loading(True)
            self.search_callback(city)
        else:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            
    def on_refresh_clicked(self):
        """Re-run the search for the city currently shown, or fall back to the entry text."""
        # Prefer the city already displayed in the card
        displayed = self.city_label.cget("text")
        city = displayed if displayed not in ("City Name", "") else self.city_var.get().strip()
        if city:
            self.set_loading(True)
            self.search_callback(city)
        else:
            messagebox.showwarning("Input Error", "Please search for a city first.")
            
    def on_favorite_selected(self, event):
        city = self.fav_var.get()
        if city and city != "Select Favorite":
            self.city_var.set(city)
            self.on_search_clicked()
            
    def on_fav_clicked(self):
        city = self.city_label.cget("text")
        if city and city != "City Name":
            self.toggle_fav_callback(city)
            
    def on_theme_toggled(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.theme_callback()
        
    def set_loading(self, is_loading):
        if is_loading:
            self.status_label.config(text="Fetching data...", fg="blue")
            self.search_btn.state(['disabled'])
            self.refresh_btn.state(['disabled'])
        else:
            self.status_label.config(text="Ready", fg="gray")
            self.search_btn.state(['!disabled'])
            self.refresh_btn.state(['!disabled'])
            
    def update_favorites_dropdown(self):
        favs = utils.load_favorites()
        if not favs:
            self.fav_dropdown['values'] = ["No Favorites"]
            self.fav_dropdown.set("No Favorites")
        else:
            self.fav_dropdown['values'] = ["Select Favorite"] + favs
            self.fav_dropdown.set("Select Favorite")
            
    def apply_theme(self):
        if self.is_dark_mode:
            self.bg_color = "#1e1e1e"
            self.fg_color = "#ffffff"
            self.card_bg = "#2d2d2d"
        else:
            self.bg_color = "#f0f0f0"
            self.fg_color = "#333333"
            self.card_bg = "#ffffff"
            
        self.root.configure(bg=self.bg_color)
        
        # Update all widgets
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.bg_color)
            elif isinstance(widget, tk.Label):
                widget.configure(bg=self.bg_color, fg=self.fg_color)
                
        self.main_card.configure(bg=self.card_bg)
        for widget in self.main_card.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.card_bg)
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=self.card_bg, fg=self.fg_color)
                elif isinstance(child, tk.Button):
                    child.configure(bg=self.card_bg)
                    
        self.desc_label.configure(bg=self.card_bg, fg=self.fg_color)
        
        self.forecast_frame.configure(bg=self.bg_color)
        for card_data in self.forecast_cards:
            card_data['frame'].configure(bg=self.card_bg)
            card_data['day'].configure(bg=self.card_bg, fg=self.fg_color)
            card_data['icon'].configure(bg=self.card_bg)
            card_data['temp'].configure(bg=self.card_bg, fg=self.fg_color)
