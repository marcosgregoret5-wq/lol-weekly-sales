import requests
import os

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

mensaje = """
🎮 OFERTAS SEMANALES DE LEAGUE OF LEGENDS

Revisá las ofertas actuales:
https://lolskinsale.com/

🔥 Se actualizaron las skins en descuento.
"""

requests.post(
    WEBHOOK_URL,
    json={"content": mensaje}
)
