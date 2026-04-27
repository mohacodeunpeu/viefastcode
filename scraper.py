import requests
import random
import time
import logging
from dataclasses import dataclass

import config

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/121.0",
]

@dataclass
class Offer:
    id: str
    titre: str
    entreprise: str
    duree: int
    ville: str
    pays: str
    zone_geographique: str
    salaire: float
    date_debut: str
    date_fin: str
    date_publication: str
    description: str

    @property
    def url(self):
        return f"{config.BASE_URL}/offres/{self.id}"

def build_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Referer": config.BASE_URL
    })
    return s

def is_relevant(o):
    titre = o.titre.lower()

    for kw in config.KEYWORDS_EXCLUS:
        if kw.lower() in titre:
            return False

    if config.KEYWORDS_TITRE:
        if not any(k.lower() in titre for k in config.KEYWORDS_TITRE):
            return False

    return True

def fetch_offers():
    session = build_session()

    all_items = []

    for page in range(0, 3):
        params = config.PARAMS.copy()
        params["page"] = page

        try:
            r = session.get(config.API_URL, params=params, timeout=10)
            print("STATUS:", r.status_code)

            if r.status_code != 200:
                continue

            data = r.json()
            items = data.get("content", [])

            print(f"PAGE {page}: {len(items)}")

            all_items.extend(items)

            time.sleep(1)

        except Exception as e:
            print("ERROR API:", e)

    print("TOTAL:", len(all_items))

    offers = []

    for o in all_items:
        try:
            offer = Offer(
                id=str(o.get("id") or o.get("reference") or hash(str(o))),
                titre=o.get("intitule") or "N/A",
                entreprise=str(o.get("entreprise", {}).get("nom") if isinstance(o.get("entreprise"), dict) else "N/A"),
                duree=int(o.get("duree") or 0),
                ville=str(o.get("ville") or "N/A"),
                pays=str(o.get("pays") or "N/A"),
                zone_geographique=str(o.get("zoneGeographique") or "N/A"),
                salaire=float(o.get("salaire") or 0),
                date_debut=str(o.get("dateDebut") or "N/A"),
                date_fin=str(o.get("dateFin") or "N/A"),
                date_publication=str(o.get("datePublication") or "N/A"),
                description=str(o.get("description") or "N/A"),
            )

            if is_relevant(offer):
                offers.append(offer)

        except:
            continue

    print("VALIDES:", len(offers))

    return offers
