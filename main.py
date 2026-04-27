"""
Bot VIE — boucle principale.
Scrape toutes les 90-150 secondes (aléatoire), ne crashe jamais.
"""

import json
import logging
import logging.handlers
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import config
import discord_notif
import scraper


# ── Logging ──────────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=5 * 1024 * 1024,   # 5 Mo
            backupCount=3,
            encoding="utf-8",
        ),
    ]
    for h in handlers:
        h.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in handlers:
        root.addHandler(h)


logger = logging.getLogger(__name__)


# ── Persistance ───────────────────────────────────────────────────────────────────

def load_seen() -> dict[str, str]:
    """
    Charge les offres déjà vues depuis seen_offers.json.
    Format : { "id_offre": "2026-04-27 13:00:00", ... }
    """
    path = Path(config.SEEN_FILE)
    if not path.exists():
        path.write_text("{}", encoding="utf-8")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Compatibilité avec l'ancien format liste
        if isinstance(data, list):
            return {str(oid): "unknown" for oid in data}
        return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        logger.warning(f"Impossible de lire {config.SEEN_FILE}: {e} — démarrage à vide")
        return {}


def save_seen(seen: dict[str, str]) -> None:
    try:
        Path(config.SEEN_FILE).write_text(
            json.dumps(seen, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error(f"Impossible de sauvegarder {config.SEEN_FILE}: {e}")


# ── Boucle principale ─────────────────────────────────────────────────────────────

def run() -> None:
    setup_logging()

    logger.info("=" * 60)
    logger.info("Bot VIE Ultra-Rapide démarré")
    logger.info(f"Intervalle : {config.MIN_INTERVAL}-{config.MAX_INTERVAL}s (aléatoire)")
    logger.info(f"Filtres actifs :")
    logger.info(f"  Zones    : {config.ZONES_SOUHAITEES or 'toutes'}")
    logger.info(f"  Pays     : {config.PAYS_SOUHAITES  or 'tous'}")
    logger.info(f"  Salaire  : >={config.SALAIRE_MIN} €" if config.SALAIRE_MIN else "  Salaire  : pas de filtre")
    logger.info(f"  Durée    : {config.DUREE_MIN or '?'}-{config.DUREE_MAX or '?'} mois")
    logger.info(f"  Keywords : {config.KEYWORDS_TITRE or 'tous'}")
    logger.info("=" * 60)

    discord_notif.send_startup()

    seen: dict[str, str] = load_seen()
    logger.info(f"IDs déjà connus : {len(seen)}")

    cycle = 0

    while True:
        cycle += 1
        t_start = time.time()
        now_str = datetime.now().strftime("%H:%M:%S")
        logger.info(f"── Cycle #{cycle} @ {now_str} ──")

        try:
            offers = scraper.fetch_offers()
            new_offers = [o for o in offers if o.id not in seen]

            logger.info(
                f"Cycle #{cycle} : {len(offers)} offres récupérées, "
                f"{len(new_offers)} nouvelles"
            )

            sent = 0
            for offer in new_offers:
                if discord_notif.send_offer(offer):
                    seen[offer.id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sent += 1
                    save_seen(seen)   # Sauvegarde immédiate après chaque envoi réussi

            elapsed = round(time.time() - t_start, 1)
            logger.info(
                f"Cycle #{cycle} terminé en {elapsed}s — "
                f"{sent} offre(s) envoyée(s) | "
                f"{len(seen)} offres vues au total"
            )

        except KeyboardInterrupt:
            logger.info("Arrêt demandé (Ctrl+C)")
            break

        except Exception as exc:
            logger.error(f"Erreur inattendue cycle #{cycle}: {exc}", exc_info=True)
            logger.info("Attente 60s avant de reprendre…")
            try:
                time.sleep(60)
            except KeyboardInterrupt:
                break
            continue

        # Intervalle aléatoire anti-ban
        wait = random.uniform(config.MIN_INTERVAL, config.MAX_INTERVAL)
        logger.info(f"Prochain cycle dans {wait:.0f}s…")
        try:
            time.sleep(wait)
        except KeyboardInterrupt:
            logger.info("Arrêt demandé (Ctrl+C)")
            break

    logger.info("Bot arrêté proprement.")


if __name__ == "__main__":
    run()
