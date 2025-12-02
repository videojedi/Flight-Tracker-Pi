#!/usr/bin/env python3
"""
Flight Tracker Pi - Main Application
Displays overhead flight information on MHS 3.5" SPI display
Falls back to time/date/temperature when no flights nearby
"""

import sys
import time
import signal
import yaml
from pathlib import Path

from src.display import MHS35Display, DisplayRenderer
from src.flight_tracker import FlightTracker
from src.weather import WeatherClient
from src.ui import FlightScreen, IdleScreen, LoadingScreen
from src.touch import SimpleTouchDetector


class FlightTrackerApp:
    """Main application class for Flight Tracker Pi"""

    def __init__(self, config_path: str = 'config.yaml'):
        self.running = True
        self.config = self._load_config(config_path)

        # Initialize display
        display_config = self.config.get('display', {})
        self.display = MHS35Display(
            width=display_config.get('width', 480),
            height=display_config.get('height', 320),
            mirror_hdmi=display_config.get('mirror_hdmi', True)
        )
        self.renderer = DisplayRenderer(self.display)

        # Initialize UI screens
        self.loading_screen = LoadingScreen(self.renderer)
        self.flight_screen = FlightScreen(self.renderer)
        self.idle_screen = IdleScreen(self.renderer)

        # Initialize flight tracker
        location = self.config.get('location', {})
        self.latitude = location.get('latitude', 51.5074)
        self.longitude = location.get('longitude', -0.1278)
        self.location_name = location.get('name', '')

        self.flight_tracker = FlightTracker(
            latitude=self.latitude,
            longitude=self.longitude,
            radius_km=self.config.get('flight_radius_km', 50)
        )

        # Initialize weather client
        weather_config = self.config.get('weather', {})
        self.weather_client = WeatherClient(
            latitude=self.latitude,
            longitude=self.longitude,
            cache_duration_seconds=weather_config.get('update_interval_seconds', 600)
        )

        # Timing
        self.flight_update_interval = self.config.get(
            'flight_update_interval_seconds', 5
        )
        self.last_flight_check = 0
        self.current_flights = []

        # Watchlist for highlighting specific aircraft
        self.watchlist = self.config.get('watchlist', [])

        # Flight cycling
        self.selected_flight_index = 0
        self.touch_handler = SimpleTouchDetector(callback=self._on_tap)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Config file not found: {config_path}")
            print("Using default configuration")
            return {}

        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return {}

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\nShutting down...")
        self.running = False

    def _on_tap(self):
        """Handle screen tap - cycle to next flight"""
        if len(self.current_flights) > 1:
            self.selected_flight_index = (self.selected_flight_index + 1) % len(self.current_flights)
            print(f"\n[TAP] Showing flight {self.selected_flight_index + 1}/{len(self.current_flights)}")

    def _check_flights(self) -> bool:
        """Check for nearby flights, return True if flights found"""
        now = time.time()

        # Only check if enough time has passed
        if now - self.last_flight_check < self.flight_update_interval:
            return len(self.current_flights) > 0

        self.last_flight_check = now

        try:
            new_flights = self.flight_tracker.get_nearby_flights()
            # Reset index if flight list changed significantly
            if len(new_flights) != len(self.current_flights):
                self.selected_flight_index = 0
            # Keep index in bounds
            if self.selected_flight_index >= len(new_flights):
                self.selected_flight_index = 0
            self.current_flights = new_flights
            return len(self.current_flights) > 0
        except Exception as e:
            print(f"Error checking flights: {e}")
            return len(self.current_flights) > 0

    def _show_flight(self):
        """Display the selected flight"""
        if not self.current_flights:
            return

        selected_flight = self.current_flights[self.selected_flight_index]
        self.flight_screen.render(
            flight=selected_flight,
            flight_count=len(self.current_flights),
            flight_index=self.selected_flight_index,
            radius_km=self.config.get('flight_radius_km', 50),
            watchlist=self.watchlist
        )

    def _show_idle(self):
        """Display the idle screen with time and weather"""
        weather = self.weather_client.get_weather()
        self.idle_screen.render(
            weather=weather,
            location_name=self.location_name
        )

    def run(self):
        """Main application loop"""
        print("=" * 50)
        print("  Flight Tracker Pi")
        print("=" * 50)
        print(f"Location: {self.location_name}")
        print(f"  Lat: {self.latitude}, Lon: {self.longitude}")
        print(f"Search radius: {self.config.get('flight_radius_km', 50)} km")
        print(f"Update interval: {self.flight_update_interval} seconds")
        print("=" * 50)
        print("Starting... (Press Ctrl+C to exit)")
        print()

        # Show loading screen
        self.loading_screen.render("Initializing...")

        # Start touch handler
        if self.touch_handler.start():
            print("Touch input enabled - tap to cycle flights")
        else:
            print("Touch input not available")
        print()

        # Update loading status and fetch weather
        self.loading_screen.render("Fetching weather...")
        print("Fetching weather data...")
        weather = self.weather_client.get_weather()
        if weather:
            print(f"Current temperature: {weather.temperature_c}°C")
            print(f"Conditions: {weather.weather_description}")
        else:
            print("Weather data unavailable")
        print()

        # Brief pause on loading screen before starting
        self.loading_screen.render("Scanning for flights...")
        time.sleep(1)

        while self.running:
            try:
                # Check for flights
                has_flights = self._check_flights()

                if has_flights:
                    # Show flight information
                    self._show_flight()
                    selected = self.current_flights[self.selected_flight_index]
                    print(f"\r[{time.strftime('%H:%M:%S')}] "
                          f"Flight {self.selected_flight_index + 1}/{len(self.current_flights)} - "
                          f"{selected.flight_number} "
                          f"at {selected.distance_km} km     ", end='')
                else:
                    # Show idle screen with time and weather
                    self._show_idle()
                    print(f"\r[{time.strftime('%H:%M:%S')}] "
                          f"No flights nearby - showing clock    ", end='')

                # Small delay to prevent CPU overuse on Pi 1
                # Update once per second (no seconds display)
                time.sleep(1)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError in main loop: {e}")
                time.sleep(1)

        # Cleanup
        print("\nCleaning up...")
        self.touch_handler.stop()
        self.display.clear('black')
        self.display.update()
        self.display.cleanup()
        print("Goodbye!")

    def test_display(self):
        """Test the display with sample data"""
        from src.flight_tracker import FlightInfo

        print("Testing display...")

        # Create sample flight
        sample_flight = FlightInfo(
            flight_number="BA123",
            callsign="BAW123",
            aircraft_type="A320",
            airline="British Airways",
            origin="LHR",
            destination="CDG",
            altitude_ft=35000,
            ground_speed_kts=450,
            heading=135,
            latitude=self.latitude + 0.1,
            longitude=self.longitude + 0.1,
            vertical_speed=0,
            distance_km=12.5,
            registration="G-EUPT",
            squawk="1234"
        )

        print("Showing flight screen for 5 seconds...")
        self.flight_screen.render(sample_flight, flight_count=3)
        time.sleep(5)

        print("Showing idle screen for 5 seconds...")
        weather = self.weather_client.get_weather()
        self.idle_screen.render(weather, self.location_name)
        time.sleep(5)

        print("Test complete!")
        self.display.cleanup()


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Flight Tracker Pi - Track overhead flights'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run display test with sample data'
    )

    args = parser.parse_args()

    app = FlightTrackerApp(config_path=args.config)

    if args.test:
        app.test_display()
    else:
        app.run()


if __name__ == '__main__':
    main()
