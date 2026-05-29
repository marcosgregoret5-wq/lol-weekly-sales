import requests
import os

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

url = "https://script.google.com/macros/s/AKfycbxqlNW0mNo7FsGo0hR2_2jwJ_WAxC1HiJoKB92Sfupv_1llL1vz04DKRivr-vxPtpQwvQ/exec"

data = requests.get(url).json()

mensaje = "🎮 **OFERTAS SEMANALES DE LEAGUE OF LEGENDS**\n\n"

for skin in data:
    mensaje += f"🔥 {skin['skin'].title()} - {skin['discount']}% OFF ({skin['price']} RP)\n"

# Discord tiene límite de 2000 caracteres
mensaje = mensaje[:1900]

requests.post(
    WEBHOOK_URL,
    json={"content": mensaje}
)

print("Mensaje enviado")
