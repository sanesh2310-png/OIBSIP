"""
Beginner-Tier Weather App — MOCK / DEMO VERSION (No API key required)
--------------------------------------------------------------------------
This version does NOT call a real weather API. It generates realistic-
looking sample weather data locally, so you can run and demo the app
immediately without signing up for anything.

IMPORTANT: this is for practice/demo purposes only. The data shown is
NOT real weather — it's randomly generated to look plausible. See
README.md for how to switch to a real API (OpenWeatherMap or Open-Meteo)
later if you want live data.

Feature checklist covered (using mock data instead of a live API call):
  - Prompt user for a city name or ZIP code
  - Generate a "response" shaped like a real weather API result and parse it
  - Display: temperature (°C and °F), humidity %, condition description,
    wind speed
  - Simulated error handling: an empty city, or a city name containing
    "error" (typed on purpose), demonstrates the error-handling path
  - Input validation: reject empty city input

Run:
    python beginner_weather_mock.py
"""

import random

CONDITIONS = [
    "Clear Sky", "Few Clouds", "Scattered Clouds", "Broken Clouds",
    "Light Rain", "Moderate Rain", "Thunderstorm", "Snow", "Mist", "Partly Cloudy",
]


def get_city_input() -> str:
    while True:
        city = input("Enter a city name or ZIP code: ").strip()
        if not city:
            print("  ⚠ City cannot be empty. Please enter a city name or ZIP code.")
            continue
        return city


def generate_mock_weather(city: str) -> dict:
    """
    Generates a fake but realistic-looking weather reading for the given
    city name. Two special inputs simulate error conditions so you can
    see the error-handling path without needing a real API:
      - typing a city name that includes "error" simulates a
        "city not found" response
    """
    if "error" in city.lower():
        raise ValueError(f"City '{city}' not found. Check the spelling and try again. (simulated error)")

    temp_c = round(random.uniform(-5, 40), 1)
    temp_f = round(temp_c * 9 / 5 + 32, 1)
    humidity = random.randint(20, 95)
    condition = random.choice(CONDITIONS)
    wind_speed = round(random.uniform(0, 15), 1)

    return {
        "city": city.title(),
        "temp_c": temp_c,
        "temp_f": temp_f,
        "humidity": humidity,
        "condition": condition,
        "wind_speed": wind_speed,
    }


def display_weather(data: dict):
    print("-" * 45)
    print(f"Weather in {data['city']}  (SAMPLE DATA — not live)")
    print("-" * 45)
    print(f"Temperature : {data['temp_c']}°C  /  {data['temp_f']}°F")
    print(f"Condition   : {data['condition']}")
    print(f"Humidity    : {data['humidity']}%")
    print(f"Wind Speed  : {data['wind_speed']} m/s")
    print("-" * 45)


def main():
    print("=" * 50)
    print("   BASIC WEATHER APP — DEMO MODE (no API key)")
    print("   Shows realistic SAMPLE data, not live weather")
    print("=" * 50)

    while True:
        city = get_city_input()
        try:
            data = generate_mock_weather(city)
            display_weather(data)
        except ValueError as e:
            print(f"  ⚠ {e}")

        again = input("\nCheck another location? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye!")
            break
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExited. Goodbye!")
