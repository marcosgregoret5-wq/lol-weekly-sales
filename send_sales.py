import requests
import os
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "")

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
    return text.lower().replace("&", "and").replace("'", "").replace(".", "").replace("-", " ").strip()

def font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def cover_resize(img, size):
    tw, th = size
    w, h = img.size
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = int((nh - th) * 0.25)
    return img.crop((left, top, left + tw, top + th))

sales = requests.get(SALES_URL).json()
sales = sorted(sales, key=lambda x: x["discount"], reverse=True)

version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

champion_data = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"
).json()["data"]

champ_lookup = {normalize(champ["name"]): key for key, champ in champion_data.items()}

resolved = []

for sale in sales:
    champion_name = sale["champion"].lower()
    champion_id = SPECIAL_CHAMPIONS.get(champion_name) or champ_lookup.get(normalize(champion_name))

    if not champion_id:
        print("No se encontró campeón:", champion_name)
        continue

    champ = champion_data[champion_id]
    target = normalize(sale["skin"])

    skin_num = None

    for s in champ["skins"]:
        if normalize(s["name"]) == target:
            skin_num = s["num"]
            break

    if skin_num is None:
        print("No se encontró skin:", sale["skin"])
        continue

    resolved.append({
        "skin": sale["skin"].title(),
        "champion": sale["champion"].title(),
        "discount": sale["discount"],
        "price": sale["price"],
        "week": sale["week"],
        "url": f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_id}_{skin_num}.jpg"
    })

image_slots = [
    (70, 182, 410, 185),   (528, 182, 410, 185),   (990, 182, 410, 185),
    (70, 472, 410, 185),   (528, 472, 410, 185),   (990, 472, 410, 185),
    (70, 762, 410, 185),   (528, 762, 410, 185),   (990, 762, 410, 185),
]

text_slots = [
    (73, 388, 345, 412),   (532, 388, 804, 412),   (994, 388, 1265, 412),
    (73, 678, 345, 702),   (532, 678, 804, 702),   (994, 678, 1265, 702),
    (73, 968, 345, 992),   (532, 968, 804, 992),   (994, 968, 1265, 992),
]

discount_slots = [
    (398, 333), (857, 333), (1319, 333),
    (398, 623), (857, 623), (1319, 623),
    (398, 913), (857, 913), (1319, 913),
]

price_slots = [
    (412, 394), (871, 394), (1333, 394),
    (412, 684), (871, 684), (1333, 684),
    (412, 974), (871, 974), (1333, 974),
]

name_font = font(18, True)
champ_font = font(15, False)
discount_font = font(24, True)
price_font = font(27, True)

PAGE_SIZE = 9
pages = math.ceil(len(resolved) / PAGE_SIZE)

for page in range(pages):

    canvas = Image.open("template.png").convert("RGB")
    draw = ImageDraw.Draw(canvas)

    page_items = resolved[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    for i, skin in enumerate(page_items):

        x, y, w, h = image_slots[i]

        try:
            img_data = requests.get(skin["url"], timeout=20).content
            splash = Image.open(BytesIO(img_data)).convert("RGB")
            splash = cover_resize(splash, (w, h))

            splash = splash.resize((w - 14, h - 14), Image.LANCZOS)
            canvas.paste(splash, (x + 7, y + 7))

        except Exception as e:
            print("Error imagen:", e)

        name_x, name_y, champ_x, champ_y = text_slots[i]

        draw.rectangle(
            (name_x - 2, name_y - 2, name_x + 280, name_y + 40),
            fill=(247, 250, 255)
        )

        draw.text(
            (name_x, name_y),
            skin["skin"][:28],
            fill=(10, 16, 30),
            font=name_font
        )

        draw.text(
            (champ_x, champ_y),
            skin["champion"][:24],
            fill=(115, 130, 170),
            font=champ_font
        )

        dx, dy = discount_slots[i]

        draw.rounded_rectangle(
            (dx - 5, dy - 3, dx + 80, dy + 35),
            radius=15,
            fill=(250, 252, 255)
        )

        draw.text(
            (dx, dy),
            f"-{skin['discount']}%",
            fill=(45, 95, 255),
            font=discount_font
        )

        px, py = price_slots[i]

        draw.rectangle(
            (px - 5, py - 3, px + 80, py + 35),
            fill=(247, 250, 255)
        )

        draw.text(
            (px, py),
            str(skin["price"]),
            fill=(10, 16, 30),
            font=price_font
        )

    for empty_i in range(len(page_items), 9):

        x, y, w, h = image_slots[empty_i]

        draw.rounded_rectangle(
            (x + 7, y + 7, x + w - 7, y + h + 80),
            radius=18,
            fill=(247, 250, 255)
        )

        draw.text(
            (x + 90, y + 110),
            "Sin más ofertas",
            fill=(120, 130, 160),
            font=name_font
        )

    filename = f"sales_page_{page + 1}.png"
    canvas.save(filename)

    if WEBHOOK_URL:
        with open(filename, "rb") as f:
            requests.post(
                WEBHOOK_URL,
                data={
                    "content": f"🎮 **GPBot Tienda Semanal** | Página {page + 1}/{pages}"
                },
                files={
                    "file": (filename, f, "image/png")
                }
            )

print("Finalizado")
