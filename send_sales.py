import requests
import os
import math
from datetime import date, timedelta
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

    possible_paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for path in possible_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass

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

def rounded_image(img, radius):
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (0, 0, img.size[0] - 1, img.size[1] - 1),
        radius=radius,
        fill=255
    )
    img.putalpha(mask)
    return img

def current_week_text():
    today = date.today()
    days_since_tuesday = (today.weekday() - 1) % 7
    start = today - timedelta(days=days_since_tuesday)
    end = start + timedelta(days=7)
    months = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    return f"{start.day:02d} {months[start.month - 1]} - {end.day:02d} {months[end.month - 1]}"

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
    (70, 182, 410, 185),   (524, 182, 410, 185),   (980, 182, 410, 185),
    (70, 462, 410, 185),   (524, 462, 410, 185),   (980, 462, 410, 185),
    (70, 740, 410, 185),   (524, 740, 410, 185),   (980, 740, 410, 185),
]

text_slots = [
    (73, 395, 345, 412),   (532, 395, 804, 412),   (994, 395, 1265, 412),
    (73, 675, 345, 702),   (532, 675, 804, 702),   (994, 675, 1265, 702),
    (73, 950, 345, 992),   (532, 950, 804, 992),   (994, 950, 1265, 992),
]

discount_slots = [
    (398, 333), (857, 333), (1319, 333),
    (398, 623), (857, 623), (1319, 623),
    (398, 913), (857, 913), (1319, 913),
]

price_slots = [
    (412, 391), (871, 391), (1333, 391),
    (412, 672), (871, 672), (1333, 672),
    (412, 945), (871, 945), (1333, 945),
]

name_font = font(18, True)
champ_font = font(15, False)
discount_font = font(24, True)
price_font = font(27, True)
rp_font = font(15, True)
empty_font = font(14, False)
week_font = font(22, True)

PAGE_SIZE = 9
pages = math.ceil(len(resolved) / PAGE_SIZE)

for page in range(pages):

    canvas = Image.open("template.png").convert("RGB")
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (1215, 72),
        current_week_text(),
        fill=(10, 16, 30),
        font=week_font
    )

    page_items = resolved[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    for i, skin in enumerate(page_items):

        x, y, w, h = image_slots[i]

        try:
            img_data = requests.get(skin["url"], timeout=20).content
            splash = Image.open(BytesIO(img_data)).convert("RGB")
            splash = cover_resize(splash, (w, h))

            splash = splash.resize((w - 8, h - 8), Image.LANCZOS)
            splash = rounded_image(splash, 20)
            canvas.paste(splash, (x - 7, y + 1), splash)

        except Exception as e:
            print("Error imagen:", e)

        name_x, name_y, _, _ = text_slots[i]

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

        dx, dy = discount_slots[i]
        discount_text = f"-{skin['discount']}%"
        discount_bbox = draw.textbbox((0, 0), discount_text, font=discount_font)
        discount_w = discount_bbox[2] - discount_bbox[0] + 24
        discount_h = 34
        discount_x2 = dx + 82
        discount_x1 = discount_x2 - discount_w
        discount_y1 = dy - 4
        discount_y2 = discount_y1 + discount_h

        draw.rounded_rectangle(
            (discount_x1 + 2, discount_y1 + 3, discount_x2 + 2, discount_y2 + 3),
            radius=17,
            fill=(208, 221, 255)
        )

        draw.rounded_rectangle(
            (discount_x1, discount_y1, discount_x2, discount_y2),
            radius=17,
            fill=(45, 95, 255)
        )

        draw.text(
            (discount_x1 + 12, discount_y1 + 2),
            discount_text,
            fill=(255, 255, 255),
            font=discount_font
        )

        px, py = price_slots[i]
        price_text = str(skin["price"])
        price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
        price_w = price_bbox[2] - price_bbox[0]

        draw.rounded_rectangle(
            (px - 48, py - 4, px + 104, py + 37),
            radius=12,
            fill=(247, 250, 255)
        )

        draw.text(
            (px - 34, py),
            price_text,
            fill=(10, 16, 30),
            font=price_font
        )

        draw.text(
            (px - 28 + price_w, py + 8),
            "RP",
            fill=(85, 103, 150),
            font=rp_font
        )

    for empty_i in range(len(page_items), 9):

        x, y, w, h = image_slots[empty_i]

        draw.text(
            (x + 145, y + 150),
            "Sin más ofertas",
            fill=(120, 130, 160),
            font=empty_font
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
