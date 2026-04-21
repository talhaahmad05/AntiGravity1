import json
import os
from datetime import datetime

FAVORITES_FILE = "favorites.json"

def load_favorites():
    """Load favorite cities from JSON file."""
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading favorites: {e}")
        return []

def save_favorite(city):
    """Add a city to favorites."""
    favorites = load_favorites()
    if city and city not in favorites:
        favorites.append(city)
        try:
            with open(FAVORITES_FILE, "w") as f:
                json.dump(favorites, f)
        except Exception as e:
            print(f"Error saving favorite: {e}")

def remove_favorite(city):
    """Remove a city from favorites."""
    favorites = load_favorites()
    if city in favorites:
        favorites.remove(city)
        try:
            with open(FAVORITES_FILE, "w") as f:
                json.dump(favorites, f)
        except Exception as e:
            print(f"Error removing favorite: {e}")

def get_temp_color(temp_celsius):
    """Return a color code based on temperature."""
    if temp_celsius <= 0:
        return "#005c99" # Dark Blue (Freezing)
    elif temp_celsius <= 10:
        return "#3399ff" # Light Blue (Cold)
    elif temp_celsius <= 20:
        return "#00b300" # Green (Mild)
    elif temp_celsius <= 30:
        return "#e68a00" # Orange (Warm)
    else:
        return "#cc0000" # Red (Hot)

def get_current_datetime_str():
    """Return formatted current date and time."""
    now = datetime.now()
    return now.strftime("%A, %b %d, %Y | %I:%M %p")
