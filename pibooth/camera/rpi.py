# -*- coding: utf-8 -*-

import time
import pygame
import numpy as np
from io import BytesIO
from PIL import Image, ImageOps
try:
    from picamera2 import Picamera2
    from libcamera import Transform
except ImportError:
    Picamera2 = None  # picamera2 is optional
    Transform = None
from pibooth.language import get_translated_text
from pibooth.camera.base import BaseCamera


def get_rpi_camera_proxy(port=None):
    """Return camera proxy if a Raspberry Pi compatible camera is found
    else return None.

    :param port: look on given port number
    :type port: int
    """
    if not Picamera2:
        return None  # picamera2 is not installed
    try:
        # Check if cameras are available
        cameras = Picamera2.global_camera_info()
        if not cameras:
            return None
        
        # Select camera by port/index
        if port is not None and port < len(cameras):
            return Picamera2(port)
        return Picamera2()
    except Exception:
        pass
    return None


class RpiCamera(BaseCamera):

    """Camera management using Picamera2 and libcamera stack.
    """

    # Common effects that can be simulated with PIL post-processing
    IMAGE_EFFECTS = ['none', 'negative', 'solarize', 'sketch', 'denoise', 'emboss', 
                     'oilpaint', 'hatch', 'gpen', 'pastel', 'watercolor', 'film', 
                     'blur', 'saturation', 'colorswap', 'washedout', 'posterise', 
                     'colorpoint', 'colorbalance', 'cartoon', 'deinterlace1', 'deinterlace2']

    def _specific_initialization(self):
        """Camera initialization with Picamera2.
        """
        # Create preview configuration
        preview_config = self._cam.create_preview_configuration(
            main={"size": self.resolution, "format": "RGB888"},
            transform=Transform(
                hflip=self.capture_flip,
                vflip=False
            )
        )
        self._cam.configure(preview_config)
        
        # Set controls (ISO → AnalogueGain conversion: gain = iso / 100)
        preview_gain = self.preview_iso / 100.0
        controls = {
            "AnalogueGain": preview_gain,
            "AeEnable": True,  # Auto-exposure
        }
        self._cam.set_controls(controls)
        
        # Store original transform for later modifications
        self._transform = Transform(hflip=self.capture_flip, vflip=False)
        self._preview_started = False
        self._preview_surface = None
        self._last_preview_time = 0
        self._preview_fps = 15  # Target FPS for preview

    def _show_overlay(self, text, alpha):
        """Add an image as an overlay using Pygame (Picamera2 doesn't have native overlays).
        Note: The actual overlay rendering is handled by Pibooth's window system.
        We just store the overlay data here for compatibility.
        """
        if self._window:
            # Store overlay information for potential Pygame rendering
            self._overlay = {'text': str(text), 'alpha': alpha}

    def _hide_overlay(self):
        """Remove any existing overlay.
        """
        if self._overlay:
            self._overlay = None

    def _post_process_capture(self, capture_data):
        """Rework capture data.

        :param capture_data: tuple (numpy array, effect)
        :type capture_data: tuple
        """
        array, effect = capture_data
        
        # Convert numpy array to PIL Image
        image = Image.fromarray(array)
        
        # Apply effect if not 'none'
        if effect and effect != 'none':
            image = self._apply_effect(image, effect)
        
        return image
    
    def _apply_effect(self, image, effect):
        """Apply image effect using PIL post-processing.
        
        :param image: PIL Image
        :param effect: effect name
        :return: PIL Image with effect applied
        """
        effect = effect.lower()
        
        if effect == 'negative':
            return ImageOps.invert(image.convert('RGB'))
        elif effect == 'solarize':
            return ImageOps.solarize(image, threshold=128)
        elif effect == 'posterise':
            return ImageOps.posterize(image, bits=2)
        elif effect == 'colorbalance':
            return ImageOps.equalize(image)
        # Add more effects as needed
        # For unsupported effects, return original image
        return image
Captures frames and displays them in Pygame window.
        """
        if self._preview_started:
            # Already running
            return

        self._window = window
        
        # Start the camera (streaming mode)
        self._cam.start()
        self._preview_started = True
        
        # Display initial preview frame
        self._update_preview()
    
    def _update_preview(self):
        """Update the preview by capturing and displaying a frame."""
        if not self._preview_started or not self._window:
            return
        Displays live preview with countdown overlay.
        """
        timeout = int(timeout)
        if timeout < 1:
            raise ValueError("Start time shall be greater than 0")
        if not self._preview_started:
            raise EnvironmentError("Preview shall be started first")

        while timeout > 0:
            self._show_overlay(timeout, alpha)
            
            # Update preview with countdown
            start_time = time.time()
            while time.time() - start_time < 1.0:
                self._update_preview()
                time.sleep(0.033)  # ~30 FPS
            
            timeout -= 1
            self._hide_overlay()
            
            # Enable flash bef while showing live preview.
        """
        self._show_overlay(get_translated_text('smile'), alpha)
        start_time = time.time()
        while time.time() - start_time < timeout:
            self._update_preview()
            time.sleep(0.033)  # ~30 FPS
        self._show_overlay(get_translated_text('smile'), alpha)
        # Show "smile" for a brief moment with live preview
        for _ in range(10):
            self._update_preview()
            time.sleep(0.033
            image = image.resize((rect.width, rect.height), Image.LANCZOS)
            
            # Convert PIL Image to Pygame surface
            mode = image.mode
            size = image.size
            data = image.tobytes()
            
            self._preview_surface = pygame.image.fromstring(data, size, mode)
            
            # Draw on window
            surface = self._window.get_surface()
            surface.fill((0, 0, 0))  # Clear background
            surface.blit(self._preview_surface, (rect.x, rect.y))
            
            # Draw overlay if present
            if self._overlay:
                self._draw_overlay_on_surface(surface, rect)
            
            pygame.display.flip()
            
        except Exception as e:
            # Silently ignore preview errors to not block the application
            pass
    
    def _draw_overlay_on_surface(self, surface, rect):
        """Draw overlay text on pygame surface."""
        if not self._overlay:
            return
        
        text = str(self._overlay.get('text', ''))
        alpha = self._overlay.get('alpha', 255)
        
        # Create overlay surface
        overlay_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Render text
        font_size = min(rect.width, rect.height) // 3
        font = pygame.font.Font(None, font_size)
        text_surf = font.render(text, True, (255, 255, 255, alpha))
        
        # Center text
        text_rect = text_surf.get_rect(center=(rect.width // 2, rect.height // 2))
        overlay_surf.blit(text_surf, text_rect)
        
        # Draw on main surface
        surface.blit(overlay_surf, (rect.x, rect.y))
        # Start the camera (streaming mode without native preview window)
        self._cam.start()
        self._preview_started = True

    def preview_countdown(self, timeout, alpha=60, flash_led=None):
        """Show a countdown of `timeout` seconds on the preview.
        Returns when the countdown is finished.
        Note: Overlay rendering should be handled by Pibooth's window system.
        """
        timeout = int(timeout)
        if timeout < 1:
            raise ValueError("Start time shall be greater than 0")
        if not self._preview_started:
            raise EnvironmentError("Preview shall be started first")

        while timeout > 0:
            self._show_overlay(timeout, alpha)
            time.sleep(1)
            timeout -= 1
            self._hide_overlay()
            # Enable flash before taking the picture
            if timeout == 1:
                flash_led.on()

        self._show_overlay(get_translated_text('smile'), alpha)

    def preview_wait(self, timeout, alpha=60):
        """Wait the given time.
        """
        time.sleep(timeout)
        self._show_overlay(get_translated_text('smile'), alpha)

    def stop_preview(self):
        """Stop the preview.
        """
        self._hide_overlay()
        if self._preview_started:
            self._cam.stop()
            self._preview_started = False
        self._window = None

    def capture(self, effect=None):
        """Capture a new picture using Picamera2.
        """
        effect = str(effect).lower()
        if effect not in self.IMAGE_EFFECTS:
            raise ValueError("Invalid capture effect '{}' (choose among {})".format(effect, self.IMAGE_EFFECTS))

        try:
            # Adjust ISO/gain if needed for capture
            if self.capture_iso != self.preview_iso:
                capture_gain = self.capture_iso / 100.0
                self._cam.set_controls({"AnalogueGain": capture_gain})
            
            # Capture as numpy array (RGB format)
            array = self._cam.capture_array("main")
            
            # Store capture with effect for post-processing
            self._captures.append((array, effect))
            
            # Restore preview ISO/gain
            if self.capture_iso != self.preview_iso:
                preview_gain = self.preview_iso / 100.0
                self._cam.set_controls({"AnalogueGain": preview_gain})
                
        except Exception as e:
            # In case of error, ensure we restore preview settings
            if self.capture_iso != self.preview_iso:
                preview_gain = self.preview_iso / 100.0
                self._cam.set_controls({"AnalogueGain": preview_gain})
            raise e

        self._hide_overlay()  # If stop_preview() has not been called

    def quit(self):
        """Close the camera driver, it's definitive.
        """
        if self._preview_started:
            self._cam.stop()
        self._cam.close()
