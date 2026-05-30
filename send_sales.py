import requests
import os
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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

def get_font(size, bold=False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except:
            pass
    return ImageFont.load_default()

def cover_resize(img, size):
    target_w, target_h = size
    w, h = img.size
    scale = max(target_w / w, target_h / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - target_w) // 2
    top = (nh - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def draw_rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

sales = requests.get(SALES_URL).json()
sales = sorted(sales, key=lambda x: x["discount"], reverse=True)

version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

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

    splash_url = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_id}_{skin_num}.jpg"

    resolved_skins.append({
        "skin": sale["skin"].title(),
        "discount": sale["discount"],
        "price": sale["price"],
        "url": splash_url,
        "week": sale["week"]
    })

PAGE_SIZE = 9
pages = math.ceil(len(resolved_skins) / PAGE_SIZE)

font_title = get_font(54, True)
font_brand = get_font(34, True)
font_subtitle = get_font(24, False)
font_card_title = get_font(24, True)
font_badge = get_font(22, True)
font_price = get_font(26, True)
font_small = get_font(18, False)

for page in range(pages):
    page_skins = resolved_skins[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    W, H = 1600, 1250
    canvas = Image.new("RGB", (W, H), (5, 12, 22))
    draw = ImageDraw.Draw(canvas)

    for y in range(H):
        r = int(5 + y / H * 8)
        g = int(12 + y / H * 12)
        b = int(22 + y / H * 25)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    draw.text((50, 35), "GPBot", fill=(255, 255, 255), font=font_brand)
    draw.text((205, 35), "Tienda Semanal", fill=(220, 170, 70), font=font_title)
    draw.text((55, 105), "LEAGUE OF LEGENDS", fill=(120, 180, 220), font=font_subtitle)

    draw.rounded_rectangle(
        (1120, 45, 1535, 130),
        radius=18,
        outline=(190, 135, 55),
        width=2,
        fill=(10, 24, 38)
    )
    draw.text((1150, 65), f"Página {page + 1}/{pages}", fill=(220, 170, 70), font=font_card_title)
    draw.text((1150, 98), f"{len(resolved_skins)} skins en oferta", fill=(235, 235, 235), font=font_small)

    card_w, card_h = 480, 300
    img_h = 215
    gap_x, gap_y = 35, 35
    start_x, start_y = 55, 170

    for idx, skin in enumerate(page_skins):
        row = idx // 3
        col = idx % 3
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        draw_rounded_rect(
            draw,
            (x, y, x + card_w, y + card_h),
            12,
            fill=(8, 24, 38),
            outline=(180, 125, 45),
            width=2
        )

        try:
            img_data = requests.get(skin["url"], timeout=20).content
            splash = Image.open(BytesIO(img_data)).convert("RGB")
            splash = cover_resize(splash, (card_w, img_h))
            canvas.paste(splash, (x, y))
        except Exception as e:
            print(e)
            draw.rectangle((x, y, x + card_w, y + img_h), fill=(30, 35, 45))

        overlay = Image.new("RGBA", (card_w, 85), (5, 14, 24, 225))
        canvas.paste(overlay, (x, y + img_h), overlay)

        draw.text((x + 16, y + img_h + 12), skin["skin"][:36], fill=(255, 255, 255), font=font_card_title)

        badge_x = x + 16
        badge_y = y + img_h + 50
        draw.rounded_rectangle(
            (badge_x, badge_y, badge_x + 145, badge_y + 34),
            radius=7,
            fill=(235, 175, 55)
        )
        draw.text((badge_x + 13, badge_y + 5), f"{skin['discount']}% OFF", fill=(5, 12, 22), font=font_badge)

        draw.text((x + card_w - 130, badge_y + 3), f"{skin['price']} RP", fill=(180, 225, 255), font=font_price)

    draw.line((55, 1190, 1545, 1190), fill=(160, 110, 45), width=2)
    draw.text((60, 1205), "GPBot - Bot de LoL", fill=(220, 170, 70), font=font_small)
    draw.text((600, 1205), "Datos: LoLSkinSale + Riot Data Dragon", fill=(215, 215, 215), font=font_small)
    draw.text((1120, 1205), "No afiliado a Riot Games", fill=(170, 170, 170), font=font_small)

    filename = f"sales_page_{page + 1}.png"
    canvas.save(filename, quality=95)

    with open(filename, "rb") as f:
        requests.post(
            WEBHOOK_URL,
            data={"content": f"🎮 **GPBot Tienda Semanal** ({page + 1}/{pages})"},
            files={"file": (filename, f, "image/png")}
        )

print("Finalizado")
