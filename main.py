import time
import json
import random
import logging

import config
from scraper import fetch_offers
from discord_notif import send_discord

logging.basicConfig(level=logging.INFO)

try:
    with open(config.SEEN_FILE) as f:
        seen = set(json.load(f))
except:
    seen = set()

print("BOT LANCÉ")

while True:
    try:
        offers = fetch_offers()

        new = 0

        for o in offers:
            uid = f"{o.id}_{o.date_publication}"

            if uid not in seen:
                send_discord(o)
                seen.add(uid)
                new += 1

        with open(config.SEEN_FILE, "w") as f:
            json.dump(list(seen), f)

        print(f"NOUVELLES: {new}")

        time.sleep(random.uniform(config.MIN_INTERVAL, config.MAX_INTERVAL))

    except Exception as e:
        print("ERROR MAIN:", e)
        time.sleep(60)
