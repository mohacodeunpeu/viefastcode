import requests
import time
import config

def send_discord(offer):
    data = {
        "embeds": [{
            "title": f"💼 {offer.titre}",
            "url": offer.url,
            "color": 5814783,
            "fields": [
                {"name": "🏢 Entreprise", "value": offer.entreprise, "inline": True},
                {"name": "🌍 Pays", "value": offer.pays, "inline": True},
                {"name": "📅 Durée", "value": f"{offer.duree} mois", "inline": True},
            ],
            "footer": {"text": "Bot VIE"},
        }]
    }

    for i in range(3):
        try:
            requests.post(config.DISCORD_WEBHOOK_URL, json=data)
            time.sleep(1.2)
            return
        except:
            time.sleep(2 ** i)
