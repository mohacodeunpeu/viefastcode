"""
Scraper Business France — offres VIE.

Cascade :
  1. API JSON (avec Bearer token si token_cache.json existe)
  2. Extraction état Nuxt embarqué dans le HTML
  3. BeautifulSoup sur les cartes visibles
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

# ── Headers HTTP ────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://mon-vie-via.businessfrance.fr/",
    "Origin":          "https://mon-vie-via.businessfrance.fr",
    "Connection":      "keep-alive",
}

TOKEN_CACHE = Path("token_cache.json")


# ── Dataclass Offre ─────────────────────────────────────────────────────────────

@dataclass
class Offer:
    id:                str
    titre:             str
    entreprise:        str
    duree:             int          # mois
    ville:             str
    pays:              str
    zone_geographique: str
    salaire:           float
    date_debut:        str          # JJ/MM/AAAA
    date_fin:          str          # JJ/MM/AAAA
    date_publication:  str          # JJ/MM/AAAA HH:MM
    description:       str
    keyword_match:     bool = field(default=False, repr=False)

    @property
    def url(self) -> str:
        return f"{config.BASE_URL}/offres/{self.id}"


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _str(val, default: str = "N/A") -> str:
    """Convertit proprement une valeur en string non vide."""
    s = str(val).strip() if val is not None else ""
    return s if s and s.lower() not in ("none", "null", "nan") else default


def _int(val, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _float(val, default: float = 0.0) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        for k in ("montant", "value", "amount", "net", "total"):
            if val.get(k) is not None:
                return _float(val[k])
        return default
    try:
        cleaned = re.sub(r"[^\d.,]", "", str(val)).replace(",", ".")
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def _parse_date(raw, include_time: bool = False) -> str:
    """Normalise n'importe quel format de date → JJ/MM/AAAA [HH:MM]."""
    if not raw:
        return "N/A"
    s = str(raw).strip()
    # Timestamp millisecondes
    if s.isdigit() and len(s) >= 10:
        try:
            from datetime import datetime
            ts = int(s) / (1000 if len(s) == 13 else 1)
            dt = datetime.utcfromtimestamp(ts)
            if include_time:
                return dt.strftime("%d/%m/%Y %H:%M")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            pass
    # ISO 8601 (avec ou sans T)
    if "T" in s:
        date_part, _, time_part = s.partition("T")
        time_part = time_part[:5]
    elif " " in s and len(s) > 10:
        date_part, _, time_part = s.partition(" ")
        time_part = time_part[:5]
    else:
        date_part, time_part = s, ""
    # YYYY-MM-DD → JJ/MM/AAAA
    parts = re.split(r"[-/]", date_part)
    if len(parts) == 3:
        y, m, d = (parts[0], parts[1], parts[2]) if len(parts[0]) == 4 else (parts[2], parts[1], parts[0])
        base = f"{d.zfill(2)}/{m.zfill(2)}/{y}"
        return f"{base} {time_part}" if include_time and time_part else base
    return s or "N/A"


# ── Filtre profil ────────────────────────────────────────────────────────────────

def is_relevant(offer: Offer) -> bool:
    """
    Vérifie si une offre correspond au profil défini dans config.py.
    Retourne True si l'offre doit être envoyée sur Discord.
    """
    titre_lower = offer.titre.lower()

    # Mots-clés exclus → rejeter immédiatement
    for kw in config.KEYWORDS_EXCLUS:
        if kw.lower() in titre_lower:
            logger.debug(f"Offre [{offer.id}] exclue (mot-clé '{kw}')")
            return False

    # Filtre zones géographiques
    if config.ZONES_SOUHAITEES:
        zone_lower = offer.zone_geographique.lower()
        if not any(z.lower() in zone_lower for z in config.ZONES_SOUHAITEES):
            return False

    # Filtre pays
    if config.PAYS_SOUHAITES:
        pays_lower = offer.pays.lower()
        if not any(p.lower() in pays_lower for p in config.PAYS_SOUHAITES):
            return False

    # Filtre salaire minimum
    if config.SALAIRE_MIN and offer.salaire and offer.salaire < config.SALAIRE_MIN:
        return False

    # Filtre durée minimum
    if config.DUREE_MIN and offer.duree and offer.duree < config.DUREE_MIN:
        return False

    # Filtre durée maximum
    if config.DUREE_MAX and offer.duree and offer.duree > config.DUREE_MAX:
        return False

    # Mots-clés titre → au moins un doit matcher
    if config.KEYWORDS_TITRE:
        matched = any(kw.lower() in titre_lower for kw in config.KEYWORDS_TITRE)
        offer.keyword_match = matched
        if not matched:
            return False
    else:
        offer.keyword_match = False

    return True


# ── Session HTTP ────────────────────────────────────────────────────────────────

def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    # Charger le token Bearer si disponible (généré par login.py)
    if TOKEN_CACHE.exists():
        try:
            cache = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
            token = cache.get("access_token", "")
            if token and token.startswith("ey"):
                session.headers["Authorization"] = f"Bearer {token}"
                logger.info("Token Bearer chargé depuis token_cache.json")
        except Exception:
            pass
    return session


def _get(session: requests.Session, url: str,
         params: dict = None, retries: int = 3) -> Optional[requests.Response]:
    """GET avec retry exponentiel."""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, timeout=15)
            return resp
        except requests.Timeout:
            logger.warning(f"Timeout {url} (tentative {attempt}/{retries})")
        except requests.ConnectionError as e:
            logger.warning(f"Connexion échouée {url}: {e} (tentative {attempt}/{retries})")
        except requests.RequestException as e:
            logger.error(f"Erreur requête: {e}")
            break
        if attempt < retries:
            time.sleep(2 ** attempt)
    return None


# ── Parsing d'un dict brut → Offer ─────────────────────────────────────────────

def _parse_raw(raw: dict) -> Optional[Offer]:
    try:
        offer_id = _str(
            raw.get("id") or raw.get("offreId") or raw.get("offerId") or
            raw.get("reference") or raw.get("ref"), ""
        )
        if not offer_id:
            return None

        titre = _str(
            raw.get("intitule") or raw.get("title") or raw.get("libelle") or
            raw.get("poste") or raw.get("titreFrancais"), "Poste non précisé"
        )

        # Entreprise
        ent = raw.get("entreprise") or raw.get("company") or raw.get("societe") or {}
        if isinstance(ent, dict):
            entreprise = _str(
                ent.get("raisonSociale") or ent.get("nom") or ent.get("name") or
                ent.get("libelle"), raw.get("entrepriseLibelle", "N/A")
            )
        else:
            entreprise = _str(ent or raw.get("entrepriseLibelle"), "N/A")

        # Localisation
        loc = raw.get("localisation") or raw.get("lieu") or raw.get("location") or {}
        if isinstance(loc, dict):
            ville = _str(loc.get("ville") or loc.get("city") or loc.get("commune") or raw.get("ville"), "N/A")
            pays  = _str(loc.get("pays") or loc.get("country") or loc.get("libellePays") or raw.get("pays"), "N/A")
            zone  = _str(
                loc.get("zoneGeographique") or loc.get("zone") or
                raw.get("zoneGeographique") or raw.get("zone") or
                raw.get("continentLibelle"), "N/A"
            )
        else:
            ville = _str(raw.get("ville") or raw.get("city"), "N/A")
            pays  = _str(raw.get("pays") or raw.get("country") or raw.get("libellePays"), "N/A")
            zone  = _str(raw.get("zoneGeographique") or raw.get("zone") or raw.get("continentLibelle"), "N/A")

        duree   = _int(raw.get("duree") or raw.get("dureeMission") or raw.get("duration") or raw.get("nbMois"))
        salaire = _float(raw.get("salaire") or raw.get("remunerationMensuelle") or raw.get("remuneration") or raw.get("salary") or raw.get("indemnite"))

        date_debut = _parse_date(raw.get("dateDebut") or raw.get("startDate") or raw.get("dateDebutMission") or raw.get("debut"))
        date_fin   = _parse_date(raw.get("dateFin")   or raw.get("endDate")   or raw.get("dateFinCandidature") or raw.get("fin") or raw.get("dateLimite"))
        date_pub   = _parse_date(raw.get("datePublication") or raw.get("publishedAt") or raw.get("createdAt") or raw.get("dateCreation"), include_time=True)

        description = _str(
            raw.get("description") or raw.get("descriptif") or
            raw.get("resume") or raw.get("summary"), "N/A"
        )
        # Tronquer la description si trop longue
        if len(description) > 500:
            description = description[:497] + "…"

        return Offer(
            id=offer_id,
            titre=titre,
            entreprise=entreprise,
            duree=duree,
            ville=ville,
            pays=pays,
            zone_geographique=zone,
            salaire=salaire,
            date_debut=date_debut,
            date_fin=date_fin,
            date_publication=date_pub,
            description=description,
        )
    except Exception as e:
        logger.debug(f"Parsing échoué id={raw.get('id','?')}: {e}")
        return None


# ── Stratégie 1 : API JSON ───────────────────────────────────────────────────────

def _fetch_api(session: requests.Session) -> list[Offer]:
    logger.info(f"[API] {config.API_URL}")
    resp = _get(session, config.API_URL, params=config.PARAMS)
    if not resp:
        return []

    if resp.status_code in (401, 403, 500):
        try:
            msg = resp.json().get("message", resp.text[:80])
        except Exception:
            msg = resp.text[:80]
        logger.warning(f"[API] HTTP {resp.status_code}: {msg} → fallback HTML")
        return []

    if resp.status_code != 200:
        logger.warning(f"[API] HTTP {resp.status_code} inattendu")
        return []

    try:
        data = resp.json()
    except ValueError:
        logger.error("[API] Réponse non-JSON")
        return []

    # Normaliser les structures de réponse possibles
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = (
            data.get("content") or data.get("offres") or data.get("results") or
            data.get("data")    or data.get("items")  or data.get("list")    or
            data.get("_embedded", {}).get("offres", []) or []
        )
        total = data.get("totalElements") or data.get("total") or len(items)
        logger.info(f"[API] {len(items)}/{total} offres reçues")
    else:
        logger.warning(f"[API] Structure inconnue: {type(data)}")
        return []

    offers = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        offer = _parse_raw(raw)
        if offer and is_relevant(offer):
            offers.append(offer)

    logger.info(f"[API] {len(offers)} offres après filtres")
    return offers


# ── Stratégie 2 : HTML Nuxt ─────────────────────────────────────────────────────

def _dig_for_offers(node, depth: int = 0) -> list[dict]:
    """Parcours récursif pour trouver une liste d'offres dans un dict Nuxt."""
    if depth > 7:
        return []
    if isinstance(node, list) and node:
        if isinstance(node[0], dict) and any(
            node[0].get(k)
            for k in ("id", "offreId", "intitule", "title", "entreprise")
        ):
            return node
        for item in node:
            found = _dig_for_offers(item, depth + 1)
            if found:
                return found
    elif isinstance(node, dict):
        for key in ("content", "offres", "results", "data", "items", "list",
                    "offers", "missions", "annonces"):
            val = node.get(key)
            if isinstance(val, list) and val:
                found = _dig_for_offers(val, depth + 1)
                if found:
                    return found
        for val in node.values():
            if isinstance(val, (dict, list)):
                found = _dig_for_offers(val, depth + 1)
                if found:
                    return found
    return []


def _extract_nuxt_items(html: str) -> list[dict]:
    """Extrait les données embarquées par Nuxt/SSR depuis le HTML."""
    soup = BeautifulSoup(html, "lxml")

    # Nuxt 3 : <script id="__NUXT_DATA__" type="application/json">
    for tag in soup.find_all("script", {"type": "application/json"}):
        try:
            data = json.loads(tag.string or "")
            found = _dig_for_offers(data)
            if found:
                return found
        except Exception:
            continue

    # Nuxt 2 : window.__NUXT__ = {...}
    for script in soup.find_all("script"):
        text = script.string or ""
        if "__NUXT__" not in text:
            continue
        # Extraire l'objet JSON après le signe égal
        m = re.search(r"__NUXT__\s*=\s*(\{.*)", text, re.DOTALL)
        if m:
            # Nettoyer les éventuels caractères JS après la fermeture
            candidate = m.group(1).strip().rstrip(";")
            # Chercher le JSON valide le plus long possible
            for end in range(len(candidate), 0, -1):
                try:
                    data = json.loads(candidate[:end])
                    found = _dig_for_offers(data)
                    if found:
                        return found
                    break
                except json.JSONDecodeError:
                    continue

    return []


def _fetch_html(session: requests.Session) -> list[Offer]:
    logger.info(f"[HTML] {config.HTML_URL}")
    resp = _get(session, config.HTML_URL)
    if not resp or resp.status_code != 200:
        logger.error("[HTML] Impossible de charger la page")
        return []

    html = resp.text

    # Tentative Nuxt embarqué
    items = _extract_nuxt_items(html)
    if items:
        logger.info(f"[HTML/Nuxt] {len(items)} items bruts")
        offers = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            offer = _parse_raw(raw)
            if offer and is_relevant(offer):
                offers.append(offer)
        if offers:
            logger.info(f"[HTML/Nuxt] {len(offers)} offres après filtres")
            return offers

    # Tentative JSON-LD
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            items = (
                data if isinstance(data, list) else
                data.get("itemListElement") or data.get("offers") or []
            )
            offers = []
            for raw in items:
                if not isinstance(raw, dict):
                    continue
                offer = _parse_raw(raw)
                if offer and is_relevant(offer):
                    offers.append(offer)
            if offers:
                logger.info(f"[HTML/JSON-LD] {len(offers)} offres")
                return offers
        except Exception:
            continue

    # Tentative CSS
    selectors = [
        "[data-id]", "[data-offre-id]", "[data-offer-id]",
        "article.offer", ".offer-card", ".job-card", ".offre-item",
        "[class*='offer']", "[class*='offre']",
    ]
    for sel in selectors:
        cards = soup.select(sel)
        if not cards:
            continue
        logger.info(f"[HTML/CSS] {len(cards)} cartes ('{sel}')")
        offers = []
        for card in cards:
            raw = _card_to_dict(card)
            if raw:
                offer = _parse_raw(raw)
                if offer and is_relevant(offer):
                    offers.append(offer)
        if offers:
            return offers

    logger.warning("[HTML] Aucune offre trouvée — site probablement rendu côté client uniquement")
    return []


def _card_to_dict(tag) -> Optional[dict]:
    try:
        raw: dict = {}
        for attr in ("data-id", "data-offre-id", "data-offer-id"):
            val = (tag.get(attr) or "").strip()
            if val:
                raw["id"] = val
                break
        if not raw.get("id"):
            m = re.search(r"\d{4,}", tag.get("id", ""))
            if m:
                raw["id"] = m.group()
        if not raw.get("id"):
            return None

        for sel in ("h1", "h2", "h3", ".title", "[class*='title']", "[class*='intitule']"):
            el = tag.select_one(sel)
            if el:
                raw["intitule"] = el.get_text(strip=True)
                break

        for sel in (".company", ".entreprise", "[class*='company']", "[class*='entreprise']"):
            el = tag.select_one(sel)
            if el:
                raw["entreprise"] = {"raisonSociale": el.get_text(strip=True)}
                break

        for sel in (".location", ".localisation", "[class*='location']", "[class*='pays']"):
            el = tag.select_one(sel)
            if el:
                parts = [p.strip() for p in el.get_text(strip=True).split(",")]
                raw["localisation"] = {
                    "ville": parts[0] if len(parts) >= 2 else "N/A",
                    "pays":  parts[-1],
                }
                break

        return raw if raw.get("intitule") else None
    except Exception:
        return None


# ── Point d'entrée ───────────────────────────────────────────────────────────────

def fetch_offers() -> list[Offer]:
    """
    Récupère toutes les offres VIE filtrées selon le profil config.py.
    Cascade : API JSON → HTML Nuxt → HTML BeautifulSoup.
    """
    session = _build_session()

    # Pré-requête pour obtenir les cookies de session
    try:
        _get(session, config.BASE_URL)
    except Exception:
        pass

    offers = _fetch_api(session)
    if offers:
        return offers

    return _fetch_html(session)
