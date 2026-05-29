import requests

version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"

data = requests.get(url).json()

print(list(data["data"].keys())[:20])
