import requests
import os
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

SALES_URL = "https://script.google.com/macros/s/AKfycbxqlNW0mNo7FsGo0hR2_2jwJ_WAxC1HiJoKB92Sfupv_1llL1vz04DKRivr-vxPtpQwvQ/exec"

SPECIAL_CHAMPIONS = {
    "nunu & willump": "Nunu",
    "jarvan iv": "JarvanIV",
    "wukong": "MonkeyKing",
    "renata glasc": "Renata",
    "bel'veth": "Belveth",
    "cho'gath": "Chogath",
    "kai'sa": "Kaisa",
    "kha'zix": "Khazix",
    "kog'maw": "KogMaw",
    "lee sin": "LeeSin",
    "master yi": "MasterYi",
    "miss fortune": "MissFortune",
    "tahm kench": "TahmKench",
    "twisted fate": "TwistedFate",
    "vel'koz": "Velkoz",
    "xin zhao": "XinZhao",
    "aurelion sol": "AurelionSol",
    "dr. mundo": "DrMundo"
}

def normalize(text):
    return (
        text.lower()
        .replace("&", "and")
        .replace("'", "")
        .replace(".", "")
        .replace("-", " ")
        .strip()
    )

print("Obteniendo ofertas...")
sales = requests.get(SALES_URL).json()

print("Obteniendo versión...")
version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

print("Obteniendo championFull...")
champion_data = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"
).json()["data"]

champ_lookup = {}

for key, champ in champion_data.items():
    champ_lookup[normalize(champ["name"])] = key

resolved_skins = []

for sale in sales:

    champion_name = sale["champion"].lower()

    if champion_name in SPECIAL_CHAMPIONS:
        champion_id = SPECIAL_CHAMPIONS[champion_name]
    else:
        champion_id = champ_lookup.get(normalize(champion_name))

    if not champion_id:
        print(f"No se encontró campeón: {champion_name}")
        continue

    champion = champion_data[champion_id]

    target_skin = normalize(sale["skin"])

    skin_num = None

    for skin in champion["skins"]:
        if normalize(skin["name"]) == target_skin:
            skin_num = skin["num"]
            break

    if skin_num is None:
        print(f"No se encontró skin: {sale['skin']}")
        continue

    splash_url = (
        f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/"
        f"{champion_id}_{skin_num}.jpg"
    )

    resolved_skins.append({
        "skin": sale["skin"].title(),
        "discount": sale["discount"],
        "price": sale["price"],
        "url": splash_url
    })

print(f"Skins encontradas: {len(resolved_skins)}")

PAGE_SIZE = 9

pages = math.ceil(len(resolved_skins) / PAGE_SIZE)

try:
    title_font = ImageFont.truetype("DejaVuSans.ttf", 50)
    text_font = ImageFont.truetype("DejaVuSans.ttf", 24)
    small_font = ImageFont.truetype("DejaVuSans.ttf", 20)
except:
    title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

for page in range(pages):

    page_skins = resolved_skins[
        page * PAGE_SIZE:(page + 1) * PAGE_SIZE
    ]

    canvas = Image.new("RGB", (1920, 1400), (15, 18, 25))
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (40, 25),
        "GPBot Tienda Semanal",
        fill="white",
        font=title_font
    )

    draw.text(
        (40, 90),
        f"League of Legends - Página {page + 1}/{pages}",
        fill=(200, 200, 200),
        font=text_font
    )

    card_w = 580
    card_h = 380

    for idx, skin in enumerate(page_skins):

        row = idx // 3
        col = idx % 3

        x = 30 + col * 620
        y = 160 + row * 410

        try:
            img_data = requests.get(skin["url"], timeout=20).content

            splash = Image.open(BytesIO(img_data)).convert("RGB")
            splash = splash.resize((card_w, 300))

            canvas.paste(splash, (x, y))

        except Exception as e:
            print(e)
            continue

        draw.rectangle(
            [x, y + 300, x + card_w, y + card_h],
            fill=(25, 30, 40)
        )

        draw.text(
            (x + 10, y + 310),
            skin["skin"][:40],
            fill="white",
            font=small_font
        )

        draw.text(
            (x + 10, y + 340),
            f"🔥 {skin['discount']}% OFF",
            fill=(255, 215, 0),
            font=text_font
        )

        draw.text(
            (x + 250, y + 340),
            f"{skin['price']} RP",
            fill=(0, 255, 150),
            font=text_font
        )

    filename = f"sales_page_{page+1}.png"
    canvas.save(filename)

    with open(filename, "rb") as f:

        requests.post(
            WEBHOOK_URL,
            data={
                "content":
                f"🎮 GPBot Tienda Semanal ({page+1}/{pages})"
            },
            files={
                "file": (
                    filename,
                    f,
                    "image/png"
                )
            }
        )

print("Finalizado")
