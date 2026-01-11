import os
import threading
import pygame
from pygame import image as pg_image
from inotify_simple import INotify, flags
import pibooth

# Chemins des QR codes
QR_PATH_WIFI = "/home/adrien/Documents/pibooth/assets/wifi_qr.png"
QR_PATH_OTHER = "/home/adrien/Documents/pibooth/assets/url_qr.png"

# Taille des QR codes
QR_SIZE = (300, 300)

# Variables globales pour les images
qr_image_wifi = None
qr_image_other = None
watcher = None

def load_qr_image_wifi():
    global qr_image_wifi
    try:
        img = pg_image.load(QR_PATH_WIFI)
        qr_image_wifi = pygame.transform.scale(img, QR_SIZE)
        print("[QR Plugin] QR code WiFi chargé")
    except Exception as e:
        print(f"[QR Plugin] Erreur chargement QR WiFi: {e}")
        qr_image_wifi = None

def load_qr_image_other():
    global qr_image_other
    try:
        img = pg_image.load(QR_PATH_OTHER)
        qr_image_other = pygame.transform.scale(img, QR_SIZE)
        print("[QR Plugin] QR code URL chargé")
    except Exception as e:
        print(f"[QR Plugin] Erreur chargement QR URL: {e}")
        qr_image_other = None

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
                    print("[QR Plugin] CLOSE_WRITE reçu → Rechargement QR WiFi")
                    self.callback()

    def stop(self):
        self.running = False

@pibooth.hookimpl
def pibooth_startup(app):
    global watcher
    load_qr_image_wifi()
    load_qr_image_other()
    watcher = QRCodeWatcher(QR_PATH_WIFI, load_qr_image_wifi)
    watcher.start()
    print("[QR Plugin] Surveillance du QR code WiFi démarrée")

@pibooth.hookimpl
def pibooth_cleanup(app):
    global watcher
    if watcher:
        watcher.stop()
        watcher.join()
        print("[QR Plugin] Surveillance du QR code WiFi arrêtée")

@pibooth.hookimpl
def state_wait_do(cfg, app, win, events):
    global qr_image_wifi, qr_image_other
    if qr_image_wifi and qr_image_other:
        rect = win.get_rect()

        # Position QR WiFi à gauche (50px du bord gauche)
        pos_wifi = (100, 730)
        
        # Position QR autre à droite (50px du bord droit)
        pos_other = (qr_image_other.get_width() + 250, 730)

        win.surface.blit(qr_image_wifi, pos_wifi)
        win.surface.blit(qr_image_other, pos_other)
