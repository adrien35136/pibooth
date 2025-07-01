import json
import string
import time
import subprocess
import os
import ipaddress
import qrcode
from PIL import Image, ImageDraw, ImageFont
from filelock import FileLock, Timeout
import random

CHECK_INTERVAL = 10               # Seconds
HOTSPOT_SUBNET = ipaddress.ip_network("192.168.4.0/24")
MAX_USERS = 6
LOCK_PATH = "/tmp/hotspot_restart.lock"

# QR dcode define
WIFI_QR_CODE_PATH = "/home/pi/photo-booth/assets/wifi_qr.png"
URL_QR_CODE_PATH = "/home/pi/photo-booth/assets/url_qr.png"
INTRO_IMAGE1_ORIG_PATH = "/home/pi/photo-booth/assets/intro_1_origin.png"
INTRO_IMAGE2_ORIG_PATH = "/home/pi/photo-booth/assets/intro_2_origin.png"
OUTPUT_INTRO1_WITH_QR_PATH = "/home/pi/photo-booth/assets/intro_1.png"
OUTPUT_INTRO2_WITH_QR_PATH = "/home/pi/photo-booth/assets/intro_2.png"

# def get_mac_list_from_wlan0():
    # """Retourne la liste des MACs connectées et autorisées (authorized) sur wlan0"""
    # try:
        # result = subprocess.check_output(["iw", "dev", "wlan1", "station", "dump"]).decode()
        # macs = []
        # current_mac = None

        # for line in result.splitlines():
            # line = line.strip()
            # if line.startswith("Station"):
                # current_mac = line.split()[1]
            # elif current_mac and line.startswith("authorized:") and "yes" in line: # l'utilisateur a le bon mot de passe
                    # macs.append(current_mac)
                    # current_mac = None  # pour éviter les doublons accidentels
        # return macs
    # except Exception as e:
        # print(f"[ERROR] Failed to get MAC list from wlan1: {e}")
        # return []

def get_mac_list_from_wlan1():
    """
    Retourne la liste des adresses MAC autorisées (AUTHORIZED) via hostapd_cli.
    """
    try:
        output = subprocess.check_output(["sudo", "hostapd_cli", "all_sta"]).decode()
        authorized_macs = []

        lines = output.splitlines()
        current_mac = None

        for line in lines:
            line = line.strip()

            # Si la ligne contient une adresse MAC
            if len(line) == 17 and line.count(":") == 5:
                current_mac = line

            # Vérifie les flags de la station -> vérifier si la personne est bien connecté avec le bon mot de passe
            elif line.startswith("flags=") and "AUTHORIZED" in line:
                if current_mac:
                    authorized_macs.append(current_mac)
                    current_mac = None

        return authorized_macs

    except Exception as e:
        print(f"[ERROR] Failed to get MAC list from wlan1: {e}")
        return []

def change_wifi_password(new_password, config_file="/etc/hostapd/hostapd.conf"):
    try:
        with open(config_file, "r") as f:
            lines = f.readlines()

        with open(config_file, "w") as f:
            for line in lines:
                if line.startswith("wpa_passphrase="):
                    f.write(f"wpa_passphrase={new_password}\n")
                else:
                    f.write(line)

        print(f"[INFO] Nouveau mot de passe appliqué : {new_password}")

        # Arrêt propre
        subprocess.run(["systemctl", "stop", "hostapd"], check=True)
        time.sleep(2)

        # Vérification si hostapd est bien arrêté
        status = subprocess.run(["systemctl", "is-active", "hostapd"], capture_output=True, text=True)
        if "inactive" not in status.stdout:
            print("[WARN] hostapd encore actif, tentative de kill")
            subprocess.run(["pkill", "-9", "hostapd"])

        time.sleep(2)
        subprocess.run(["systemctl", "start", "hostapd"], check=True)
        print("[INFO] Hostapd redémarré avec succès")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erreur de commande système : {e}")
    except Exception as e:
        print(f"[ERROR] Problème lors du changement de mot de passe Wi-Fi : {e}")
     
def overlay_intro_with_qr(intro_img_path, wifi_qr_code_path, url_qr_code_path, output_path):
    """
    Combine l'image d'intro et les QRs code, sauvegarde dans output_path.
    """
    intro_img = Image.open(intro_img_path).convert("RGBA")
    wifi_qr_code_img = Image.open(wifi_qr_code_path).convert("RGBA")
    url_qr_code_img = Image.open(url_qr_code_path).convert("RGBA")

    position_wifi_qr_code = (180, 100)
    position_url_qr_code = (500, 100)

    intro_img.paste(wifi_qr_code_img, position_wifi_qr_code, wifi_qr_code_img)  # Le 3e argument garde la transparence
    intro_img.paste(url_qr_code_img, position_url_qr_code, url_qr_code_img)  # Le 3e argument garde la transparence

    intro_img.save(output_path)

def generate_qr_png(output_file='qr.png', size=7, wifi_ssid=None, wifi_password=None, url=None, label_text="WiFi"):
    """
    Génère un QR code PNG avec un texte en dessous.
    Soit pour un Wi-Fi (ssid + password), soit pour une URL.
    
    Args:
        output_file (str): nom du fichier PNG à générer.
        size (int): taille de chaque carré du QR code.
        wifi_ssid (str): nom du réseau Wi-Fi (optionnel).
        wifi_password (str): mot de passe du réseau Wi-Fi (optionnel).
        url (str): URL à encoder (optionnel).
        label_text (str): texte à afficher sous le QR code (default "WiFi").
        
    Si wifi_ssid est fourni : Génère un QR code Wi-Fi (mot de passe aléatoire si None)
    Sinon si url est fourni, génère un QR code URL.
    """
	
    if wifi_ssid:
        if not wifi_password:
            # Génère un mot de passe Wi-Fi aléatoire
            wifi_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            print(f"[INFO] Mot de passe Wi-Fi généré pour SSID '{wifi_ssid}': {wifi_password}")
        data = f"WIFI:T:WPA;S:{wifi_ssid};P:{wifi_password};;"
    elif url:
        # URL simple
        data = url
    else:
        raise ValueError("Il faut fournir soit wifi_ssid (pour WiFi), soit url (pour un lien)")

    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Prépare le texte sous le QR
    font_size = 25
    spacing = 5

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text_width = font.getlength(label_text)
    ascent, descent = font.getmetrics()
    text_height = ascent + descent

    qr_width, qr_height = qr_img.size
    new_height = qr_height + spacing + text_height

    new_img = Image.new("RGB", (qr_width, new_height), "white")
    new_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    text_x = (qr_width - text_width) / 2
    text_y = qr_height + spacing

    draw.text((text_x, text_y), label_text, font=font, fill="black")

    new_img.save(output_file)
    print(f"QR Code enregistré sous : {output_file}")
    
def main():
    lock = FileLock(LOCK_PATH, timeout=1)
    with lock:
        while True:
            users_connected = get_mac_list_from_wlan1()

            if len(users_connected) >= MAX_USERS:
                print("[INFO] Trop de connexions, Réinitialisation du Wi-Fi...")

                new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                try:
                    change_wifi_password(new_password)
                except Exception as e:
                    print(f"[ERROR] Impossible de changer le mot de passe : {e}")
                    continue

                generate_qr_png(output_file=WIFI_QR_CODE_PATH, wifi_ssid="Photobooth", wifi_password=new_password, label_text="1 - WiFi connect")
                overlay_intro_with_qr(INTRO_IMAGE1_ORIG_PATH, WIFI_QR_CODE_PATH, URL_QR_CODE_PATH, OUTPUT_INTRO1_WITH_QR_PATH)
                overlay_intro_with_qr(INTRO_IMAGE2_ORIG_PATH, WIFI_QR_CODE_PATH, URL_QR_CODE_PATH, OUTPUT_INTRO2_WITH_QR_PATH)
                
                print("[INFO] Pause de sécurité après changement de mot de passe pour laisser le temps à hotsapt de bien redémarrer")
                time.sleep(30)  # Pause spéciale après MAJ, ne pas retirer

            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
