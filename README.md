# 🤖 VIE Fast Bot

Bot Python qui détecte automatiquement les nouvelles offres **VIE (Business France)** et les envoie instantanément sur Discord.

---

## 🚀 Fonctionnalités

* ⚡ Détection rapide (30 à 60 secondes)
* 📡 Scraping multi-pages (jusqu’à 300 offres)
* 🔔 Notifications Discord automatiques
* 🧠 Filtrage personnalisé (mots-clés, pays, salaire…)
* 🔁 Anti-duplication intelligent
* 🛡️ Rotation User-Agent (anti-blocage)

---

## 📁 Structure

```
config.py
scraper.py
discord_notif.py
main.py
requirements.txt
Procfile
runtime.txt
seen_offers.json
```

---

## ⚙️ Installation

### 1. Cloner le repo

```bash
git clone https://github.com/mohacodeunpeu/viefastcode.git
cd viefastcode
```

---

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

Dans `config.py` :

### Webhook Discord

```python
DISCORD_WEBHOOK_URL = "TON_WEBHOOK"
```

### Filtres (optionnel)

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

1. Push le projet sur GitHub
2. Connecte-le à **Railway**
3. Déploiement automatique

Le bot démarre avec :

```
worker: python main.py
```

---

## 📡 Fonctionnement

1. Le bot scrape l’API Business France
2. Récupère plusieurs pages d’offres
3. Filtre selon ton profil
4. Compare avec `seen_offers.json`
5. Envoie uniquement les nouvelles offres sur Discord

---

## ⚠️ Problèmes courants

### Aucune offre envoyée

* Supprimer `seen_offers.json`
* Vérifier les filtres

### STATUS 403

* API temporairement bloquée
* Attendre ou relancer

### Rien sur Discord

* Vérifier le webhook

---

## 🧠 Optimisation

Pour plus de vitesse :

```python
MIN_INTERVAL = 30
MAX_INTERVAL = 60
```

---

## 👨‍💻 Objectif

Bot optimisé pour détecter les offres VIE plus rapidement que la majorité des bots classiques.

---
