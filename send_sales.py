import requests

js = requests.get("https://lolskinsale.com/scripts/script.js").text

print(js[:10000])
