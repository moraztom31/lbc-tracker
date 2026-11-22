#!/usr/bin/env python3
"""Tracker Leboncoin : Xbox Series S, 100-220 EUR, livraison possible.
Interroge la recherche toutes les ~8 s et alerte instantanément (ntfy / Telegram / son).

Config par variables d'environnement (toutes facultatives) :
  NTFY_TOPIC          nom de ton topic ntfy.sh (appli ntfy sur le téléphone) -> push immédiat
  TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID   alternative Telegram
  POLL_SECONDS        délai entre 2 requêtes (défaut 8)
"""
import json, os, random, re, sys, time
from pathlib import Path
import requests

QUERY = "xbox series s"
PRICE_MIN, PRICE_MAX = 100, 220
POLL = float(os.getenv("POLL_SECONDS", "8"))
SEEN_FILE = Path(__file__).with_name("seen.json")

# Titres à ignorer : autres modèles, accessoires, pièces, recherches
EXCLUDE = re.compile(r"series\s*x\b|\bone\b|\b360\b|manette seule|pour pi[eè]ces|hs\b|"
                     r"en panne|cherche|achat|jeu\b|jeux\b|housse|support|c[aâ]ble", re.I)

URL = "https://api.leboncoin.fr/finder/search"
HEADERS = {
    "api_key": "ba0c2dad52b3ec",  # clé publique utilisée par le site web
    "Content-Type": "application/json",
    "Origin": "https://www.leboncoin.fr",
    "Referer": "https://www.leboncoin.fr/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
}
PAYLOAD = {
    "limit": 35, "limit_alu": 0,
    "filters": {
        "enums": {"ad_type": ["offer"], "shippable": ["1"]},   # offres + livraison possible
        "keywords": {"text": QUERY},
        "ranges": {"price": {"min": PRICE_MIN, "max": PRICE_MAX}},
    },
    "sort_by": "time", "sort_order": "desc",
}


def load_seen():
    try:
        return set(json.loads(SEEN_FILE.read_text()))
    except Exception:
        return None  # None = premier lancement


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen)[-2000:]))


def fetch(session):
    r = session.post(URL, json=PAYLOAD, headers=HEADERS, timeout=10)
    if r.status_code in (403, 429):
        raise RuntimeError(f"bloqué par Leboncoin (HTTP {r.status_code})")
    r.raise_for_status()
    return r.json().get("ads", [])


def price_of(ad):
    p = ad.get("price") or []
    return p[0] if p else ad.get("price_cents", 0) / 100


def notify(ad):
    title = ad.get("subject", "?")
    price = price_of(ad)
    link = ad.get("url") or f"https://www.leboncoin.fr/ad/consoles/{ad['list_id']}"
    msg = f"{price} € - {title}\n{link}"
    print("\a\n🚨 NOUVELLE OFFRE :", msg, flush=True)
    topic = os.getenv("NTFY_TOPIC")
    if topic:
        try:
            requests.post(f"https://ntfy.sh/{topic}", data=msg.encode("utf-8"), timeout=8,
                          headers={"Title": "Xbox Series S", "Click": link,
                                   "Priority": "urgent", "Tags": "video_game"})
        except Exception as e:
            print("ntfy KO:", e)
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if tok and chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", timeout=8,
                          data={"chat_id": chat, "text": f"🚨 {msg}"})
        except Exception as e:
            print("telegram KO:", e)


def main():
    seen = load_seen()
    first = seen is None
    seen = seen or set()
    s = requests.Session()
    fails = 0
    print(f"Surveillance : '{QUERY}' {PRICE_MIN}-{PRICE_MAX} €, livraison. Ctrl+C pour arrêter.")
    while True:
        try:
            ads = fetch(s)
            fails = 0
            for ad in reversed(ads):  # du plus ancien au plus récent
                lid = str(ad["list_id"])
                if lid in seen:
                    continue
                seen.add(lid)
                if first or EXCLUDE.search(ad.get("subject", "")):
                    continue
                notify(ad)
            if first:
                print(f"Initialisé ({len(ads)} annonces existantes ignorées).")
                first = False
            save_seen(seen)
        except Exception as e:
            fails += 1
            print(time.strftime("%H:%M:%S"), "erreur:", e, file=sys.stderr, flush=True)
            time.sleep(min(60, 5 * fails))
        time.sleep(POLL + random.uniform(-2, 2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
