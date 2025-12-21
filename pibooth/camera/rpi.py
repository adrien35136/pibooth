# -*- coding: utf-8 -*-

import time
import pygame
import numpy as np
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw
try:
    import cv2
except ImportError:
    cv2 = None
try:
    from picamera2 import Picamera2
    from libcamera import Transform
except ImportError:
    Picamera2 = None  # picamera2 is optional
    Transform = None
from pibooth.utils import LOGGER
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
        self._overlay_cache = {}  # Cache for countdown overlays
        self._overlay = None  # Current overlay image
        
        # Create configuration with dual streams:
        # - main: medium resolution RGB for quality preview
        # - lores: not used but required by Picamera2
        # Using 1280x960 (native 4:3 ratio) for optimal balance between quality and performance
        preview_resolution = (1280, 960)
        self._preview_config = self._cam.create_video_configuration(
            main={"size": preview_resolution, "format": "RGB888"},
            lores={"size": (640, 480), "format": "YUV420"},
            transform=self._transform,
            controls={
                "FrameRate": 30.0,  # Force 30 FPS for smooth preview
            }
        )
        
        # Start with preview configuration
        self._cam.configure(self._preview_config)
        
        # Démarrer la caméra immédiatement pour le warmup AWB
        self._cam.start()
        
        # Laisser AWB et AE se stabiliser (crucial pour Picamera2)
        time.sleep(2.0)
        
        # Après stabilisation, appliquer les contrôles optimisés
        # ISO 1600 peut être trop élevé pour le preview, utiliser une valeur plus faible
        preview_gain = min(self.preview_iso / 100.0, 8.0)  # Cap à 8.0 (ISO 800) pour le preview
        controls = {
            "AnalogueGain": preview_gain,
            "Sharpness": 1.5,  # Améliorer la netteté du preview
        }
        self._cam.set_controls(controls)
        
        # Arrêter pour reconfigurer proprement au moment du preview()
        self._cam.stop()

    def _create_overlay_image(self, size, text, alpha):
        """Create overlay image with text (helper method).
        """
        from pibooth import fonts
        
        # Create transparent overlay
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Doubled font size (2x the original annotate_text_size)
        font = fonts.get_pil_font(str(text), fonts.CURRENT, 
                                 size[0] * 0.6, size[1] * 0.3)
        bbox = font.getbbox(str(text))
        txt_width = bbox[2] - bbox[0]
        txt_height = bbox[3] - bbox[1]
        
        # Center horizontally and vertically
        position = ((size[0] - txt_width) // 2, (size[1] - txt_height) // 2)
        draw.text(position, str(text), (255, 255, 255, alpha), font=font)
        
        return image
    
    def _show_overlay(self, text, alpha):
        """Show overlay using cache if available, create cache on first call.
        """
        if self._window:
            text_str = str(text)
            rect = self.get_rect()
            
            # Create cache on first call with the configured alpha
            if not self._overlay_cache:
                for num in range(1, 6):
                    self._overlay_cache[num] = self._create_overlay_image(rect.size, str(num), alpha)
                smile_text = get_translated_text('smile')
                self._overlay_cache['smile'] = self._create_overlay_image(rect.size, smile_text, alpha)
            
            # Use cached overlay if available
            if text_str.isdigit() and int(text_str) in self._overlay_cache:
                self._overlay = self._overlay_cache[int(text_str)]
            elif text_str == get_translated_text('smile') and 'smile' in self._overlay_cache:
                self._overlay = self._overlay_cache['smile']
            else:
                # Fallback: create overlay on-the-fly
                self._overlay = self._create_overlay_image(rect.size, text_str, alpha)

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
        
        # Update transform with preview flip setting
        self._transform = Transform(hflip=flip, vflip=False)
        self._preview_config["transform"] = self._transform
        self._cam.configure(self._preview_config)
        
        # Start the camera (streaming mode)
        if not self._preview_started:
            self._cam.start()
            self._preview_started = True
            
            # Brief warmup après le démarrage
            time.sleep(1.0)
        
        # Show initial preview frame
        self._window.show_image(self._get_preview_image())
    
    def _get_preview_image(self):
        """Capture and return a PIL preview image from main stream."""
        if not self._preview_started:
            return None
        
        try:
            # Capture request and use main stream (RGB888)
            request = self._cam.capture_request()
            try:
                # Get RGB image from main stream
                image = request.make_image("main")
                
                # Get the preview rectangle from Pibooth to know target size
                rect = self.get_rect()
                
                # Resize to fit preview area while keeping aspect ratio
                # Use BILINEAR for better balance between quality and speed (faster than LANCZOS)
                from pibooth.pictures import sizing
                new_size = sizing.new_size_keep_aspect_ratio(image.size, (rect.width, rect.height))
                image = image.resize(new_size, Image.BILINEAR)
                
                return image
            finally:
                request.release()
            
        except Exception as e:
            LOGGER.warning(f"Preview capture error: {e}")
            import traceback
            traceback.print_exc()
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
            # Create overlay only once per second (not every frame)
            self._show_overlay(timeout, alpha)
            overlay_img = self._overlay
            
            # Pre-compute: get sample preview size and resize overlay once
            sample_img = self._get_preview_image()
            if sample_img and overlay_img:
                # Resize overlay once per second (not every frame)
                overlay_resized = overlay_img.resize(sample_img.size, Image.NEAREST)  # NEAREST is fastest
                # Pre-convert preview to RGBA once (reuse for composite)
                sample_rgba = sample_img.convert('RGBA')
            else:
                overlay_resized = None
                sample_rgba = None
            
            # Update preview with countdown (show multiple frames during 1 second)
            start_time = time.time()
            frame_count = 0
            while time.time() - start_time < 1.0:
                preview_img = self._get_preview_image()
                if preview_img and overlay_resized:
                    # Fast composite: convert preview to RGBA, alpha_composite, convert back to RGB
                    preview_rgba = preview_img.convert('RGBA')
                    preview_rgba.alpha_composite(overlay_resized, (0, 0))
                    preview_img = preview_rgba.convert('RGB')
                
                updated_rect = self._window.show_image(preview_img)
                pygame.event.pump()
                if updated_rect:
                    pygame.display.update(updated_rect)
                frame_count += 1
            
            timeout -= 1
            self._hide_overlay()
            
            # Enable flash before taking the picture
            if timeout == 1:
                flash_led.on()

        # Create smile overlay once, reuse for all frames
        self._show_overlay(get_translated_text('smile'), alpha)
        smile_img = self._overlay
        
        # Pre-resize smile overlay once
        sample_img = self._get_preview_image()
        if smile_img and sample_img:
            smile_resized = smile_img.resize(sample_img.size, Image.NEAREST)
        else:
            smile_resized = None
        
        # Show smile with live preview (optimized compositing)
        for _ in range(5):
            preview_img = self._get_preview_image()
            if preview_img and smile_resized:
                # Fast composite: in-place alpha_composite
                preview_rgba = preview_img.convert('RGBA')
                preview_rgba.alpha_composite(smile_resized, (0, 0))
                preview_img = preview_rgba.convert('RGB')
            
            updated_rect = self._window.show_image(preview_img)
            pygame.event.pump()
            if updated_rect:
                pygame.display.update(updated_rect)
            time.sleep(0.05)  # Small delay to see "smile" message

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
            # Adjust ISO/gain for capture if needed
            if self.capture_iso != self.preview_iso:
                capture_gain = self.capture_iso / 100.0
                self._cam.set_controls({"AnalogueGain": capture_gain})
                time.sleep(0.3)  # Brief pause for adjustment
            
            # Capture from MAIN stream (high resolution)
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
