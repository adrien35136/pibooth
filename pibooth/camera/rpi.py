# -*- coding: utf-8 -*-

import time
import pygame

from picamera2 import Picamera2, Preview
from libcamera import Transform

from pibooth.camera.base import BaseCamera
from pibooth.language import get_translated_text
from pibooth.utils import LOGGER


def get_rpi_camera_proxy(port=None):
    """Return True if a Raspberry Pi camera is available."""
    try:
        return bool(Picamera2.global_camera_info())
    except Exception:
        return False


class RpiCamera(BaseCamera):
    """
    Raspberry Pi Camera backend using Picamera2.
    GPU preview via EGL + pygame overlays (compatible Pibooth).
    """

    IMAGE_EFFECTS = ['none']

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------

    def _specific_initialization(self):
        LOGGER.info("Initializing Picamera2 backend")

        # IMPORTANT:
        # Pibooth does NOT inject the camera instance.
        # We must create Picamera2 ourselves.
        self._cam = Picamera2()

        self._preview_started = False
        self._window = None
        self._overlay_surface = None

        self._transform = Transform(
            hflip=self.capture_flip,
            vflip=False
        )

        self._preview_config = self._cam.create_preview_configuration(
            main={
                "size": (1280, 960),
                "format": "YUV420"
            },
            transform=self._transform,
            controls={
                "FrameRate": 30
            }
        )

        self._cam.configure(self._preview_config)

    # ------------------------------------------------------------------
    # PREVIEW (GPU – EGL)
    # ------------------------------------------------------------------

    def preview(self, window, flip=True):
        self._window = window
        self.preview_flip = flip

        self._transform = Transform(hflip=flip, vflip=False)
        self._preview_config["transform"] = self._transform
        self._cam.configure(self._preview_config)

        if not self._preview_started:
            LOGGER.info("Starting Picamera2 preview (EGL)")
            self._cam.start_preview("egl")
            self._cam.start()
            self._preview_started = True
            time.sleep(0.5)  # AE / AWB warmup

        size = self._window.get_rect().size
        self._overlay_surface = pygame.Surface(size, pygame.SRCALPHA)

    def stop_preview(self):
        if self._preview_started:
            LOGGER.info("Stopping Picamera2 preview")
            self._cam.stop_preview()
            self._cam.stop()
            self._preview_started = False

        self._overlay_surface = None
        self._window = None

    # ------------------------------------------------------------------
    # OVERLAY (pygame only)
    # ------------------------------------------------------------------

    def _draw_overlay(self, text, alpha=180):
        if not self._window or not self._overlay_surface:
            return

        self._overlay_surface.fill((0, 0, 0, 0))

        font_size = int(self._overlay_surface.get_width() * 0.35)
        font = pygame.font.Font(None, font_size)

        label = font.render(str(text), True, (255, 255, 255))
        label.set_alpha(alpha)

        rect = label.get_rect(center=self._overlay_surface.get_rect().center)
        self._overlay_surface.blit(label, rect)

        self._window.surface.blit(self._overlay_surface, (0, 0))
        pygame.display.update()

    def _clear_overlay(self):
        if self._overlay_surface and self._window:
            self._overlay_surface.fill((0, 0, 0, 0))
            self._window.surface.blit(self._overlay_surface, (0, 0))
            pygame.display.update()

    # ------------------------------------------------------------------
    # COUNTDOWN
    # ------------------------------------------------------------------

    def preview_countdown(self, timeout, alpha=180, flash_led=None):
        timeout = int(timeout)
        if timeout < 1:
            raise ValueError("Timeout must be >= 1")

        for i in range(timeout, 0, -1):
            self._draw_overlay(i, alpha)
            if i == 2 and flash_led:
                flash_led.on()
            time.sleep(1)

        self._draw_overlay(get_translated_text("smile"), alpha)
        time.sleep(0.5)
        self._clear_overlay()

    def preview_wait(self, timeout, alpha=180):
        start = time.time()
        self._draw_overlay(get_translated_text("smile"), alpha)
        while time.time() - start < timeout:
            pygame.event.pump()
            time.sleep(0.05)
        self._clear_overlay()

    # ------------------------------------------------------------------
    # CAPTURE (fallback Picamera2)
    # ------------------------------------------------------------------

    def capture(self, effect=None):
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

    # ------------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------------

    def quit(self):
        try:
            if self._preview_started:
                self._cam.stop_preview()
                self._cam.stop()
            self._cam.close()
        except Exception:
            pass
