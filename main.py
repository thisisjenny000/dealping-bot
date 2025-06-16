import os
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)
#12
# Discord-Webhooks aus Umgebungsvariablen
WEBHOOKS = {
    "unter15": os.environ.get("WEBHOOK_UNTER15"),
    "all": os.environ.get("WEBHOOK_ALL"),
    "halfprice": os.environ.get("WEBHOOK_HALFPRICE"),
    "epic": os.environ.get("WEBHOOK_EPIC"),
}

# Filter-Regeln für jede Kategorie
FILTERS = {
    "unter15": lambda g: g["storeID"] == "1" and float(g["salePrice"]) < 15,
    "all": lambda g: g["storeID"] == "1",
    "halfprice": lambda g: g["storeID"] == "1" and float(g["savings"]) >= 50,
    "epic": lambda g: g["storeID"] == "25" and float(g["savings"]) >= 40,
}

# Dateinamen für gespeicherte Deal-Titel
LAST_FILES = {
    "unter15": "last_unter15.txt",
    "all": "last_all.txt",
    "halfprice": "last_half.txt",
    "epic": "last_epic.txt"
}

def fetch_deals():
    url = "https://www.cheapshark.com/api/1.0/deals?sortBy=Deal%20Rating&pageSize=20"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DealPingBot/1.0; +https://github.com/thisisjenny000/dealping-bot)"
    }
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("❌ Fehler beim Laden der Deals:", e)
        return []


def format_deals(deals):
    text = ""
    for g in deals:
        title = g["title"]
        price = g["salePrice"]
        normal = g["normalPrice"]
        store = g["storeID"]
        appid = g.get("steamAppID")
        if store == "1" and appid:  # Steam
            url = f"https://store.steampowered.com/app/{appid}"
        else:
            url = f"https://www.cheapshark.com/redirect?dealID={g['dealID']}"
        text += f"**{title}** – {price} € (statt {normal} €)\n{url}\n\n"
    return text

def load_last_titles(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return f.read().splitlines()

def save_titles(filename, titles):
    with open(filename, "w") as f:
        f.write("\n".join(titles))

def process_category(name):
    deals = fetch_deals()
    filtered = [g for g in deals if FILTERS[name](g)]
    titles = [g["title"] for g in filtered]
    last = load_last_titles(LAST_FILES[name])

    if titles != last:
        content = f"**Neue Angebote – {name.replace('-', ' ').capitalize()}**\n\n" + format_deals(filtered)
        if WEBHOOKS[name]:
            requests.post(WEBHOOKS[name], json={"content": content})
        save_titles(LAST_FILES[name], titles)
        print(f"✅ Neue Deals gepostet: {name}")
    else:
        print(f"ℹ️ Keine neuen Deals bei {name}.")

@app.route('/')
def home():
    return "DealPing-Bot läuft!"

def run_bot():
    for name in WEBHOOKS:
        if WEBHOOKS[name]:
            process_category(name)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8000)).start()
    run_bot()

