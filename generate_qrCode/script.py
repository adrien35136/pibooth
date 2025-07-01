from PIL import Image

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

if __name__ == "__main__":

	# Génère un QR code pointant vers ton site ou ce que tu veux
	wifi_qr_code_path = "./wifi_qr.png"
	url_qr_code_path = "./url_qr.png"
	intro_image_1 = "./intro_1_origin.png"
	intro_image_2 = "./intro_2_origin.png"

	# Crée une image d'intro avec les QRss code dessus
	intro1_with_qr_path = "./intro_1.png"
	intro2_with_qr_path = "./intro_2.png"
	overlay_intro_with_qr(intro_image_1, wifi_qr_code_path, url_qr_code_path, intro1_with_qr_path)
	overlay_intro_with_qr(intro_image_2, wifi_qr_code_path, url_qr_code_path, intro2_with_qr_path)

