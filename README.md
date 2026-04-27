# 🤖 Bot VIE Alert — Business France

Bot Python automatisé qui détecte et envoie en temps réel les nouvelles offres **VIE (Volontariat International en Entreprise)** depuis Business France vers Discord.

---

## 🚀 Fonctionnalités

* 🔎 Scraping automatique des offres VIE
* ⚡ Détection rapide des nouvelles offres (toutes les 30–60 secondes)
* 📩 Notifications Discord via webhook
* 🧠 Filtrage intelligent (mots-clés, pays, salaire, durée)
* 🔁 Anti-duplication (ne renvoie jamais deux fois la même offre)
* 🔄 Rotation User-Agent (anti-blocage basique)
* 📊 Multi-pages (jusqu’à 300 offres analysées)

---

## 📁 Structure du projet

```
.
├── config.py              # Configuration générale
├── scraper.py             # Scraper Business France
├── discord_notif.py       # Envoi vers Discord
├── main.py                # Boucle principale
├── requirements.txt       # Dépendances
├── Procfile               # Railway worker
├── runtime.txt            # Version Python
├── seen_offers.json       # Stockage des offres déjà envoyées
└── bot.log                # Logs (si activé)
```

---

## ⚙️ Installation

### 1. Cloner le repo

```bash
git clone https://github.com/ton-repo/vie-bot.git
cd vie-bot
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

Dans `config.py` :

* Ajouter ton webhook Discord :

```python
DISCORD_WEBHOOK_URL = "TON_WEBHOOK"
```

* Modifier les filtres si besoin :

```python
KEYWORDS_TITRE = ["finance", "marketing"]
PAYS_SOUHAITES = ["ALLEMAGNE", "ESPAGNE"]
```

---

## ▶️ Lancer le bot

```bash
python main.py
```

---

## ☁️ Déploiement Railway

1. Push sur GitHub
2. Connecter le repo à **Railway**
3. Déployer automatiquement

Le bot démarre avec :

```
worker: python main.py
```

---

## 📡 Fonctionnement

1. Le bot interroge l’API Business France
2. Récupère les offres (jusqu’à 3 pages)
3. Filtre selon ton profil
4. Compare avec `seen_offers.json`
5. Envoie uniquement les nouvelles offres sur Discord

---

## 🧠 Anti-duplication

Chaque offre est identifiée par :

```
ID + date_publication
```

➡️ Permet de détecter :

* nouvelles offres
* offres repostées

---

## ⚠️ Problèmes possibles

### ❌ Aucune offre envoyée

* Vérifier `seen_offers.json`
* Vérifier filtres trop stricts

### ❌ STATUS 403

* API bloquée → changer User-Agent ou attendre

### ❌ Rien dans Discord

* Vérifier webhook

---

## 🔥 Améliorations possibles

* Scraping via navigateur (Playwright)
* Proxy rotation (anti-ban avancé)
* Analyse intelligente des offres
* Dashboard web

---

## 📜 Licence

Usage personnel / éducatif.

---

## 👨‍💻 Auteur

Projet optimisé pour performance et détection rapide des offres VIE.
