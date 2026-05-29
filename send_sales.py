import requests
import os

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

image_url = "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Nunu_3.jpg"

image_data = requests.get(image_url).content

with open("test_skin.jpg", "wb") as f:
    f.write(image_data)

with open("test_skin.jpg", "rb") as f:
    requests.post(
        WEBHOOK_URL,
        data={
            "content": "🎮 GPBot Tienda Semanal - Prueba Splash Art"
        },
        files={
            "file": ("test_skin.jpg", f, "image/jpeg")
        }
    )

print("Imagen enviada")
