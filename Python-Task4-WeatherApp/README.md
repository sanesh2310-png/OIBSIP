# Basic Weather App — Demo Mode (No API Key Required)

A weather app with two tiers, running on **locally generated sample
data** instead of a live weather API — no signup, no API key, no
internet connection required.

- **`beginner_weather_mock.py`** — command-line tool.
- **`advanced_weather_mock.py`** — full GUI (tkinter) with icons,
  hourly/daily forecast panels, and a °C/°F toggle.

## ⚠️ Important: this shows sample data, not real weather

Both scripts generate realistic-looking but **randomly made-up** weather
values (temperature, humidity, condition, wind speed) each time you run
them. This lets you build, run, and demo the full app experience —
input validation, error handling, the GUI layout, forecasts, unit
conversion — without waiting on API key activation or needing internet
access.

**To simulate the "city not found" error path**, type any city name that
contains the word "error" (e.g. `ErrorCity`) — this triggers the same
error-handling code path a real "city not found" API response would.

## Beginner Tier

**Run:**
```bash
python beginner_weather_mock.py
```
No dependencies beyond the Python standard library.

- Enter a city name (empty input is rejected).
- Shows a random but realistic temperature (°C and °F), humidity,
  condition, and wind speed.
- Type a city with "error" in the name to see the simulated
  "city not found" error message.
- Choose to check another location without restarting the script.

## Advanced Tier

**Run:**
```bash
python advanced_weather_mock.py
```
`tkinter` ships with standard Python — no extra install needed. (On some
Linux distros: `sudo apt-get install python3-tk`.)

**How it works:**
1. A yellow banner at the top reminds you this is demo/sample data.
2. Type a city and click **Get Weather** (or press Enter).
3. See a current-conditions panel with an emoji weather icon, temperature,
   condition, humidity, and wind speed.
4. **Next 6 hours** and **Next 5 days** panels show randomly generated
   forecast cards, each with its own icon and temperature.
5. **Switch to °F / °C** toggles units and instantly re-renders using the
   already-generated data (no new "API call" needed).
6. Errors (empty input, simulated "not found") show inside the app as a
   red status message — never only in the terminal.

## Switching to real live data later

When you're ready to use real weather data, you have two good free
options:

**Option A — OpenWeatherMap** (what this project was originally built
around): sign up at openweathermap.org for a free API key, then set it
as an environment variable (`OPENWEATHER_API_KEY`) before running the
non-mock versions of these scripts (`beginner_weather.py` /
`advanced_weather.py`), which call the real API.

**Option B — Open-Meteo** (no signup or API key at all): a free weather
API that works with a plain HTTP request — no account needed. This is
the easiest path if you'd rather skip API key management entirely.

## Files

| File | Purpose |
|---|---|
| `beginner_weather_mock.py` | CLI version, sample data, no API key |
| `advanced_weather_mock.py` | GUI version, sample data, no API key |
