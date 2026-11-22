# Tracker Leboncoin - Xbox Series S

Alerte dès qu'une annonce Xbox Series S (100-220 €, livraison possible) est publiée.
Vérifie toutes les ~8 s, donc bien avant les notifications Leboncoin.

## Lancer (sur ton PC, connexion maison)
    pip install -r requirements.txt
    NTFY_TOPIC=un-nom-secret-unique python tracker.py

- **Push téléphone** : installe l'appli *ntfy*, abonne-toi au topic choisi. Le tap ouvre l'annonce directement.
- Ou Telegram : `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`.
- Le premier lancement ignore les annonces déjà en ligne.
- Réglages (prix, mots exclus, délai) en haut de `tracker.py`.

## Limites
Leboncoin protège son API (DataDome). Lance-le depuis ta connexion perso, pas depuis un serveur/VPN.
En cas d'erreur 403 répétée, laisse un peu de temps ou augmente `POLL_SECONDS`.
Le code n'a pas pu être testé en réel depuis l'environnement de développement : dis-moi ce que ça affiche au 1er lancement.

## Version navigateur (si le script renvoie 403)
    pip3 install -r requirements.txt
    python3 -m playwright install chromium
    NTFY_TOPIC=ton-topic python3 tracker_browser.py
Une fenêtre Chromium s'ouvre et recharge la recherche. Laisse-la ouverte (tu peux la mettre en arrière-plan).
