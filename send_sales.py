import requests

version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

print(version)
