#!/usr/bin/env python3
"""Version navigateur : ouvre une vraie fenêtre Chromium sur la recherche Leboncoin,
la recharge toutes les ~12 s et alerte sur les nouvelles annonces (ntfy / Telegram / son).
Si un captcha apparaît, résous-le à la main une fois : la session est conservée dans ./profile
"""
import json, os, random, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import tracker  # réutilise notify(), EXCLUDE, save_seen()...

SEARCH = ("https://www.leboncoin.fr/recherche?text=xbox%20series%20s"
          "&price=100-220&shippable=1&sort=time&order=desc")
POLL = float(os.getenv("POLL_SECONDS", "12"))


def ads_from_page(page):
    raw = page.evaluate("() => document.getElementById('__NEXT_DATA__')?.textContent")
    if not raw:
        return None
    data = json.loads(raw)
    sd = data.get("props", {}).get("pageProps", {}).get("searchData") or {}
    return sd.get("ads", [])


def main():
    seen = tracker.load_seen()
    first = seen is None
    seen = seen or set()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(Path(__file__).with_name("profile")), headless=False,
            locale="fr-FR", viewport={"width": 1200, "height": 800})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print("Surveillance (navigateur) en cours. Ctrl+C pour arrêter.")
        while True:
            try:
                page.goto(SEARCH, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
                ads = ads_from_page(page)
                if ads is None:
                    print(time.strftime("%H:%M:%S"),
                          "page sans résultats (captcha ? résous-le dans la fenêtre)", flush=True)
                    time.sleep(10)
                    continue
                for ad in reversed(ads):
                    lid = str(ad["list_id"])
                    if lid in seen:
                        continue
                    seen.add(lid)
                    if first or tracker.EXCLUDE.search(ad.get("subject", "")):
                        continue
                    tracker.notify(ad)
                if first:
                    print(f"Initialisé ({len(ads)} annonces existantes ignorées).")
                    first = False
                tracker.save_seen(seen)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(time.strftime("%H:%M:%S"), "erreur:", e, file=sys.stderr, flush=True)
                time.sleep(10)
            time.sleep(POLL + random.uniform(-3, 3))
        ctx.close()


if __name__ == "__main__":
    main()
