import qrcode
from PIL import Image, ImageDraw, ImageFont

def generate_qr_png(output_file='qr.png', size=10, wifi_ssid=None, wifi_password=None, url=None, label_text="WiFi"):
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


# Exemples d'utilisation :

# QR code Wi-Fi
generate_qr_png(output_file="wifi_qr.png", size=7, wifi_ssid="Photobooth", wifi_password="2HrU8ILllBxX", label_text="1 - WiFi connect")

# QR code URL
generate_qr_png(output_file="url_qr.png", size=7, url="http://192.168.4.1:8000", label_text="2 - Galerie photos")
