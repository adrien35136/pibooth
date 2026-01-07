# Intro

Je veux repartir de ma confguration actuelle sur Raspberry Pi 3 avec Pibooth qui fonctionne bien, et migrer vers Raspberry Pi 4 sur la mêeme image.

## Setup actuel sur RPI 3 fonctionnel

adrien@raspberrypi:~ $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"
adrien@raspberrypi:~ $ lsb_release -a
No LSB modules are available.
Distributor ID:	Raspbian
Description:	Raspbian GNU/Linux 11 (bullseye)
Release:	11
Codename:	bullseye
adrien@raspberrypi:~ $ uname -a
Linux raspberrypi 6.1.21-v7+ #1642 SMP Mon Apr  3 17:20:52 BST 2023 armv7l GNU/Linux
adrien@raspberrypi:~ $ cat /proc/version
Linux version 6.1.21-v7+ (dom@buildbot) (arm-linux-gnueabihf-gcc-8 (Ubuntu/Linaro 8.4.0-3ubuntu1) 8.4.0, GNU ld (GNU Binutils for Ubuntu) 2.34) #1642 SMP Mon Apr  3 17:20:52 BST 2023
adrien@raspberrypi:~ $ vcgencmd version
Mar 17 2023 10:53:39 
Copyright (c) 2012 Broadcom
version 82f3750a65fadae9a38077e3c2e217ad158c8d54 (clean) (release) (start_x)
adrien@raspberrypi:~ $ dpkg -l | grep raspberrypi-kernel
ii  raspberrypi-kernel                   1:1.20230405-1                     armhf        Raspberry Pi bootloader
ii  raspberrypi-kernel-headers           1:1.20230405-1                     armhf        Header files for the Raspberry Pi Linux kernel
adrien@raspberrypi:~ $ python
Python 3.9.2 (default, Mar 20 2025, 22:21:41) 
>>> import pygame
pygame 1.9.6

Settings pibooth : v2.0.8


# Tests 1 : PiBooth Hybrid sur Raspberry Pi 4 + Bullseye (2022-04-04-raspios-bullseye-armhf-full.img)

## 1️⃣ PiCamera V2 (preview)

- PiBooth utilise la **PiCamera V2 pour le preview**.
- Sur **Pi 4 + Bullseye** :
  - Le preview fonctionne encore ✅
  - Les réglages comme `preview_delay` ou `preview_alpha_value` sont pris en compte.
  - Tu peux voir l’aperçu sur l’écran tactile.
- Donc le preview PiCamera **reste fonctionnel**.

---

## 2️⃣ Mode Hybrid (PiCamera + Canon)

- PiBooth en **mode hybrid** attend :
  - PiCamera → preview
  - Canon via gphoto2 → capture
- Sur Pi 4 + Bullseye :
  - La PiCamera est détectée pour le preview ✅
  - LE mode hybrid est fonctionnel -> ne pas oublier d'installer gphoto2 avec pip car pour le mode hybrid pibooth fait appel a une fonctio nde detection de gphoto2


## Image installée : 

2022-04-04-raspios-bullseye-armhf-full.img (C:\Users\Adrien\Documents\Projets\Perso\Image Raspberry\Photomaton_V3_touch_screen_RPI4\2022-04-04-raspios-bullseye-armhf-full.img)

## procédure d'installation après démarrage sur la RPI 4:

sudo apt update
sudo apt upgrade -y
sudo raspi-config (Interface Options→ Legacy Camera→ Enable)
sudo reboot
sudo apt install -y python3-picamera

sudo apt install -y \
python3-pip \
python3-dev \
python3-venv \
libjpeg-dev \
libpng-dev \
libtiff5-dev \
libsdl1.2-dev \
libfreetype6-dev \
libatlas-base-dev

python3 -m pip install --upgrade pip setuptools wheel
pip3 install pygame==1.9.6
pip3 install pillow numpy
sudo apt install -y gphoto2
gphoto2 --auto-detect
pip install gphoto2

## Résultat final :

Tout est fonctionnel sauf le hostpot wifi (clé usb rtl8188eus) qui ne fonctionne pas -> problèmme de kernel

# Test 2 : Copy intact de la sd card RPI3 sur une carte sd pour RPI4

## Démarrage de la RPI4

Tout fonctionne sauf le hotspot avec la clé WIFI, le driver n'est pas bien installé car il y a un problème avec le kernel. A part ça tout fonctionne parfaitement, le preview de la caméra et la capture via gphoto2 fonctionnent parfaitement.

Solution pour le hotspot : Forcer le kernel en 32-bit (par défaut le RPI4 boot en 64-bit si l'image le permet ce qui est le cas de l'image bullseye).
Modifier le fichier /boot/config.txt et ajouter la ligne suivante :
  1: sudo nano /boot/config.txt
  2: rajouter le ligne suivante à la fin du fichier : kernel=kernel7l.img
  3: sudo reboot
  4: uname -r -> résultat : 6.1.xx-v7l+
  5: le dossier build doit exister : ls /lib/modules/$(uname -r)/build
  6: cd ~/rtl8188eus
  7: sudo dkms remove 8188eu/5.3.9 --all (Nettoyage DKMS)
  8: sudo ./dkms-install.sh





