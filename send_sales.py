import requests
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

url = "https://script.google.com/macros/s/AKfycbxqlNW0mNo7FsGo0hR2_2jwJ_WAxC1HiJoKB92Sfupv_1llL1vz04DKRivr-vxPtpQwvQ/exec"

data = requests.get(url).json()

# Primeras 9 skins
skins = data[:9]

# Crear imagen
width = 1200
height = 1200
img = Image.new("RGB", (width, height), (20, 20, 30))
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("DejaVuSans.ttf", 50)
    font_text = ImageFont.truetype("DejaVuSans.ttf", 24)
except:
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()

draw.text((30, 20), "League of Legends - Weekly Skin Sales", fill="white", font=font_title)

card_w = 360
card_h = 300

for i, skin in enumerate(skins):
    row = i // 3
    col = i % 3

    x = 30 + col * 390
    y = 100 + row * 340

    draw.rectangle(
        [x, y, x + card_w, y + card_h],
        outline=(255, 255, 255),
        width=2
    )

    draw.text(
        (x + 15, y + 15),
        skin["skin"].title(),
        fill="white",
        font=font_text
    )

    draw.text(
        (x + 15, y + 60),
        f"{skin['discount']}% OFF",
        fill=(0, 255, 0),
        font=font_text
    )

    draw.text(
        (x + 15, y + 100),
        f"{skin['price']} RP",
        fill="gold",
        font=font_text
    )

img.save("sales.png")

with open("sales.png", "rb") as f:
    requests.post(
        WEBHOOK_URL,
        data={
            "content": "🎮 Nuevas ofertas semanales de League of Legends"
        },
        files={
            "file": ("sales.png", f, "image/png")
        }
    )

print("Imagen enviada")
