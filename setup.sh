#!/bin/bash
# Flight Tracker Pi - Setup Script
# For Raspberry Pi 1 Model B with MHS 3.5" SPI Display

set -e

echo "=============================================="
echo "  Flight Tracker Pi - Setup"
echo "=============================================="

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    echo "Continuing anyway for development purposes..."
fi

# Update system packages
echo ""
echo "Updating system packages..."
sudo apt-get update

# Install system dependencies
echo ""
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-pil \
    fonts-dejavu \
    libopenjp2-7 \
    libtiff6 || sudo apt-get install -y libtiff5

# Enable SPI if not already enabled
echo ""
echo "Checking SPI configuration..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    echo "Enabling SPI..."
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    echo "SPI enabled. A reboot will be required."
fi

# Check for SPI speed override for 125MHz
if ! grep -q "spidev.bufsiz" /boot/cmdline.txt 2>/dev/null; then
    echo "Setting SPI buffer size for high-speed operation..."
    sudo sed -i 's/$/ spidev.bufsiz=65536/' /boot/cmdline.txt
fi

# Create virtual environment with system packages (uses system Pillow to avoid compilation)
echo ""
echo "Creating Python virtual environment..."
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Python dependencies one at a time to avoid memory issues
echo ""
echo "Installing Python dependencies..."
pip install --no-cache-dir --only-binary=:all: spidev || pip install --no-cache-dir spidev
pip install --no-cache-dir --only-binary=:all: RPi.GPIO || echo "RPi.GPIO may need compilation, skipping for now"
pip install --no-cache-dir requests pyyaml
# Install FlightRadarAPI without brotli dependency
pip install --no-cache-dir --no-deps FlightRadarAPI

# Create systemd service
echo ""
echo "Creating systemd service..."
sudo tee /etc/systemd/system/flight-tracker.service > /dev/null << EOF
[Unit]
Description=Flight Tracker Pi Display
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml with your location"
echo "  2. Reboot if SPI was just enabled"
echo "  3. Test with: source venv/bin/activate && python main.py --test"
echo "  4. Run normally: python main.py"
echo ""
echo "To run as a service:"
echo "  sudo systemctl enable flight-tracker"
echo "  sudo systemctl start flight-tracker"
echo ""
echo "To view logs:"
echo "  journalctl -u flight-tracker -f"
echo ""
