# Flight Tracker Pi

A Raspberry Pi flight tracker that displays overhead aircraft information using FlightRadar24 data on an MHS 3.5" SPI display. When no flights are nearby, it shows the current time, date, and weather.

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
| LED | GPIO 18 (Pin 12) | Backlight |

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

# Display rotation (0, 90, 180, 270)
display:
  rotation: 0
```

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

### Flight Screen
When aircraft are detected nearby:
- Flight number and airline
- Route (origin → destination)
- Altitude, speed, and heading
- Distance from your location
- Climbing/descending indicator
- Aircraft type and registration

### Idle Screen
When no flights are nearby:
- Current time (with seconds)
- Date
- Outside temperature
- Weather conditions
- Location name

## APIs Used

- **FlightRadar24** - Real-time flight tracking data
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
- Open-Meteo is free but rate-limited; data updates every 10 minutes by default

## Project Structure

```
flight-tracker-pi/
├── main.py              # Application entry point
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── setup.sh             # Installation script
└── src/
    ├── display.py       # MHS 3.5" SPI display driver
    ├── flight_tracker.py# FlightRadar24 API client
    ├── weather.py       # Open-Meteo weather client
    └── ui.py            # UI screens and rendering
```

## Performance Notes

The Raspberry Pi 1 Model B has limited resources. The application is optimized for:
- Minimal CPU usage (0.5s refresh rate)
- Efficient SPI transfers at 125MHz
- Cached weather data (10-minute intervals)
- Batched flight API requests (5-second intervals)

## License

MIT License - See LICENSE file
