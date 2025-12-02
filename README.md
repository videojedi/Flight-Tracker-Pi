# Flight Tracker Pi

A Raspberry Pi flight tracker that displays overhead aircraft information using FlightRadar24 data on an MHS 3.5" SPI display. When no flights are nearby, it shows the current time, date, and weather.

## Features

- Real-time flight tracking via FlightRadar24 public API
- Weather display with multi-page cycling (Open-Meteo, no API key required)
- Touch input to cycle between multiple nearby flights
- Watchlist highlighting for specific aircraft (Red Arrows, BBMF, celebrities, etc.)
- HDMI output mirroring with automatic resolution detection
- Loading screen with IP address display
- Configurable via YAML

## Hardware Requirements

- **Raspberry Pi 1 Model B** (or newer)
- **MHS 3.5" SPI Display** (480x320, ILI9486 controller)
- Internet connection (for flight and weather data)

## Display Connection

The MHS 3.5" display connects via the GPIO header:

| Display Pin | Pi GPIO | Function |
|-------------|---------|----------|
| VCC | 3.3V (Pin 1) | Power |
| GND | GND (Pin 6) | Ground |
| CS | CE0 (Pin 24) | SPI Chip Select |
| RST | GPIO 25 (Pin 22) | Reset |
| DC | GPIO 24 (Pin 18) | Data/Command |
| SDI/MOSI | MOSI (Pin 19) | SPI Data |
| SCK | SCLK (Pin 23) | SPI Clock |
| LED | 3.3V | Backlight (always on) |

## Installation

1. Clone or copy this project to your Pi:
   ```bash
   cd ~
   git clone <repo-url> flight-tracker-pi
   cd flight-tracker-pi
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Edit the configuration:
   ```bash
   nano config.yaml
   ```

4. Reboot if SPI was just enabled:
   ```bash
   sudo reboot
   ```

## Configuration

Edit `config.yaml` to set your location and preferences:

```yaml
# Your location
location:
  latitude: 51.5074    # Your latitude
  longitude: -0.1278   # Your longitude
  name: "London"       # Display name

# Search radius for flights (km)
flight_radius_km: 50

# Flight update interval (seconds)
flight_update_interval_seconds: 15

# Display settings
display:
  width: 480
  height: 320
  mirror_hdmi: true    # Mirror display to HDMI output

# Watchlist - aircraft registrations to highlight
watchlist:
  G-ABCD: "Friend's Plane"
  XX202: "Red 1"
```

### Watchlist

The watchlist highlights specific aircraft with a magenta colour scheme when detected. Includes support for:
- Custom aircraft names/descriptions
- Case-insensitive registration matching
- Pre-configured entries for Red Arrows and BBMF aircraft

## Usage

### Test Mode
Test the display with sample data:
```bash
source venv/bin/activate
python main.py --test
```

### Normal Operation
```bash
source venv/bin/activate
python main.py
```

### Run as a Service
```bash
sudo systemctl enable flight-tracker
sudo systemctl start flight-tracker
```

View logs:
```bash
journalctl -u flight-tracker -f
```

## Display Screens

### Loading Screen
Shown during startup:
- Flight Tracker Pi logo with radar rings
- Status messages (Initializing, Fetching weather, etc.)
- IP address in bottom right corner

### Flight Screen
When aircraft are detected nearby:
- Flight number and airline
- Route (origin → destination) with city names
- Altitude, speed, and heading
- Distance from your location
- Climbing/descending indicator
- Aircraft type and registration
- Watchlist highlighting (magenta theme with custom name banner)
- Tap screen to cycle between multiple flights

### Idle Screen
When no flights are nearby (auto-cycles through 3 pages):
- **Page 1**: Time, date, temperature, feels like, wind, humidity
- **Page 2**: Temperature, high/low, precipitation, pressure
- **Page 3**: Temperature, wind gusts, sunrise/sunset times
- Location name and page indicator

## APIs Used

- **FlightRadar24** - Real-time flight tracking data (public feed, no API key required)
- **Open-Meteo** - Weather data (free, no API key required)

## Troubleshooting

### Display not working
1. Ensure SPI is enabled: `sudo raspi-config` → Interface Options → SPI
2. Check connections match the pinout table
3. Try running with `--test` flag

### No flights showing
1. Verify your coordinates in config.yaml
2. Increase the `flight_radius_km` value
3. Check internet connectivity

### Weather not updating
- Open-Meteo is free but rate-limited; data updates every 15 minutes by default

### HDMI not mirroring
1. Check `mirror_hdmi: true` in config.yaml
2. Ensure HDMI is connected before starting the application
3. The display auto-detects resolution and bit depth

## Project Structure

```
flight-tracker-pi/
├── main.py              # Application entry point
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── setup.sh             # Installation script
└── src/
    ├── display.py       # MHS 3.5" display driver + HDMI mirroring
    ├── flight_tracker.py# FlightRadar24 API client
    ├── weather.py       # Open-Meteo weather client
    ├── airports.py      # IATA airport code lookup
    ├── touch.py         # Touch input handler
    └── ui.py            # UI screens (Loading, Flight, Idle)
```

## Performance Notes

The Raspberry Pi 1 Model B has limited resources. The application is optimised for:
- Minimal CPU usage (1s refresh rate)
- Efficient SPI transfers at 125MHz
- Cached weather data (15-minute intervals)
- Batched flight API requests (15-second intervals)
- NumPy-accelerated framebuffer conversion (when available)

## License

MIT License - See LICENSE file
