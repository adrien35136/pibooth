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
        # Store configurations for later use
        self._transform = Transform(hflip=self.capture_flip, vflip=False)
        self._preview_started = False
        
        # Create LOW resolution preview configuration for speed
        self._preview_config = self._cam.create_preview_configuration(
            main={"size": (800, 600), "format": "RGB888"},
            transform=self._transform
        )
        
        # Create HIGH resolution capture configuration
        self._capture_config = self._cam.create_still_configuration(
            main={"size": self.resolution, "format": "RGB888"},
            transform=self._transform
        )
        
        # Start with preview configuration (low res)
        self._cam.configure(self._preview_config)
        
        # Set controls (ISO → AnalogueGain conversion: gain = iso / 100)
        preview_gain = self.preview_iso / 100.0
        controls = {
            "AnalogueGain": preview_gain,
            "AeEnable": True,  # Auto-exposure
            "AwbEnable": True,  # Auto white balance
            "AwbMode": 0,  # Auto white balance mode
            "Sharpness": 1.5,  # Increase sharpness for better image quality
            "Contrast": 1.1,  # Slight contrast boost
            "Saturation": 1.0,  # Normal saturation
            "Brightness": 0.0,  # Normal brightness
            "ExposureTime": 0,  # Auto (will be controlled by AeEnable)
            "NoiseReductionMode": 1,  # High quality noise reduction
        }
        self._cam.set_controls(controls)

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

    def preview(self, window, flip=True):
        """Setup the preview.
        """
        self._window = window
        self.preview_flip = flip
        
        # Start the camera (streaming mode)
        if not self._preview_started:
            self._cam.start()
            self._preview_started = True
        
        # Show initial preview frame
        self._window.show_image(self._get_preview_image())
    
    def _get_preview_image(self):
        """Capture and return a PIL preview image resized to fit preview area."""
        if not self._preview_started:
            return None
        
        try:
            # Capture preview frame as numpy array
            array = self._cam.capture_array("main")
            
            # Convert numpy array to PIL Image
            image = Image.fromarray(array)
            
            # Get the preview rectangle from Pibooth to know target size
            rect = self.get_rect()
            
            # Resize to fit preview area while keeping aspect ratio
            from pibooth.pictures import sizing
            new_size = sizing.new_size_keep_aspect_ratio(image.size, (rect.width, rect.height))
            image = image.resize(new_size, Image.LANCZOS)
            
            return image
            
        except Exception as e:
            LOGGER.warning(f"Preview capture error: {e}")
            return None
    
    def preview_countdown(self, timeout, alpha=60, flash_led=None):
        """Show a countdown of timeout seconds on the preview.
        Returns when the countdown is finished.
        """
        timeout = int(timeout)
        if timeout < 1:
            raise ValueError("Start time shall be greater than 0")
        if not self._preview_started:
            raise EnvironmentError("Preview shall be started first")

        while timeout > 0:
            self._show_overlay(timeout, alpha)
            
            # Update preview with countdown (show multiple frames during 1 second)
            start_time = time.time()
            while time.time() - start_time < 1.0:
                updated_rect = self._window.show_image(self._get_preview_image())
                pygame.event.pump()
                if updated_rect:
                    pygame.display.update(updated_rect)
                time.sleep(0.05)  # ~20 FPS
            
            timeout -= 1
            self._hide_overlay()
            
            # Enable flash before taking the picture
            if timeout == 1:
                flash_led.on()

        self._show_overlay(get_translated_text('smile'), alpha)
        # Show smile with live preview
        for _ in range(10):
            updated_rect = self._window.show_image(self._get_preview_image())
            pygame.event.pump()
            if updated_rect:
                pygame.display.update(updated_rect)
            time.sleep(0.05)

    def preview_wait(self, timeout, alpha=60):
        """Wait the given time while showing live preview.
        """
        self._show_overlay(get_translated_text('smile'), alpha)
        start_time = time.time()
        while time.time() - start_time < timeout:
            updated_rect = self._window.show_image(self._get_preview_image())
            pygame.event.pump()
            if updated_rect:
                pygame.display.update(updated_rect)
            time.sleep(0.05)  # ~20 FPS

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
            # Switch to high-resolution capture configuration
            if self._preview_started:
                self._cam.stop()
            self._cam.configure(self._capture_config)
            self._cam.start()
            
            # Adjust ISO/gain and quality settings for capture
            capture_gain = self.capture_iso / 100.0
            self._cam.set_controls({
                "AnalogueGain": capture_gain,
                "AeEnable": True,
                "AwbEnable": True,
                "AwbMode": 0,
                "Sharpness": 1.5,
                "Contrast": 1.1,
                "Saturation": 1.0,
                "Brightness": 0.0,
                "NoiseReductionMode": 2,  # Maximum quality for capture
            })
            
            # Brief pause to let camera adjust and stabilize
            time.sleep(0.3)
            
            # Capture as numpy array (RGB format)
            array = self._cam.capture_array("main")
            
            # Store capture with effect for post-processing
            self._captures.append((array, effect))
            
            # Switch back to low-resolution preview configuration
            self._cam.stop()
            self._cam.configure(self._preview_config)
            if self._preview_started:
                self._cam.start()
            
            # Restore preview ISO/gain and quality settings
            preview_gain = self.preview_iso / 100.0
            self._cam.set_controls({
                "AnalogueGain": preview_gain,
                "AeEnable": True,
                "AwbEnable": True,
                "AwbMode": 0,
                "Sharpness": 1.5,
                "Contrast": 1.1,
                "Saturation": 1.0,
                "Brightness": 0.0,
                "NoiseReductionMode": 1,
            })
                
        except Exception as e:
            # In case of error, ensure we restore preview settings
            try:
                self._cam.stop()
                self._cam.configure(self._preview_config)
                if self._preview_started:
                    self._cam.start()
                preview_gain = self.preview_iso / 100.0
                self._cam.set_controls({
                    "AnalogueGain": preview_gain,
                    "AeEnable": True,
                    "AwbEnable": True,
                    "AwbMode": 0,
                    "Sharpness": 1.5,
                    "Contrast": 1.1,
                    "Saturation": 1.0,
                    "Brightness": 0.0,
                    "NoiseReductionMode": 1,
                })
            except:
                pass
            raise e

        self._hide_overlay()  # If stop_preview() has not been called

    def quit(self):
        """Close the camera driver, it's definitive.
        """
        if self._preview_started:
            self._cam.stop()
        self._cam.close()
