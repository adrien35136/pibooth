# -*- coding: utf-8 -*-

import time
from picamera2 import Preview
from libcamera import Transform
from PIL import Image
from pibooth.camera.base import BaseCamera
from pibooth.utils import LOGGER


class RpiCamera(BaseCamera):
    """
    Raspberry Pi Camera backend for pibooth
    using Picamera2 + QTGL GPU preview
    """

    IMAGE_EFFECTS = ['none']

    def _specific_initialization(self):
        LOGGER.info("Initializing Picamera2 backend")

        # IMPORTANT:
        # Picamera2 instance is ALREADY created by pibooth
        # and stored in self._proxy
        self._camera = self._proxy
        if self._camera is None:
            raise EnvironmentError("No Raspberry Pi camera detected")

        self._preview = None
        self._preview_started = False

        transform = Transform(hflip=self.capture_flip, vflip=False)

        # Preview config (FAST, GPU)
        self._preview_config = self._camera.create_preview_configuration(
            main={
                "size": (1280, 960),
                "format": "YUV420"
            },
            transform=transform
        )

        # Capture config (FULL RES SENSOR)
        self._capture_config = self._camera.create_still_configuration(
            transform=transform
        )

        self._camera.configure(self._preview_config)
        self._camera.start()

        # Let AE / AWB stabilize
        time.sleep(1.5)

    # ------------------------------------------------------------------

    def preview(self, window, flip=True):
        """Start GPU preview (QTGL)."""
        self._window = window

        if not self._preview_started:
            LOGGER.info("Starting Picamera2 preview (QTGL)")
            self._preview = self._camera.start_preview(Preview.QTGL)
            self._preview_started = True

    def preview_wait(self, timeout, alpha=60):
        """Let preview run while waiting."""
        time.sleep(timeout)

    def preview_countdown(self, timeout, alpha=60, flash_led=None):
        """Countdown drawn by pygame (NOT camera)."""
        timeout = int(timeout)
        if timeout < 1:
            return

        while timeout > 0:
            self._window.show_countdown(timeout)
            time.sleep(1)
            timeout -= 1

        self._window.show_smile()
        time.sleep(0.5)

    def stop_preview(self):
        if self._preview_started:
            self._camera.stop_preview()
            self._preview_started = False
        self._window = None

    # ------------------------------------------------------------------

    def capture(self, effect=None):
        """Capture full resolution image."""
        self._camera.stop()
        self._camera.configure(self._capture_config)
        self._camera.start()

        array = self._camera.capture_array("main")
        image = Image.fromarray(array)
        self._captures.append((image, effect))

        # Restore preview
        self._camera.stop()
        self._camera.configure(self._preview_config)
        self._camera.start()

    # ------------------------------------------------------------------

    def quit(self):
        if self._preview_started:
            self._camera.stop_preview()
        self._camera.stop()
        self._camera.close()
