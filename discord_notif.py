"""
Notifications Discord via webhook — embeds enrichis.
"""

import logging
import time
from datetime import datetime, timezone

import requests

import config
from scraper import Offer

logger = logging.getLogger(__name__)

EMBED_COLOR = 5814783   # Violet/indigo
COLOR_GREEN = 5763719   # Vert démarrage
COLOR_RED   = 15548997  # Rouge erreur


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _fmt_salary(amount: float) -> str:
    if not amount:
        return "Non précisé"
    return f"{int(amount):,} €/mois".replace(",", " ")


def _fmt_duration(months: int) -> str:
    if not months:
        return "N/A"
    return f"{months} mois"


def _val(s: str) -> str:
    return s if s and s != "N/A" else "—"


# ── Construction embed ───────────────────────────────────────────────────────────

def _build_embed(offer: Offer) -> dict:
    fields = [
        {"name": "🏢 Entreprise",  "value": _val(offer.entreprise),           "inline": True},
        {"name": "📅 Durée",        "value": _fmt_duration(offer.duree),       "inline": True},
        {"name": "🏙️ Ville",       "value": _val(offer.ville),                "inline": True},
        {"name": "🌍 Pays",         "value": _val(offer.pays),                 "inline": True},
        {"name": "💰 Indemnité",    "value": _fmt_salary(offer.salaire),       "inline": True},
        {"name": "🚀 Début",        "value": _val(offer.date_debut),           "inline": True},
        {"name": "🏁 Fin",          "value": _val(offer.date_fin),             "inline": True},
        {"name": "🗺️ Zone",        "value": _val(offer.zone_geographique),    "inline": True},
        {"name": "📆 Publié",       "value": _val(offer.date_publication),     "inline": True},
    ]

    embed: dict = {
        "title":       f"💼 {offer.titre}",
        "color":       EMBED_COLOR,
        "url":         offer.url,
        "thumbnail":   {"url": "https://i.imgur.com/VIEbot.png"},
        "description": f"🔗 [**Voir l'offre complète sur Business France**]({offer.url})",
        "fields":      fields,
        "footer":      {"text": "🇫🇷 Alerte VIE • Business France • Mise à jour toutes les 2 min"},
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
    return embed


# ── Envoi webhook ────────────────────────────────────────────────────────────────

def _post(payload: dict, retries: int = 3) -> bool:
    """POST JSON sur le webhook Discord avec retry et backoff (1s, 2s, 4s)."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                config.DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10,
            )

            if resp.status_code in (200, 204):
                return True

            # Rate limit Discord
            if resp.status_code == 429:
                try:
                    retry_after = float(resp.json().get("retry_after", 5))
                except Exception:
                    retry_after = 5.0
                logger.warning(f"Rate limit Discord — attente {retry_after:.1f}s")
                time.sleep(retry_after)
                continue

            logger.warning(
                f"Discord HTTP {resp.status_code} "
                f"(tentative {attempt}/{retries}): {resp.text[:150]}"
            )

        except requests.RequestException as e:
            logger.warning(f"Erreur webhook (tentative {attempt}/{retries}): {e}")

        if attempt < retries:
            time.sleep(2 ** (attempt - 1))  # 1s → 2s → 4s

    return False


def send_offer(offer: Offer) -> bool:
    """
    Envoie une offre VIE sur Discord.
    Ajoute @everyone si l'offre matche un keyword profil.
    Retourne True si succès.
    """
    payload: dict = {"embeds": [_build_embed(offer)]}

    # Mention @everyone si keyword profil matché
    if offer.keyword_match:
        payload["content"] = "@everyone 🔥 Offre qui correspond à ton profil !"

    ok = _post(payload)

    if ok:
        logger.info(f"Envoye : [{offer.id}] {offer.titre[:55]}")
    else:
        logger.error(f"Echec  : [{offer.id}] {offer.titre[:55]}")

    # Pause anti-rate-limit entre les messages
    time.sleep(1.5)
    return ok


def send_startup() -> None:
    """Message de démarrage dans le canal Discord."""
    payload = {
        "embeds": [{
            "title":       "✅ Bot VIE démarré !",
            "color":       COLOR_GREEN,
            "description": (
                "Je surveille les nouvelles offres VIE sur Business France.\n"
                "Mise à jour toutes les **2 minutes** environ."
            ),
            "footer":    {"text": "🇫🇷 Alerte VIE • Business France"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }
    try:
        resp = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            logger.info("Message de demarrage envoye sur Discord")
        else:
            logger.warning(f"Demarrage Discord HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"Impossible d'envoyer le message de demarrage: {e}")
