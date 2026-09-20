"""
Transform TRMNL — runtime serverless, langage Python.

Tourne sur les serveurs TRMNL à CHAQUE rafraîchissement. C'est ici que vit le
hasard : aucun cron, aucun « écran du jour ». L'utilisateur règle son appareil
sur 5 minutes et obtient un écran différent à chaque fois.

Le polling va chercher l'INDEX correspondant aux choix de l'utilisateur :

    https://nbbou81000.github.io/Ngram/api/index-{{ mode }}-{{ langue }}.json

Cet index arrive ici dans `input`. Le transform n'a donc besoin d'aucun accès
aux réglages du plugin : tout ce qu'il lui faut est déjà dans la réponse.

  - index d'un mode      -> {"base": "...", "ecrans": [...]}  : on tire un écran
  - index de rotation    -> {"modes": [...]}                  : on tire d'abord
                                                                le mode
"""
import random

import requests

RACINE = "https://nbbou81000.github.io/Ngram/api"
DELAI = 10


def _json(url):
    r = requests.get(url, timeout=DELAI)
    r.raise_for_status()
    return r.json()


def run(input):
    donnees = input if isinstance(input, dict) else {}
    try:
        langue = donnees.get("langue", "en")

        # rotation : l'index ne liste pas des écrans mais des modes
        if "modes" in donnees and not donnees.get("ecrans"):
            modes = donnees.get("modes") or []
            if not modes:
                return {"erreur": "aucun mode disponible"}
            mode = random.choice(modes)
            donnees = _json(f"{RACINE}/index-{mode}-{langue}.json")

        ecrans = donnees.get("ecrans") or []
        if not ecrans:
            return {"erreur": "index vide ou illisible"}

        # tirage indépendant à chaque appel : deux rafraîchissements de suite
        # peuvent retomber sur le même écran, c'est rare sur plusieurs centaines
        choisi = random.choice(ecrans)
        ecran = _json(f"{RACINE}/{donnees['base']}/{choisi}.json")
        ecran["slug"] = choisi
        ecran["total"] = len(ecrans)
        return ecran

    except Exception as e:
        # un message propre vaut mieux qu'un écran cassé
        return {"erreur": str(e)[:200]}
