import requests

version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

champions = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"
).json()["data"]

nunu = champions["Nunu"]

for skin in nunu["skins"]:
    print(skin["num"], "-", skin["name"])
