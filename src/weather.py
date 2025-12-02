"""
Weather API Client using Open-Meteo (free, no API key required)
"""

import time
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherInfo:
    """Current weather information"""
    temperature_c: float
    temperature_f: float
    feels_like_c: float
    humidity: int
    wind_speed_kmh: float
    wind_direction: int
    wind_gusts_kmh: float
    pressure_hpa: float
    weather_code: int
    weather_description: str
    is_day: bool
    sunrise: str  # HH:MM format
    sunset: str   # HH:MM format
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    last_updated: float  # timestamp


class WeatherClient:
    """Client for Open-Meteo weather API"""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # WMO Weather interpretation codes
    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    def __init__(self, latitude: float, longitude: float,
                 cache_duration_seconds: int = 600):
        self.latitude = latitude
        self.longitude = longitude
        self.cache_duration = cache_duration_seconds
        self._cached_weather: Optional[WeatherInfo] = None
        self._last_fetch: float = 0

    def _fetch_weather(self) -> Optional[WeatherInfo]:
        """Fetch current weather from Open-Meteo API"""
        params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'current': [
                'temperature_2m',
                'relative_humidity_2m',
                'apparent_temperature',
                'weather_code',
                'wind_speed_10m',
                'wind_direction_10m',
                'wind_gusts_10m',
                'surface_pressure',
                'is_day'
            ],
            'daily': [
                'sunrise',
                'sunset',
                'temperature_2m_max',
                'temperature_2m_min',
                'precipitation_sum'
            ],
            'temperature_unit': 'celsius',
            'wind_speed_unit': 'kmh',
            'timezone': 'auto'
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get('current', {})
            daily = data.get('daily', {})

            temp_c = current.get('temperature_2m', 0)
            weather_code = current.get('weather_code', 0)

            # Extract sunrise/sunset times (format: "2024-01-15T07:45")
            sunrise_list = daily.get('sunrise', [''])
            sunset_list = daily.get('sunset', [''])
            sunrise_raw = sunrise_list[0] if sunrise_list else ''
            sunset_raw = sunset_list[0] if sunset_list else ''

            # Convert to HH:MM format
            sunrise = sunrise_raw.split('T')[1][:5] if 'T' in sunrise_raw else ''
            sunset = sunset_raw.split('T')[1][:5] if 'T' in sunset_raw else ''

            # Extract daily values (first element is today)
            temp_max_list = daily.get('temperature_2m_max', [0])
            temp_min_list = daily.get('temperature_2m_min', [0])
            precip_list = daily.get('precipitation_sum', [0])

            weather = WeatherInfo(
                temperature_c=temp_c,
                temperature_f=round(temp_c * 9 / 5 + 32, 1),
                feels_like_c=current.get('apparent_temperature', temp_c),
                humidity=current.get('relative_humidity_2m', 0),
                wind_speed_kmh=current.get('wind_speed_10m', 0),
                wind_direction=current.get('wind_direction_10m', 0),
                wind_gusts_kmh=current.get('wind_gusts_10m', 0),
                pressure_hpa=current.get('surface_pressure', 0),
                weather_code=weather_code,
                weather_description=self.WEATHER_CODES.get(weather_code, "Unknown"),
                is_day=current.get('is_day', 1) == 1,
                sunrise=sunrise,
                sunset=sunset,
                temp_max_c=temp_max_list[0] if temp_max_list else 0,
                temp_min_c=temp_min_list[0] if temp_min_list else 0,
                precipitation_mm=precip_list[0] if precip_list else 0,
                last_updated=time.time()
            )

            return weather

        except requests.RequestException as e:
            print(f"Error fetching weather: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing weather data: {e}")
            return None

    def get_weather(self, force_refresh: bool = False) -> Optional[WeatherInfo]:
        """Get current weather, using cache if available"""
        now = time.time()

        # Return cached data if still valid
        if (not force_refresh and
                self._cached_weather and
                (now - self._last_fetch) < self.cache_duration):
            return self._cached_weather

        # Fetch new data
        weather = self._fetch_weather()
        if weather:
            self._cached_weather = weather
            self._last_fetch = now
            return weather

        # Return stale cache if fetch failed
        return self._cached_weather

    def update_location(self, latitude: float, longitude: float):
        """Update the weather location (clears cache)"""
        if self.latitude != latitude or self.longitude != longitude:
            self.latitude = latitude
            self.longitude = longitude
            self._cached_weather = None
            self._last_fetch = 0

    def get_weather_icon(self, weather_code: int, is_day: bool) -> str:
        """Get a text representation of weather for display"""
        # Map weather codes to simple icons/text
        if weather_code == 0:
            return "SUN" if is_day else "MOON"
        elif weather_code in (1, 2):
            return "PCLD" if is_day else "PCLD"
        elif weather_code == 3:
            return "CLDY"
        elif weather_code in (45, 48):
            return "FOG"
        elif weather_code in (51, 53, 55, 56, 57):
            return "DRZL"
        elif weather_code in (61, 63, 65, 66, 67, 80, 81, 82):
            return "RAIN"
        elif weather_code in (71, 73, 75, 77, 85, 86):
            return "SNOW"
        elif weather_code in (95, 96, 99):
            return "STRM"
        else:
            return "????"

    def get_wind_direction_text(self, degrees: int) -> str:
        """Convert wind direction degrees to compass direction"""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
