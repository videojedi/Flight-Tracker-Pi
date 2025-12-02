"""
UI Screens for Flight Tracker Pi
- Loading Screen (startup splash)
- Flight Display Screen (when flights are overhead)
- Idle Screen (time, date, temperature when no flights)
"""

import socket
from datetime import datetime
from typing import Optional
from src.display import DisplayRenderer
from src.flight_tracker import FlightInfo
from src.weather import WeatherInfo
from src.airports import get_airport_city


def get_ip_address() -> str:
    """Get the local IP address of the Pi"""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No network"


class Colors:
    """UI Color scheme"""
    BACKGROUND = '#000000'
    TEXT_PRIMARY = '#FFFFFF'
    TEXT_SECONDARY = '#AAAAAA'
    ACCENT = '#00AAFF'
    ALTITUDE_HIGH = '#00FF00'    # > 30000 ft
    ALTITUDE_MED = '#FFFF00'     # 10000-30000 ft
    ALTITUDE_LOW = '#FF8800'     # < 10000 ft
    CLIMBING = '#00FF00'
    DESCENDING = '#FF4444'
    DIVIDER = '#333333'
    TEMP_HOT = '#FF4444'
    TEMP_WARM = '#FFAA00'
    TEMP_MILD = '#88FF88'
    TEMP_COOL = '#88CCFF'
    TEMP_COLD = '#4488FF'
    WATCHLIST = '#FF00FF'        # Magenta for watchlist aircraft
    WATCHLIST_BG = '#330033'     # Dark magenta background


class LoadingScreen:
    """Splash screen shown during startup"""

    def __init__(self, renderer: DisplayRenderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height

    def render(self, status: str = "Starting..."):
        """Render the loading splash screen"""
        # Clear screen
        self.renderer.display.clear(Colors.BACKGROUND)

        # Draw airplane logo (larger, centered)
        logo_y = 80
        self._draw_airplane_logo(self.width // 2, logo_y, size=60)

        # Title
        self.renderer.draw_centered_text(
            "Flight Tracker Pi", 160,
            font_size='large', color=Colors.TEXT_PRIMARY
        )

        # Subtitle/status
        self.renderer.draw_centered_text(
            status, 210,
            font_size='medium', color=Colors.ACCENT
        )

        # Decorative line
        self.renderer.draw_line(100, 245, self.width - 100, 245,
                                color=Colors.DIVIDER, width=1)

        # Version/credit
        self.renderer.draw_centered_text(
            "Raspberry Pi Flight Display", 260,
            font_size='small', color=Colors.TEXT_SECONDARY
        )

        # IP address in bottom right
        ip_address = get_ip_address()
        self.renderer.draw_text(
            ip_address,
            self.width - 10, self.height - 10,
            font_size='small', color=Colors.TEXT_SECONDARY, anchor='rb'
        )

        # Update display
        self.renderer.display.update()

    def _draw_airplane_logo(self, x: int, y: int, size: int = 60):
        """Draw a stylized airplane logo with radar rings"""
        # Use the renderer's airplane icon but larger and facing up
        self.renderer.draw_airplane_icon(x, y, heading=0, size=size, color=Colors.ACCENT)

        # Draw concentric radar rings around it
        draw = self.renderer.display.get_draw()
        for radius in [size + 10, size + 25, size + 40]:
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                outline=Colors.DIVIDER, width=1
            )


class FlightScreen:
    """Display screen for showing flight information"""

    def __init__(self, renderer: DisplayRenderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height

    def _get_altitude_color(self, altitude_ft: int) -> str:
        """Get color based on altitude"""
        if altitude_ft > 30000:
            return Colors.ALTITUDE_HIGH
        elif altitude_ft > 10000:
            return Colors.ALTITUDE_MED
        else:
            return Colors.ALTITUDE_LOW

    def _format_altitude(self, altitude_ft: int) -> str:
        """Format altitude for display"""
        if altitude_ft >= 1000:
            return f"{altitude_ft // 1000}k ft"
        return f"{altitude_ft} ft"

    def _get_vertical_indicator(self, vertical_speed: int) -> tuple[str, str]:
        """Get vertical speed indicator and color"""
        if vertical_speed > 100:
            return "▲", Colors.CLIMBING
        elif vertical_speed < -100:
            return "▼", Colors.DESCENDING
        else:
            return "→", Colors.TEXT_SECONDARY

    def render(self, flight: FlightInfo, flight_count: int = 1, flight_index: int = 0,
                radius_km: int = 50, watchlist: dict = None):
        """Render the flight display screen"""
        # Check if this aircraft is on the watchlist
        # Watchlist can be dict {reg: name} or list [reg, reg, ...]
        is_watched = False
        watchlist_name = None
        if watchlist and flight.registration:
            reg_upper = flight.registration.upper()
            if isinstance(watchlist, dict):
                # Dictionary format: {registration: name}
                for reg, name in watchlist.items():
                    if reg.upper() == reg_upper:
                        is_watched = True
                        watchlist_name = name
                        break
            else:
                # List format (legacy): [registration, ...]
                is_watched = reg_upper in [w.upper() for w in watchlist]

        # Clear screen - use special background for watchlist aircraft
        bg_color = Colors.WATCHLIST_BG if is_watched else Colors.BACKGROUND
        self.renderer.display.clear(bg_color)

        # Header bar with flight count
        header_color = '#441144' if is_watched else '#111111'
        self.renderer.draw_rect(0, 0, self.width, 35,
                                fill=header_color, outline=Colors.DIVIDER)

        # Flight count indicator (show which flight we're viewing)
        if flight_count > 1:
            self.renderer.draw_text(
                f"{flight_index + 1}/{flight_count} flights in {radius_km} km radius (tap to cycle)",
                10, 8, font_size='small', color=Colors.TEXT_SECONDARY
            )
        else:
            self.renderer.draw_text(
                f"1 flight in {radius_km} km radius",
                10, 8, font_size='small', color=Colors.TEXT_SECONDARY
            )

        # Distance on right
        self.renderer.draw_text(
            f"{flight.distance_km} km",
            self.width - 10, 8, font_size='small',
            color=Colors.ACCENT, anchor='rt'
        )

        # Main flight number (large, centered)
        y_pos = 50
        flight_num = flight.flight_number or flight.callsign
        self.renderer.draw_centered_text(
            flight_num, y_pos,
            font_size='large', color=Colors.TEXT_PRIMARY
        )

        # Airline name
        y_pos = 105
        self.renderer.draw_centered_text(
            flight.airline, y_pos,
            font_size='medium', color=Colors.ACCENT
        )

        # Route: Origin → Destination (with city names)
        y_pos = 135
        route = f"{flight.origin}  →  {flight.destination}"
        self.renderer.draw_centered_text(
            route, y_pos,
            font_size='medium', color=Colors.TEXT_PRIMARY
        )

        # City names below route (smaller font)
        origin_city = get_airport_city(flight.origin)
        dest_city = get_airport_city(flight.destination)
        if origin_city or dest_city:
            y_pos = 158
            city_route = f"{origin_city or flight.origin}  →  {dest_city or flight.destination}"
            self.renderer.draw_centered_text(
                city_route, y_pos,
                font_size='small', color=Colors.TEXT_SECONDARY
            )

        # Divider line
        y_pos = 192
        self.renderer.draw_line(20, y_pos, self.width - 20, y_pos,
                                color=Colors.DIVIDER, width=1)

        # Flight details section
        y_pos = 210

        # Left column: Altitude with vertical indicator
        alt_color = self._get_altitude_color(flight.altitude_ft)
        v_indicator, v_color = self._get_vertical_indicator(flight.vertical_speed)

        self.renderer.draw_text("ALT", 30, y_pos,
                                font_size='small', color=Colors.TEXT_SECONDARY)
        self.renderer.draw_text(
            f"{v_indicator} {self._format_altitude(flight.altitude_ft)}",
            30, y_pos + 20,
            font_size='medium', color=alt_color
        )

        # Middle column: Speed
        self.renderer.draw_text("SPD", self.width // 2 - 30, y_pos,
                                font_size='small', color=Colors.TEXT_SECONDARY)
        self.renderer.draw_text(
            f"{flight.ground_speed_kts} kts",
            self.width // 2 - 30, y_pos + 20,
            font_size='medium', color=Colors.TEXT_PRIMARY
        )

        # Right column: Heading
        self.renderer.draw_text("HDG", self.width - 100, y_pos,
                                font_size='small', color=Colors.TEXT_SECONDARY)
        self.renderer.draw_text(
            f"{flight.heading:03d}°",
            self.width - 100, y_pos + 20,
            font_size='medium', color=Colors.TEXT_PRIMARY
        )

        # Aircraft type and registration
        y_pos = 265
        self.renderer.draw_line(20, y_pos, self.width - 20, y_pos,
                                color=Colors.DIVIDER, width=1)

        y_pos = 280
        # Aircraft type
        self.renderer.draw_text(
            f"Aircraft: {flight.aircraft_type}",
            30, y_pos, font_size='small', color=Colors.TEXT_SECONDARY
        )

        # Registration - highlight if on watchlist
        if flight.registration:
            reg_color = Colors.WATCHLIST if is_watched else Colors.TEXT_SECONDARY
            reg_text = f"★ {flight.registration}" if is_watched else flight.registration
            self.renderer.draw_text(
                reg_text,
                self.width - 30, y_pos,
                font_size='small', color=reg_color, anchor='rt'
            )

        # Draw airplane icon with heading - use watchlist color if watched
        icon_color = Colors.WATCHLIST if is_watched else Colors.ACCENT
        self.renderer.draw_airplane_icon(
            self.width - 50, 70,
            heading=flight.heading,
            size=40,
            color=icon_color
        )

        # Watchlist indicator banner with custom name if available
        if is_watched:
            banner_text = f"★ {watchlist_name} ★" if watchlist_name else "★ WATCHLIST ★"
            self.renderer.draw_text(
                banner_text,
                10, self.height - 8,
                font_size='small', color=Colors.WATCHLIST, anchor='lb'
            )

        # FlightRadar24 attribution
        self.renderer.draw_text(
            "flightradar24.com",
            self.width - 10, self.height - 8,
            font_size='small', color=Colors.DIVIDER, anchor='rb'
        )

        # Update display
        self.renderer.display.update()


class IdleScreen:
    """Display screen for time, date, and temperature when no flights"""

    # Number of weather info pages to cycle through
    WEATHER_PAGES = 3
    # Seconds to display each page before cycling
    PAGE_CYCLE_SECONDS = 5

    def __init__(self, renderer: DisplayRenderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height
        self.current_page = 0
        self.last_page_change = 0

    def _get_current_page(self) -> int:
        """Get current weather page based on time cycling"""
        import time
        now = time.time()
        # Change page every PAGE_CYCLE_SECONDS
        page = int(now / self.PAGE_CYCLE_SECONDS) % self.WEATHER_PAGES
        return page

    def _get_temp_color(self, temp_c: float) -> str:
        """Get color based on temperature"""
        if temp_c >= 30:
            return Colors.TEMP_HOT
        elif temp_c >= 20:
            return Colors.TEMP_WARM
        elif temp_c >= 10:
            return Colors.TEMP_MILD
        elif temp_c >= 0:
            return Colors.TEMP_COOL
        else:
            return Colors.TEMP_COLD

    def _get_wind_direction(self, degrees: int) -> str:
        """Convert wind direction degrees to compass direction"""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]

    def render(self, weather: Optional[WeatherInfo] = None,
               location_name: str = ""):
        """Render the idle screen with time, date, and weather"""
        # Clear screen
        self.renderer.display.clear(Colors.BACKGROUND)

        now = datetime.now()

        # Time (large, centered)
        time_str = now.strftime("%H:%M")
        self.renderer.draw_centered_text(
            time_str, 30,
            font_size='large', color=Colors.TEXT_PRIMARY
        )

        # Date
        date_str = now.strftime("%A, %B %d")
        self.renderer.draw_centered_text(
            date_str, 90,
            font_size='medium', color=Colors.ACCENT
        )

        # Divider
        self.renderer.draw_line(50, 125, self.width - 50, 125,
                                color=Colors.DIVIDER, width=1)

        # Weather section
        if weather:
            page = self._get_current_page()

            # Temperature (large) - always shown
            temp_color = self._get_temp_color(weather.temperature_c)
            temp_str = f"{weather.temperature_c:.1f}°C"
            self.renderer.draw_centered_text(
                temp_str, 135,
                font_size='large', color=temp_color
            )

            # Weather description - always shown
            self.renderer.draw_centered_text(
                weather.weather_description, 185,
                font_size='medium', color=Colors.TEXT_PRIMARY
            )

            # Page-specific content
            if page == 0:
                # Page 1: Feels like, humidity, wind
                feels_str = f"Feels like {weather.feels_like_c:.1f}°C"
                self.renderer.draw_centered_text(
                    feels_str, 212,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )

                wind_dir = self._get_wind_direction(weather.wind_direction)
                wind_str = f"Wind: {wind_dir} {weather.wind_speed_kmh:.0f} km/h"
                humidity_str = f"Humidity: {weather.humidity}%"

                self.renderer.draw_text(
                    wind_str, 30, 235,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )
                self.renderer.draw_text(
                    humidity_str, self.width - 30, 235,
                    font_size='small', color=Colors.TEXT_SECONDARY, anchor='rt'
                )

            elif page == 1:
                # Page 2: High/low, precipitation, pressure
                high_low_str = f"High: {weather.temp_max_c:.1f}°C  Low: {weather.temp_min_c:.1f}°C"
                self.renderer.draw_centered_text(
                    high_low_str, 212,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )

                precip_str = f"Precip: {weather.precipitation_mm:.1f} mm"
                pressure_str = f"Pressure: {weather.pressure_hpa:.0f} hPa"

                self.renderer.draw_text(
                    precip_str, 30, 235,
                    font_size='small', color=Colors.ACCENT
                )
                self.renderer.draw_text(
                    pressure_str, self.width - 30, 235,
                    font_size='small', color=Colors.TEXT_SECONDARY, anchor='rt'
                )

            elif page == 2:
                # Page 3: Wind gusts, sunrise/sunset
                wind_dir = self._get_wind_direction(weather.wind_direction)
                wind_str = f"Wind: {wind_dir} {weather.wind_speed_kmh:.0f} km/h"
                gusts_str = f"Gusts: {weather.wind_gusts_kmh:.0f} km/h"

                self.renderer.draw_text(
                    wind_str, 30, 212,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )
                self.renderer.draw_text(
                    gusts_str, self.width - 30, 212,
                    font_size='small', color=Colors.TEXT_SECONDARY, anchor='rt'
                )

                if weather.sunrise and weather.sunset:
                    sunrise_str = f"Sunrise: {weather.sunrise}"
                    sunset_str = f"Sunset: {weather.sunset}"

                    self.renderer.draw_text(
                        sunrise_str, 30, 235,
                        font_size='small', color=Colors.TEMP_WARM
                    )
                    self.renderer.draw_text(
                        sunset_str, self.width - 30, 235,
                        font_size='small', color=Colors.ACCENT, anchor='rt'
                    )

            # Location name and page indicator
            if location_name:
                loc_with_page = f"{location_name}  [{page + 1}/{self.WEATHER_PAGES}]"
                self.renderer.draw_centered_text(
                    loc_with_page, 265,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )
            else:
                self.renderer.draw_centered_text(
                    f"[{page + 1}/{self.WEATHER_PAGES}]", 265,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )
        else:
            # No weather data
            self.renderer.draw_centered_text(
                "Weather unavailable", 170,
                font_size='medium', color=Colors.TEXT_SECONDARY
            )

            if location_name:
                self.renderer.draw_centered_text(
                    location_name, 210,
                    font_size='small', color=Colors.TEXT_SECONDARY
                )

        # "Scanning for flights" indicator - at bottom with padding
        self.renderer.draw_text(
            "Scanning for flights...",
            10, self.height - 20,
            font_size='small', color=Colors.DIVIDER
        )

        # Update display
        self.renderer.display.update()


class MultiFlightScreen:
    """Display screen showing multiple nearby flights in a list"""

    def __init__(self, renderer: DisplayRenderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height

    def render(self, flights: list[FlightInfo], selected_index: int = 0):
        """Render a list of nearby flights"""
        # Clear screen
        self.renderer.display.clear(Colors.BACKGROUND)

        # Header
        self.renderer.draw_rect(0, 0, self.width, 35,
                                fill='#111111', outline=Colors.DIVIDER)
        self.renderer.draw_text(
            f"{len(flights)} Flights Nearby",
            10, 8, font_size='medium', color=Colors.TEXT_PRIMARY
        )

        # List flights (max 5 visible)
        max_visible = 5
        row_height = 55
        start_y = 45

        for i, flight in enumerate(flights[:max_visible]):
            y = start_y + (i * row_height)
            is_selected = (i == selected_index)

            # Highlight selected row
            if is_selected:
                self.renderer.draw_rect(0, y, self.width, row_height - 5,
                                        fill='#002244')

            # Flight number
            self.renderer.draw_text(
                flight.flight_number or flight.callsign,
                15, y + 5,
                font_size='medium',
                color=Colors.ACCENT if is_selected else Colors.TEXT_PRIMARY
            )

            # Route
            route = f"{flight.origin} → {flight.destination}"
            self.renderer.draw_text(
                route, 15, y + 30,
                font_size='small', color=Colors.TEXT_SECONDARY
            )

            # Distance (right side)
            self.renderer.draw_text(
                f"{flight.distance_km} km",
                self.width - 15, y + 5,
                font_size='small', color=Colors.TEXT_SECONDARY, anchor='rt'
            )

            # Altitude (right side)
            self.renderer.draw_text(
                f"{flight.altitude_ft:,} ft",
                self.width - 15, y + 30,
                font_size='small', color=self._get_altitude_color(flight.altitude_ft),
                anchor='rt'
            )

        # "Press to see details" hint
        if len(flights) > 0:
            self.renderer.draw_text(
                "Showing closest flight details",
                10, self.height - 25,
                font_size='small', color=Colors.TEXT_SECONDARY
            )

        self.renderer.display.update()

    def _get_altitude_color(self, altitude_ft: int) -> str:
        if altitude_ft > 30000:
            return Colors.ALTITUDE_HIGH
        elif altitude_ft > 10000:
            return Colors.ALTITUDE_MED
        else:
            return Colors.ALTITUDE_LOW
