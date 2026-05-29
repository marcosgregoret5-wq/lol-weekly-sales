import requests

data = requests.get(
    "https://script.google.com/macros/s/AKfycbxqlNW0mNo7FsGo0hR2_2jwJ_WAxC1HiJoKB92Sfupv_1llL1vz04DKRivr-vxPtpQwvQ/exec"
).json()

print(data[0])
