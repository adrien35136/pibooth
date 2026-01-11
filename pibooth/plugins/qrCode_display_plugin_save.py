import os
import threading
import pygame
from pygame import image as pg_image
from inotify_simple import INotify, flags
import pibooth

QR_PATH = "/home/adrien/Documents/pibooth/assets/wifi_qr.png"
QR_POSITION = (-160, -160)
QR_SIZE = (150, 150)

class QRCodeWatcher(threading.Thread):
    def __init__(self, filepath, callback):
        super().__init__(daemon=True)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.dirpath = os.path.dirname(filepath)
        self.callback = callback
        self.inotify = INotify()
        self.wd = self.inotify.add_watch(self.dirpath, flags.CLOSE_WRITE)
        self.running = True

    def run(self):
        while self.running:
            for event in self.inotify.read(timeout=1000):
                if event.name == self.filename and flags.CLOSE_WRITE in flags.from_mask(event.mask):
                    print("[QR Plugin] CLOSE_WRITE reçu → Rechargement QR")
                    self.callback()

    def stop(self):
        self.running = False

class QRCodePlugin(object):
    name = 'pibooth-core:qr_code'

    def __init__(self, plugin_manager):
        self._pm = plugin_manager
        self.qr_image = None
        self.watcher = None

    def load_qr_image(self):
        try:
            img = pg_image.load(QR_PATH)
            self.qr_image = pygame.transform.scale(img, QR_SIZE)
            print("[QR Plugin] QR code chargé")
        except Exception as e:
            print(f"[QR Plugin] Erreur chargement QR: {e}")
            self.qr_image = None

    @pibooth.hookimpl
    def pibooth_startup(self, app):
        self.load_qr_image()
        self.watcher = QRCodeWatcher(QR_PATH, self.load_qr_image)
        self.watcher.start()
        print("[QR Plugin] Surveillance du QR code démarrée")

    @pibooth.hookimpl
    def pibooth_cleanup(self, app):
        if self.watcher:
            self.watcher.stop()
            self.watcher.join()
            print("[QR Plugin] Surveillance du QR code arrêtée")

    @pibooth.hookimpl
    def state_idle_do(self, app, events):
        if self.qr_image:
            rect = app.window.surface.get_rect()
            pos = (rect.right + QR_POSITION[0], rect.bottom + QR_POSITION[1])
            app.window.surface.blit(self.qr_image, pos)

    @pibooth.hookimpl
    def state_idle_exit(self, app):
        self.qr_image = None
