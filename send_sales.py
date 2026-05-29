import requests

html = requests.get("https://lolskinsale.com/").text

print(html[:5000])
