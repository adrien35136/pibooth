# -*- coding: utf-8 -*-

import time
import pygame
import traceback
from PIL import Image, ImageOps, ImageDraw
from picamera2 import Picamera2
from libcamera import Transform
from pibooth.utils import LOGGER
from pibooth.language import get_translated_text
from pibooth.camera.base import BaseCamera
from pibooth import fonts
from pibooth.pictures import sizing
import numpy as np

def get_rpi_camera_proxy(port=None):
    """Return camera proxy if a Raspberry Pi compatible camera is found
    else return None.
    """
    if not Picamera2:
        return None
    try:
        cameras = Picamera2.global_camera_info()
        if not cameras:
            return None
        if port is not None and port < len(cameras):
            return Picamera2(port)
        return Picamera2()
    except Exception:
        pass
    return None


class RpiCamera(BaseCamera):
    """Camera management using Picamera2 and libcamera stack."""

    IMAGE_EFFECTS = ['none', 'negative', 'solarize', 'sketch', 'denoise', 'emboss', 
                     'oilpaint', 'hatch', 'gpen', 'pastel', 'watercolor', 'film', 
                     'blur', 'saturation', 'colorswap', 'washedout', 'posterise', 
                     'colorpoint', 'colorbalance', 'cartoon', 'deinterlace1', 'deinterlace2']

    def _specific_initialization(self):
        """Camera initialization with Picamera2."""
        self._transform = Transform(hflip=self.capture_flip, vflip=False)
        self._preview_started = False
        self._overlay_cache = {}
        self._overlay = None
        
        # Preview full resolution 1280x960
        preview_resolution = (1280, 960)
        self._preview_config = self._cam.create_video_configuration(
            main={"size": preview_resolution, "format": "RGB888"},
            lores={"size": (640, 480), "format": "YUV420"},
            transform=self._transform,
            controls={"FrameRate": 30.0}
        )
        self._cam.configure(self._preview_config)
        self._cam.start()
        time.sleep(2.0)  # AWB/AE stabilization

        # Adjust preview gain/sharpness
        preview_gain = min(self.preview_iso / 100.0, 6.0)
        self._cam.set_controls({"AnalogueGain": preview_gain, "Sharpness": 1.5})
        self._cam.stop()

    def _create_overlay_image(self, size, text, alpha):
        """Create overlay image with text."""
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = fonts.get_pil_font(str(text), fonts.CURRENT, size[0]*0.6, size[1]*0.3)
        bbox = font.getbbox(str(text))
        txt_width = bbox[2] - bbox[0]
        txt_height = bbox[3] - bbox[1]
        position = ((size[0] - txt_width) // 2, (size[1] - txt_height) // 2)
        draw.text(position, str(text), (255, 255, 255, alpha), font=font)
        return image

    def _show_overlay(self, text, alpha):
        """Show overlay using cache if available."""
        if not self._window:
            return
        text_str = str(text)
        rect = self.get_rect()
        if not self._overlay_cache:
            for num in range(1, 6):
                self._overlay_cache[num] = self._create_overlay_image(rect.size, str(num), alpha)
            smile_text = get_translated_text('smile')
            self._overlay_cache['smile'] = self._create_overlay_image(rect.size, smile_text, alpha)
        if text_str.isdigit() and int(text_str) in self._overlay_cache:
            self._overlay = self._overlay_cache[int(text_str)]
        elif text_str == get_translated_text('smile') and 'smile' in self._overlay_cache:
            self._overlay = self._overlay_cache['smile']
        else:
            self._overlay = self._create_overlay_image(rect.size, text_str, alpha)

    def _hide_overlay(self):
        """Remove any existing overlay."""
        self._overlay = None

    def _post_process_capture(self, capture_data):
        """Rework capture data."""
        array, effect = capture_data
        image = Image.fromarray(array)
        if effect and effect != 'none':
            image = self._apply_effect(image, effect)
        return image

    def _apply_effect(self, image, effect):
        """Apply image effect using PIL post-processing."""
        effect = effect.lower()
        if effect == 'negative':
            return ImageOps.invert(image.convert('RGB'))
        elif effect == 'solarize':
            return ImageOps.solarize(image, threshold=128)
        elif effect == 'posterise':
            return ImageOps.posterize(image, bits=2)
        elif effect == 'colorbalance':
            return ImageOps.equalize(image)
        return image

    def preview(self, window, flip=True):
        """Setup the preview."""
        self._window = window
        self.preview_flip = flip
        self._transform = Transform(hflip=flip, vflip=False)
        self._preview_config["transform"] = self._transform
        self._cam.configure(self._preview_config)
        if not self._preview_started:
            self._cam.start()
            self._preview_started = True
            time.sleep(0.5)
        self._window.show_image(self._get_preview_image())

    def _get_preview_image(self):
        """Capture and return pygame Surface for preview (fast)."""
        if not self._preview_started:
            return None
        try:
            req = self._cam.capture_request()
            try:
                array = req.make_array("main")  # RGB888 numpy array
                surf = pygame.surfarray.make_surface(array.swapaxes(0,1))
                return surf
            finally:
                req.release()
        except Exception as e:
            LOGGER.warning(f"Preview capture error: {e}")
            traceback.print_exc()
            return None

    def preview_countdown(self, timeout, alpha=60, flash_led=None):
        """Show a countdown of timeout seconds on the preview."""
        timeout = int(timeout)
        if timeout < 1 or not self._preview_started:
            return

        overlay_cache_surf = {}
        while timeout > 0:
            self._show_overlay(timeout, alpha)
            overlay_img = self._overlay
            preview_img = self._get_preview_image()

            # Convert PIL overlay to pygame.Surface if nécessaire
            if overlay_img:
                if timeout not in overlay_cache_surf:
                    if isinstance(overlay_img, Image.Image):
                        overlay_cache_surf[timeout] = pygame.image.frombuffer(
                            overlay_img.tobytes(), overlay_img.size, 'RGBA'
                        )
                    else:
                        overlay_cache_surf[timeout] = overlay_img
                overlay_surf = overlay_cache_surf[timeout]
            else:
                overlay_surf = None

            start_time = time.time()
            frame_time = 1.0 / 25.0
            while time.time() - start_time < 1.0:
                preview_img = self._get_preview_image()
                if preview_img and overlay_surf:
                    preview_img.blit(overlay_surf, (0,0))
                if preview_img:
                    updated_rect = self._window.show_image(preview_img)
                    pygame.event.pump()
                    if updated_rect:
                        pygame.display.update(updated_rect)
                elapsed = time.time() - start_time
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)

            timeout -= 1
            self._hide_overlay()
            if timeout == 1 and flash_led:
                flash_led.on()

        # Show smile overlay
        self._show_overlay(get_translated_text('smile'), alpha)
        smile_img = self._overlay
        preview_img = self._get_preview_image()
        if smile_img:
            if isinstance(smile_img, Image.Image):
                smile_surf = pygame.image.frombuffer(smile_img.tobytes(), smile_img.size, 'RGBA')
            else:
                smile_surf = smile_img
            for _ in range(5):
                preview_img = self._get_preview_image()
                if preview_img and smile_surf:
                    preview_img.blit(smile_surf, (0,0))
                    updated_rect = self._window.show_image(preview_img)
                    pygame.event.pump()
                    if updated_rect:
                        pygame.display.update(updated_rect)
                time.sleep(0.05)

    def preview_wait(self, timeout, alpha=60):
        """Wait the given time while showing live preview."""
        self._show_overlay(get_translated_text('smile'), alpha)
        start_time = time.time()
        while time.time() - start_time < timeout:
            updated_rect = self._window.show_image(self._get_preview_image())
            pygame.event.pump()
            if updated_rect:
                pygame.display.update(updated_rect)

    def stop_preview(self):
        """Stop the preview."""
        self._hide_overlay()
        if self._preview_started:
            self._cam.stop()
            self._preview_started = False
        self._window = None

    def capture(self, effect=None):
        """Capture a new picture using Picamera2."""
        effect = str(effect).lower()
        if effect not in self.IMAGE_EFFECTS:
            raise ValueError(f"Invalid capture effect '{effect}'")
        try:
            if self.capture_iso != self.preview_iso:
                capture_gain = self.capture_iso / 100.0
                self._cam.set_controls({"AnalogueGain": capture_gain})
                time.sleep(0.3)
            array = self._cam.capture_array("main")
            self._captures.append((array, effect))
            if self.capture_iso != self.preview_iso:
                preview_gain = self.preview_iso / 100.0
                self._cam.set_controls({"AnalogueGain": preview_gain})
        except Exception as e:
            if self.capture_iso != self.preview_iso:
                preview_gain = self.preview_iso / 100.0
                self._cam.set_controls({"AnalogueGain": preview_gain})
            raise e
        self._hide_overlay()

    def quit(self):
        """Close the camera driver."""
        if self._preview_started:
            self._cam.stop()
        self._cam.close()
