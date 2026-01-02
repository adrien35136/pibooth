# -*- coding: utf-8 -*-

import time
import threading
import numpy as np
import pygame
from picamera2 import Picamera2
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
    Preview is handled by capturing frames and displaying them in pygame.
    """

    IMAGE_EFFECTS = ['none']

    def _specific_initialization(self):
        self._preview_started = False
        self._preview_running = False
        self._preview_thread = None
        self._window = None
        self._overlay_surface = None
        self._preview_surface = None

        self._transform = Transform(
            hflip=self.capture_flip,
            vflip=False
        )

        # Preview configuration - lower resolution for better performance
        self._preview_config = self._cam.create_preview_configuration(
            main={
                "size": (800, 600),      # Lower res for better FPS
                "format": "RGB888"        # Easy to convert to pygame
            },
            transform=self._transform,
            controls={
                "FrameRate": 30
            }
        )

        self._cam.configure(self._preview_config)

    # ------------------------------------------------------------------
    # PREVIEW (Software with pygame)
    # ------------------------------------------------------------------

    def _preview_loop(self):
        """Background thread that continuously updates the preview."""
        while self._preview_running:
            try:
                # Capture a frame from the camera
                array = self._cam.capture_array("main")
                
                # Convert numpy array to pygame surface
                # array is RGB888, shape (H, W, 3)
                surface = pygame.surfarray.make_surface(np.rot90(array, k=-1))
                
                # Scale to fit the window
                if self._window:
                    rect = self._window.get_rect()
                    self._preview_surface = pygame.transform.scale(surface, rect.size)
                    
                    # Display the preview
                    self._window.surface.blit(self._preview_surface, (0, 0))
                    
                    # Display overlay if any
                    if self._overlay_surface:
                        self._window.surface.blit(self._overlay_surface, (0, 0))
                    
                    pygame.display.update()
                    
            except Exception as e:
                LOGGER.debug(f"Preview frame error: {e}")
                time.sleep(0.033)  # ~30 FPS fallback
                
    def preview(self, window, flip=True):
        """Start software preview with pygame."""
        self._window = window
        self.preview_flip = flip

        self._transform = Transform(hflip=flip, vflip=False)
        self._preview_config["transform"] = self._transform
        self._cam.configure(self._preview_config)

        if not self._preview_started:
            LOGGER.info("Starting Picamera2 software preview")
            self._cam.start()
            self._preview_started = True
            time.sleep(0.5)  # AWB / AE warmup

        # Create transparent overlay surface once
        size = self._window.get_rect().size
        self._overlay_surface = pygame.Surface(size, pygame.SRCALPHA)
        
        # Start preview thread
        self._preview_running = True
        self._preview_thread = threading.Thread(target=self._preview_loop, daemon=True)
        self._preview_thread.start()

    def stop_preview(self):
        """Stop software preview."""
        self._preview_running = False
        if self._preview_thread:
            self._preview_thread.join(timeout=1.0)
            self._preview_thread = None
            
        if self._preview_started:
            LOGGER.info("Stopping Picamera2 preview")
            self._cam.stop()
            self._preview_started = False

        self._overlay_surface = None
        self._preview_surface = None
        self._window = None

    # ------------------------------------------------------------------
    # OVERLAYS (pygame)
    # ------------------------------------------------------------------

    def _draw_overlay(self, text, alpha=180):
        """Draw centered overlay text using pygame."""
        if not self._window or not self._overlay_surface:
            return

        # Clear the overlay
        self._overlay_surface.fill((0, 0, 0, 0))

        font_size = int(self._overlay_surface.get_width() * 0.35)
        font = pygame.font.Font(None, font_size)

        label = font.render(str(text), True, (255, 255, 255))
        label.set_alpha(alpha)

        rect = label.get_rect(center=self._overlay_surface.get_rect().center)
        self._overlay_surface.blit(label, rect)

    def _clear_overlay(self):
        if self._overlay_surface:
            self._overlay_surface.fill((0, 0, 0, 0))

    # ------------------------------------------------------------------
    # COUNTDOWN
    # ------------------------------------------------------------------

    def preview_countdown(self, timeout, alpha=180, flash_led=None):
        """Countdown overlay (preview thread continues in background)."""
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
        Capture using Picamera2 (fallback).
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
            self._preview_running = False
            if self._preview_thread:
                self._preview_thread.join(timeout=1.0)
            if self._preview_started:
                self._cam.stop()
            self._cam.close()
        except Exception:
            pass
