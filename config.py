# ── Webhook Discord ────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1498293144863903886/tYUYXnNqqB7Myc9nZ_6fnjcAHiazgijciPJFzCYH6oszhb31yfp1F1H-1WyXMD0cdyYp"

# ── Timing (intervalle aléatoire pour éviter le bannissement IP) ────────────────
MIN_INTERVAL = 90    # secondes minimum entre chaque cycle
MAX_INTERVAL = 150   # secondes maximum

# ── Fichiers locaux ─────────────────────────────────────────────────────────────
SEEN_FILE = "seen_offers.json"
LOG_FILE  = "bot.log"

# ── URLs ────────────────────────────────────────────────────────────────────────
BASE_URL = "https://mon-vie-via.businessfrance.fr"
API_URL  = "https://mon-vie-via.businessfrance.fr/api/offres/recherche"
HTML_URL = "https://mon-vie-via.businessfrance.fr/offres/recherche"

# ── Paramètres API ──────────────────────────────────────────────────────────────
PARAMS = {
    "missionsTypesIds": "VIE",
    "page": 0,
    "size": 100,
}

# ══════════════════════════════════════════════════════════════════════════════
#  FILTRES PROFIL
#  Laisser [] ou 0 pour désactiver un filtre et tout recevoir.
# ══════════════════════════════════════════════════════════════════════════════

# Zones géographiques souhaitées (insensible à la casse)
# Ex : ["EUROPE", "AMERIQUE DU NORD", "ASIE PACIFIQUE"]
ZONES_SOUHAITEES: list[str] = []

# Pays souhaités (insensible à la casse)
# Ex : ["ALLEMAGNE", "ESPAGNE", "ETATS-UNIS", "SINGAPOUR"]
PAYS_SOUHAITES: list[str] = []

# Indemnité mensuelle minimum en € (0 = pas de filtre)
SALAIRE_MIN: float = 0

# Durée minimum en mois (0 = pas de filtre)
DUREE_MIN: int = 0

# Durée maximum en mois (0 = pas de filtre)
DUREE_MAX: int = 0

# Mots-clés à chercher dans le titre — au moins un suffit pour matcher
# Ex : ["finance", "audit", "analyste", "comptable", "contrôle de gestion"]
# Si [] → toutes les offres sont envoyées
KEYWORDS_TITRE: list[str] = []

# Mots-clés à EXCLURE du titre ([] = aucune exclusion)
# Ex : ["stage", "alternance"]
KEYWORDS_EXCLUS: list[str] = []
