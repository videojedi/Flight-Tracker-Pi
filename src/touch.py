"""
Touch input handler for MHS 3.5" Display
Reads touch events from /dev/input/eventX
"""

import os
import struct
import select
import threading


class TouchHandler:
    """Handle touch input from the display"""

    # Input event format: timestamp (8 bytes), type (2), code (2), value (4)
    EVENT_FORMAT = 'llHHi'
    EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

    # Event types
    EV_SYN = 0x00
    EV_KEY = 0x01
    EV_ABS = 0x03

    # Touch codes
    ABS_X = 0x00
    ABS_Y = 0x01
    ABS_PRESSURE = 0x18
    BTN_TOUCH = 0x14a

    def __init__(self, device_path=None, callback=None):
        self.callback = callback
        self.device_path = device_path or self._find_touch_device()
        self.running = False
        self.thread = None
        self.touch_x = 0
        self.touch_y = 0
        self.touching = False

    def _find_touch_device(self):
        """Find the touch input device"""
        input_dir = '/dev/input'
        if not os.path.exists(input_dir):
            return None

        # Look for event devices
        for name in os.listdir(input_dir):
            if name.startswith('event'):
                path = os.path.join(input_dir, name)
                # Try to identify touch device by checking capabilities
                try:
                    # Check if device name contains 'touch' or 'ads7846'
                    with open(f'/sys/class/input/{name}/device/name', 'r') as f:
                        device_name = f.read().strip().lower()
                        if 'touch' in device_name or 'ads7846' in device_name:
                            return path
                except (IOError, OSError):
                    pass

        # Fallback: try common touch device paths
        for path in ['/dev/input/event0', '/dev/input/event1', '/dev/input/touchscreen']:
            if os.path.exists(path):
                return path

        return None

    def start(self):
        """Start listening for touch events in background thread"""
        if not self.device_path or not os.path.exists(self.device_path):
            print(f"Touch device not found: {self.device_path}")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._read_events, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        """Stop listening for touch events"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _read_events(self):
        """Read touch events in a loop"""
        try:
            with open(self.device_path, 'rb') as device:
                while self.running:
                    # Use select to avoid blocking forever
                    r, _, _ = select.select([device], [], [], 0.5)
                    if not r:
                        continue

                    event_data = device.read(self.EVENT_SIZE)
                    if not event_data:
                        continue

                    # Unpack event
                    _, _, ev_type, ev_code, ev_value = struct.unpack(
                        self.EVENT_FORMAT, event_data
                    )

                    # Process event
                    if ev_type == self.EV_ABS:
                        if ev_code == self.ABS_X:
                            self.touch_x = ev_value
                        elif ev_code == self.ABS_Y:
                            self.touch_y = ev_value
                    elif ev_type == self.EV_KEY and ev_code == self.BTN_TOUCH:
                        if ev_value == 1:  # Touch down
                            self.touching = True
                        elif ev_value == 0:  # Touch up
                            if self.touching and self.callback:
                                # Call callback with touch coordinates
                                self.callback(self.touch_x, self.touch_y)
                            self.touching = False
                    elif ev_type == self.EV_SYN:
                        # Sync event - touch sequence complete
                        pass

        except (IOError, OSError) as e:
            print(f"Touch input error: {e}")
        except Exception as e:
            print(f"Touch handler error: {e}")


class SimpleTouchDetector:
    """Simple touch detector that just detects any tap"""

    def __init__(self, callback=None):
        self.callback = callback
        self.handler = TouchHandler(callback=self._on_touch)
        self.last_tap_time = 0
        self.debounce_ms = 300  # Minimum ms between taps

    def _on_touch(self, x, y):
        """Handle touch event with debouncing"""
        import time
        now = time.time() * 1000
        if now - self.last_tap_time > self.debounce_ms:
            self.last_tap_time = now
            if self.callback:
                self.callback()

    def start(self):
        """Start touch detection"""
        return self.handler.start()

    def stop(self):
        """Stop touch detection"""
        self.handler.stop()
