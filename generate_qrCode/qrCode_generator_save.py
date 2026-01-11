import qrcode
from PIL import Image, ImageDraw, ImageFont

def generate_wifi_qr_png(ssid, password, output_file='wifi_qr.png', size=10):
    wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};;"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=1,
    )
    qr.add_data(wifi_string)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    font_size = 25
    spacing = 5  # ← Ajuste ici selon besoin

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text = "Scan : WiFi"
    text_width = font.getlength(text)
    ascent, descent = font.getmetrics()
    text_height = ascent + descent

    qr_width, qr_height = qr_img.size
    new_height = qr_height + spacing + text_height

    # Crée image avec espace pour texte
    new_img = Image.new("RGB", (qr_width, new_height), "white")
    new_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    text_x = (qr_width - text_width) / 2
    text_y = qr_height + spacing

    draw.text((text_x, text_y), text, font=font, fill="black")

    new_img.save(output_file)
    print(f"QR Code enregistré sous : {output_file}")

# Exemple d’utilisation
generate_wifi_qr_png("Photobooth", "Photobooth", size=7)
