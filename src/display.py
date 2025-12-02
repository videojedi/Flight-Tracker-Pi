"""
MHS 3.5" Display Driver for Raspberry Pi
Uses Linux framebuffer (/dev/fb1) with piscreen overlay
480x320 resolution, RGB565 color format
Also mirrors to HDMI output (/dev/fb0) if available
"""

import os
import struct
from PIL import Image, ImageDraw, ImageFont

# Try to import numpy for faster RGB565 conversion
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Check for framebuffers
FB_LCD = '/dev/fb1'
FB_HDMI = '/dev/fb0'
LCD_AVAILABLE = os.path.exists(FB_LCD)
HDMI_AVAILABLE = os.path.exists(FB_HDMI)

if not LCD_AVAILABLE:
    print(f"Warning: {FB_LCD} not available. Running in simulation mode.")
if HDMI_AVAILABLE:
    print(f"HDMI output ({FB_HDMI}) detected - will mirror display")


class MHS35Display:
    """Driver for MHS 3.5" LCD Display using Linux framebuffer"""

    def __init__(self, width=480, height=320, fb_device='/dev/fb1', mirror_hdmi=True, **kwargs):
        self.width = width
        self.height = height
        self.fb_device = fb_device
        self.mirror_hdmi = mirror_hdmi and HDMI_AVAILABLE

        # Frame buffer as PIL Image (RGB mode for easy drawing)
        self.buffer = Image.new('RGB', (width, height), 'black')
        self.draw = ImageDraw.Draw(self.buffer)

        # Get HDMI framebuffer info if mirroring
        self.hdmi_width = None
        self.hdmi_height = None
        self.hdmi_bpp = None
        if self.mirror_hdmi:
            self._detect_hdmi_resolution()
            self._hide_cursor()

    def _hide_cursor(self):
        """Hide the console cursor on HDMI output"""
        try:
            # Method 1: Write escape sequence to hide cursor
            with open('/dev/tty1', 'w') as tty:
                tty.write('\033[?25l')  # Hide cursor
                tty.write('\033[?1c')   # Set cursor to invisible
                tty.flush()
        except (IOError, OSError):
            pass

        try:
            # Method 2: Use setterm via /dev/tty0
            with open('/dev/tty0', 'w') as tty:
                tty.write('\033[?25l')
                tty.flush()
        except (IOError, OSError):
            pass

        try:
            # Method 3: Disable cursor blinking via sysfs
            with open('/sys/class/graphics/fbcon/cursor_blink', 'w') as f:
                f.write('0')
        except (IOError, OSError):
            pass

    def _detect_hdmi_resolution(self):
        """Detect HDMI framebuffer resolution and bit depth"""
        try:
            # Try to read from fbset or sysfs
            fb_path = '/sys/class/graphics/fb0'

            # Read virtual size
            with open(f'{fb_path}/virtual_size', 'r') as f:
                size = f.read().strip().split(',')
                self.hdmi_width = int(size[0])
                self.hdmi_height = int(size[1])

            # Read bits per pixel
            with open(f'{fb_path}/bits_per_pixel', 'r') as f:
                self.hdmi_bpp = int(f.read().strip())

            print(f"HDMI resolution: {self.hdmi_width}x{self.hdmi_height} @ {self.hdmi_bpp}bpp")
        except (IOError, OSError, ValueError) as e:
            # Fallback to common defaults
            print(f"Could not detect HDMI resolution: {e}")
            print("Using default 1920x1080 @ 32bpp")
            self.hdmi_width = 1920
            self.hdmi_height = 1080
            self.hdmi_bpp = 32

    def _convert_for_hdmi(self, image):
        """Convert and scale image for HDMI framebuffer"""
        if not self.hdmi_width or not self.hdmi_height:
            return None

        # Scale image to fit HDMI while maintaining aspect ratio
        # Center the scaled image on the HDMI display
        scale_x = self.hdmi_width / self.width
        scale_y = self.hdmi_height / self.height
        scale = min(scale_x, scale_y)

        new_width = int(self.width * scale)
        new_height = int(self.height * scale)

        # Resize with high quality
        scaled = image.resize((new_width, new_height), Image.LANCZOS)

        # Create full HDMI frame with black background
        hdmi_frame = Image.new('RGB', (self.hdmi_width, self.hdmi_height), 'black')

        # Center the scaled image
        x_offset = (self.hdmi_width - new_width) // 2
        y_offset = (self.hdmi_height - new_height) // 2
        hdmi_frame.paste(scaled, (x_offset, y_offset))

        # Convert to appropriate format based on bit depth
        if self.hdmi_bpp == 32:
            # BGRA format (common for 32bpp framebuffers)
            if HAS_NUMPY:
                arr = np.array(hdmi_frame)
                # RGB to BGRA
                bgra = np.zeros((self.hdmi_height, self.hdmi_width, 4), dtype=np.uint8)
                bgra[:, :, 0] = arr[:, :, 2]  # B
                bgra[:, :, 1] = arr[:, :, 1]  # G
                bgra[:, :, 2] = arr[:, :, 0]  # R
                bgra[:, :, 3] = 255           # A
                return bgra.tobytes()
            else:
                # Slow fallback
                pixels = hdmi_frame.load()
                data = bytearray(self.hdmi_width * self.hdmi_height * 4)
                idx = 0
                for y in range(self.hdmi_height):
                    for x in range(self.hdmi_width):
                        r, g, b = pixels[x, y]
                        data[idx] = b      # B
                        data[idx+1] = g    # G
                        data[idx+2] = r    # R
                        data[idx+3] = 255  # A
                        idx += 4
                return bytes(data)
        elif self.hdmi_bpp == 16:
            # RGB565 format
            return self._convert_to_rgb565(hdmi_frame)
        else:
            # 24bpp RGB
            return hdmi_frame.tobytes()

    def _rgb_to_565(self, r, g, b):
        """Convert RGB888 to RGB565"""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    def _convert_to_rgb565(self, image):
        """Convert PIL RGB image to RGB565 bytes for framebuffer"""
        if HAS_NUMPY:
            # Fast numpy-based conversion
            arr = np.array(image)
            r = (arr[:, :, 0] & 0xF8).astype(np.uint16) << 8
            g = (arr[:, :, 1] & 0xFC).astype(np.uint16) << 3
            b = (arr[:, :, 2] >> 3).astype(np.uint16)
            rgb565 = r | g | b
            return rgb565.astype('<u2').tobytes()
        else:
            # Fallback: slow Python loop
            pixels = image.load()
            data = bytearray(self.width * self.height * 2)
            idx = 0
            for y in range(self.height):
                for x in range(self.width):
                    r, g, b = pixels[x, y]
                    color = self._rgb_to_565(r, g, b)
                    data[idx] = color & 0xFF
                    data[idx + 1] = (color >> 8) & 0xFF
                    idx += 2
            return bytes(data)

    def clear(self, color='black'):
        """Clear the display with a solid color"""
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)

    def update(self):
        """Push the frame buffer to the display(s)"""
        if not os.path.exists(self.fb_device):
            # Simulation mode - save to file
            self.buffer.save('/tmp/display_preview.png')
        else:
            # Write to LCD framebuffer
            data = self._convert_to_rgb565(self.buffer)
            with open(self.fb_device, 'wb') as fb:
                fb.write(data)

        # Mirror to HDMI if enabled
        if self.mirror_hdmi and os.path.exists(FB_HDMI):
            try:
                hdmi_data = self._convert_for_hdmi(self.buffer)
                if hdmi_data:
                    with open(FB_HDMI, 'wb') as fb:
                        fb.write(hdmi_data)
            except (IOError, OSError) as e:
                # Silently fail HDMI mirroring - don't spam errors
                pass

    def get_draw(self):
        """Get the ImageDraw object for drawing operations"""
        return self.draw

    def get_buffer(self):
        """Get the PIL Image buffer"""
        return self.buffer

    def cleanup(self):
        """Cleanup resources"""
        # Clear screen on exit
        self.clear('black')
        self.update()


class DisplayRenderer:
    """High-level rendering utilities for the display"""

    def __init__(self, display):
        self.display = display
        self.draw = display.get_draw()
        self.width = display.width
        self.height = display.height

        # Try to load fonts
        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """Load fonts with fallbacks"""
        fonts = {}
        sizes = {'large': 48, 'medium': 24, 'small': 16}

        # Try common font paths on Raspberry Pi
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
        ]

        font_path = None
        for path in font_paths:
            try:
                ImageFont.truetype(path, 12)
                font_path = path
                break
            except (IOError, OSError):
                continue

        for name, size in sizes.items():
            try:
                if font_path:
                    fonts[name] = ImageFont.truetype(font_path, size)
                else:
                    fonts[name] = ImageFont.load_default()
            except (IOError, OSError):
                fonts[name] = ImageFont.load_default()

        return fonts

    def draw_text(self, text, x, y, font_size='medium', color='white', anchor='lt'):
        """Draw text at position with specified font size"""
        font = self.fonts.get(font_size, self.fonts['medium'])
        self.draw.text((x, y), text, font=font, fill=color, anchor=anchor)

    def draw_centered_text(self, text, y, font_size='medium', color='white'):
        """Draw horizontally centered text"""
        font = self.fonts.get(font_size, self.fonts['medium'])
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        self.draw.text((x, y), text, font=font, fill=color)

    def draw_rect(self, x, y, width, height, fill=None, outline=None, width_line=1):
        """Draw a rectangle"""
        self.draw.rectangle(
            [x, y, x + width, y + height],
            fill=fill,
            outline=outline,
            width=width_line
        )

    def draw_line(self, x1, y1, x2, y2, color='white', width=1):
        """Draw a line"""
        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def draw_airplane_icon(self, x, y, heading=0, size=30, color='white'):
        """Draw a simple airplane icon rotated to heading"""
        from PIL import Image as PILImage

        # Create airplane shape
        airplane = PILImage.new('RGBA', (size, size), (0, 0, 0, 0))
        airplane_draw = ImageDraw.Draw(airplane)

        # Simple airplane shape (pointing up)
        center = size // 2
        # Fuselage
        airplane_draw.polygon([
            (center, 2),
            (center - 3, size - 5),
            (center + 3, size - 5),
        ], fill=color)
        # Wings
        airplane_draw.polygon([
            (center, center - 3),
            (2, center + 5),
            (size - 2, center + 5),
        ], fill=color)
        # Tail wing
        airplane_draw.polygon([
            (center, size - 8),
            (center - 6, size - 3),
            (center + 6, size - 3),
        ], fill=color)

        # Rotate to heading
        rotated = airplane.rotate(-heading, center=(center, center), resample=PILImage.BICUBIC)

        # Paste onto display buffer
        self.display.get_buffer().paste(rotated, (x - center, y - center), rotated)
