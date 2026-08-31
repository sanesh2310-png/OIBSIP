"""
Advanced-Tier Weather App — MOCK / DEMO VERSION (No API key required)
--------------------------------------------------------------------------
GUI version that generates realistic-looking sample weather data locally
instead of calling a real weather API. Lets you demo the full interface
(icons, hourly panel, daily panel, unit toggle) with zero setup.

IMPORTANT: data shown is randomly generated, NOT live weather. See
README.md for how to switch to a real API later.

Feature checklist covered (with simulated data instead of a live API):
  - GUI window with a city input field, "Get Weather" button, results panel
  - Weather "icons" — simple emoji/text icons standing in for real
    OpenWeatherMap icon images (no internet download needed)
  - Hourly forecast panel: next 6 hours (simulated)
  - Daily forecast panel: next 5 days (simulated)
  - Unit toggle: Celsius / Fahrenheit switch button
  - Error messages shown inside the GUI (not terminal print statements)

Run:
    python advanced_weather_mock.py
"""

import random
import tkinter as tk
from datetime import datetime, timedelta

CONDITIONS = [
    ("Clear Sky", "☀️"), ("Few Clouds", "🌤️"), ("Scattered Clouds", "⛅"),
    ("Broken Clouds", "☁️"), ("Light Rain", "🌦️"), ("Moderate Rain", "🌧️"),
    ("Thunderstorm", "⛈️"), ("Snow", "❄️"), ("Mist", "🌫️"),
]


def random_condition():
    return random.choice(CONDITIONS)


class WeatherAppMock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App — Demo Mode")
        self.geometry("640x600")
        self.configure(bg="#eef2f7")
        self.resizable(False, False)

        self.unit = "C"  # "C" or "F"
        self.last_city = None
        self.last_current = None
        self.last_hourly = None
        self.last_daily = None

        self._build_widgets()

    # ---- UI construction ----

    def _build_widgets(self):
        banner = tk.Label(
            self, text="⚠ DEMO MODE — showing sample data, not live weather",
            bg="#fef3c7", fg="#92400e", font=("Segoe UI", 9, "bold")
        )
        banner.pack(fill="x")

        top = tk.Frame(self, bg="#eef2f7")
        top.pack(fill="x", padx=16, pady=12)

        tk.Label(top, text="City or ZIP:", bg="#eef2f7", font=("Segoe UI", 11)).pack(side="left")
        self.city_entry = tk.Entry(top, font=("Segoe UI", 11), width=22)
        self.city_entry.pack(side="left", padx=8)
        self.city_entry.bind("<Return>", lambda e: self.on_get_weather())

        tk.Button(top, text="Get Weather", bg="#2563eb", fg="white", bd=0,
                  command=self.on_get_weather, cursor="hand2").pack(side="left", padx=6)

        self.unit_btn = tk.Button(top, text="Switch to °F", bg="#f8fafc", bd=1,
                                   command=self.on_toggle_unit, cursor="hand2")
        self.unit_btn.pack(side="left", padx=6)

        self.status_label = tk.Label(self, text="", bg="#eef2f7", fg="#dc2626", font=("Segoe UI", 10), wraplength=600)
        self.status_label.pack(pady=(0, 6))

        # --- Current weather panel ---
        self.current_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        self.current_frame.pack(fill="x", padx=16, pady=6)

        self.icon_label = tk.Label(self.current_frame, text="", font=("Segoe UI", 40), bg="white")
        self.icon_label.grid(row=0, column=0, rowspan=4, padx=16, pady=12)

        self.city_label = tk.Label(self.current_frame, text="—", font=("Segoe UI", 16, "bold"), bg="white")
        self.city_label.grid(row=0, column=1, sticky="w", pady=(12, 0))

        self.temp_label = tk.Label(self.current_frame, text="", font=("Segoe UI", 22, "bold"), bg="white")
        self.temp_label.grid(row=1, column=1, sticky="w")

        self.condition_label = tk.Label(self.current_frame, text="", font=("Segoe UI", 11), bg="white")
        self.condition_label.grid(row=2, column=1, sticky="w")

        self.details_label = tk.Label(self.current_frame, text="", font=("Segoe UI", 10), bg="white", fg="#4b5563")
        self.details_label.grid(row=3, column=1, sticky="w", pady=(0, 12))

        # --- Hourly forecast panel ---
        tk.Label(self, text="Next 6 hours", font=("Segoe UI", 11, "bold"), bg="#eef2f7").pack(anchor="w", padx=16, pady=(10, 2))
        self.hourly_frame = tk.Frame(self, bg="#eef2f7")
        self.hourly_frame.pack(fill="x", padx=16)

        # --- Daily forecast panel ---
        tk.Label(self, text="Next 5 days", font=("Segoe UI", 11, "bold"), bg="#eef2f7").pack(anchor="w", padx=16, pady=(14, 2))
        self.daily_frame = tk.Frame(self, bg="#eef2f7")
        self.daily_frame.pack(fill="x", padx=16)

    # ---- Mock "API" ----

    def generate_mock_data(self, city):
        if "error" in city.lower():
            raise ValueError(f"City '{city}' not found. Check the spelling and try again. (simulated error)")

        condition, icon = random_condition()
        current = {
            "city": city.title(),
            "temp_c": round(random.uniform(-5, 40), 1),
            "humidity": random.randint(20, 95),
            "condition": condition,
            "icon": icon,
            "wind_speed": round(random.uniform(0, 15), 1),
        }

        hourly = []
        now = datetime.now()
        for i in range(1, 7):
            cond, ic = random_condition()
            hourly.append({
                "time": now + timedelta(hours=i),
                "temp_c": round(random.uniform(-5, 40), 1),
                "icon": ic,
            })

        daily = []
        for i in range(1, 6):
            cond, ic = random_condition()
            daily.append({
                "date": now + timedelta(days=i),
                "temp_c": round(random.uniform(-5, 40), 1),
                "icon": ic,
            })

        return current, hourly, daily

    # ---- Event handlers ----

    def on_get_weather(self):
        city = self.city_entry.get().strip()
        self.status_label.configure(text="")

        if not city:
            self.status_label.configure(text="Please enter a city name or ZIP code.")
            return

        try:
            current, hourly, daily = self.generate_mock_data(city)
        except ValueError as e:
            self.status_label.configure(text=str(e))
            return

        self.last_city = city
        self.last_current = current
        self.last_hourly = hourly
        self.last_daily = daily
        self._render_current(current)
        self._render_hourly(hourly)
        self._render_daily(daily)

    def on_toggle_unit(self):
        self.unit = "F" if self.unit == "C" else "C"
        self.unit_btn.configure(text="Switch to °F" if self.unit == "C" else "Switch to °C")
        # Re-render with cached data in the new unit (no need to regenerate)
        if self.last_current is not None:
            self._render_current(self.last_current)
            self._render_hourly(self.last_hourly)
            self._render_daily(self.last_daily)

    # ---- Rendering ----

    def _convert_temp(self, temp_c):
        if self.unit == "C":
            return f"{temp_c:.1f}°C"
        return f"{(temp_c * 9 / 5 + 32):.1f}°F"

    def _render_current(self, data):
        self.city_label.configure(text=data["city"])
        self.temp_label.configure(text=self._convert_temp(data["temp_c"]))
        self.condition_label.configure(text=data["condition"])
        self.details_label.configure(text=f"Humidity: {data['humidity']}%   |   Wind: {data['wind_speed']} m/s")
        self.icon_label.configure(text=data["icon"])

    def _render_hourly(self, hourly):
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        for entry in hourly:
            card = tk.Frame(self.hourly_frame, bg="white", bd=1, relief="solid")
            card.pack(side="left", padx=4, pady=4, fill="y")

            tk.Label(card, text=entry["time"].strftime("%H:%M"), bg="white", font=("Segoe UI", 9)).pack(pady=(6, 0))
            tk.Label(card, text=entry["icon"], font=("Segoe UI", 18), bg="white").pack()
            tk.Label(card, text=self._convert_temp(entry["temp_c"]), bg="white", font=("Segoe UI", 9, "bold")).pack(pady=(0, 6))

    def _render_daily(self, daily):
        for widget in self.daily_frame.winfo_children():
            widget.destroy()

        for entry in daily:
            card = tk.Frame(self.daily_frame, bg="white", bd=1, relief="solid")
            card.pack(side="left", padx=4, pady=4, fill="y")

            tk.Label(card, text=entry["date"].strftime("%a"), bg="white", font=("Segoe UI", 9, "bold")).pack(pady=(6, 0))
            tk.Label(card, text=entry["icon"], font=("Segoe UI", 18), bg="white").pack()
            tk.Label(card, text=self._convert_temp(entry["temp_c"]), bg="white", font=("Segoe UI", 9)).pack(pady=(0, 6))


if __name__ == "__main__":
    app = WeatherAppMock()
    app.mainloop()
