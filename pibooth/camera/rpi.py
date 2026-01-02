# -*- coding: utf-8 -*-

import time
import pygame
from picamera2 import Picamera2, Preview
from libcamera import Transform

from pibooth.camera.base import BaseCamera
from pibooth.language import get_translated_text
from pibooth.utils import LOGGER


def get_rpi_camera_proxy(port=None):
    """Return Picamera2 instance if a camera is available."""
    try:
        cams = Picamera2.global_camera_info()
        if not cams:
            return None
        return Picamera2(port) if port is not None else Picamera2()
    except Exception:
        return None


class RpiCamera(BaseCamera):
    """
    Raspberry Pi Camera backend using Picamera2.
    Preview handled natively by GPU (DRM/EGL/QTGL).
    Overlays (countdown) drawn via PyGame above preview window.
    """

    IMAGE_EFFECTS = ['none']

    def _specific_initialization(self):
        """Initialize camera and preview configuration."""
        self._preview_started = False
        self._window = None
        self._overlay_surface = None

        self._transform = Transform(
            hflip=self.capture_flip,
            vflip=False
        )

        # GPU preview configuration (fast & smooth)
        self._preview_config = self._cam.create_preview_configuration(
            main={
                "size": (1280, 960),
                "format": "YUV420"  # GPU friendly
            },
            transform=self._transform,
            controls={
                "FrameRate": 30
            }
        )

        self._cam.configure(self._preview_config)

    # ------------------------------------------------------------------
    # PREVIEW
    # ------------------------------------------------------------------

    def preview(self, window, flip=True):
        """Start GPU preview and prepare overlay."""
        self._window = window
        self.preview_flip = flip

        self._transform = Transform(hflip=flip, vflip=False)
        self._preview_config["transform"] = self._transform
        self._cam.configure(self._preview_config)

        if not self._preview_started:
            LOGGER.info("Starting Picamera2 QTGL preview")
            self._cam.start_preview(
                Preview.QTGL,
                x=0,
                y=0,
                width=window.surface.get_width(),
                height=window.surface.get_height()
            )
            self._cam.start()
            self._preview_started = True
            time.sleep(0.5)  # AWB / AE warmup

        # Prepare overlay surface (transparent) same size as window
        size = self._window.get_rect().size
        self._overlay_surface = pygame.Surface(size, pygame.SRCALPHA)

    def stop_preview(self):
        """Stop GPU preview and remove overlay."""
        if self._preview_started:
            LOGGER.info("Stopping Picamera2 preview")
            self._cam.stop_preview()
            self._cam.stop()
            self._preview_started = False

        self._overlay_surface = None
        self._window = None

    # ------------------------------------------------------------------
    # OVERLAYS
    # ------------------------------------------------------------------

    def _draw_overlay(self, text, alpha=180):
        """Draw centered overlay text above preview using PyGame."""
        if not self._window or not self._overlay_surface:
            return

        # Clear overlay
        self._overlay_surface.fill((0, 0, 0, 0))

        # Draw text
        font_size = int(self._overlay_surface.get_width() * 0.35)
        font = pygame.font.Font(None, font_size)
        label = font.render(str(text), True, (255, 255, 255))
        label.set_alpha(alpha)
        rect = label.get_rect(center=self._overlay_surface.get_rect().center)
        self._overlay_surface.blit(label, rect)

        # Blit overlay above the preview window
        self._window.surface.blit(self._overlay_surface, (0, 0))
        pygame.display.flip()  # Update entire window

    def _clear_overlay(self):
        """Remove overlay text."""
        if self._overlay_surface and self._window:
            self._overlay_surface.fill((0, 0, 0, 0))
            self._window.surface.blit(self._overlay_surface, (0, 0))
            pygame.display.flip()

    # ------------------------------------------------------------------
    # COUNTDOWN
    # ------------------------------------------------------------------

    def preview_countdown(self, timeout, alpha=180, flash_led=None):
        """Smooth countdown overlay above GPU preview."""
        if not self._preview_started:
            raise RuntimeError("Preview must be started before countdown")

        start_time = time.time()
        end_time = start_time + timeout
        last_number = None
        fps = 25.0
        frame_time = 1.0 / fps

        while True:
            now = time.time()
            remaining = end_time - now
            if remaining <= 0:
                break

            number = int(remaining) + 1
            if number != last_number:
                self._draw_overlay(number, alpha)
                last_number = number

            # Flash LED at 2 seconds remaining
            if flash_led and int(remaining) + 1 == 2:
                flash_led.on()

            pygame.event.pump()
            time.sleep(frame_time)

        # Show smile overlay at end
        self._draw_overlay(get_translated_text("smile"), alpha)
        time.sleep(0.5)
        self._clear_overlay()

    def preview_wait(self, timeout, alpha=180):
        """Show smile overlay while waiting."""
        start = time.time()
        self._draw_overlay(get_translated_text("smile"), alpha)
        while time.time() - start < timeout:
            pygame.event.pump()
            time.sleep(0.05)
        self._clear_overlay()

    # ------------------------------------------------------------------
    # CAPTURE
    # ------------------------------------------------------------------

    def capture(self, effect=None):
        """
        Capture using Picamera2 fallback.
        For production: prefer Canon + gphoto2.
        """
        try:
            array = self._cam.switch_mode_and_capture_array(
                self._cam.create_still_configuration(
                    main={"size": (4056, 3040)}
                )
            )
            self._captures.append((array, 'none'))
        except Exception as e:
            LOGGER.error(f"Capture failed: {e}")
            raise

    def quit(self):
        """Close camera definitively."""
        try:
            if self._preview_started:
                self._cam.stop_preview()
                self._cam.stop()
            self._cam.close()
        except Exception:
            pass
