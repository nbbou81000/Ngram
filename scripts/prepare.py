#!/usr/bin/env python3
"""
Prépare les listes de candidats, un fichier par mode et par langue.

Séparé du générateur quotidien à dessein : cette étape est coûteuse (WordNet,
filtres qualité) et ne bouge que quand la récolte bouge. Le générateur, lui,
tourne tous les jours et ne fait que piocher dans ces listes.

Sortie : data/selection/<mode>-<langue>.json — une liste ordonnée, du meilleur
au moins bon, mélangée de façon déterministe pour que deux jours consécutifs ne
se ressemblent pas.

Usage : python scripts/prepare.py --lang fr
"""
import argparse, json, os, random, sys

import shapes

Y0 = 1800

# Mots parasites récurrents : noms propres non capitalisés dans le corpus,
# scories d'OCR, mots étrangers. La liste s'enrichit à l'usage.
PARASITES = {
    "fr": {"frank", "carter", "mark", "stone", "came", "japon", "indiens", "jésus",
           "normaux", "john", "george", "paul", "charles", "henry", "william"},
    "en": {"der", "und", "ing", "les", "des", "une", "est", "mme", "von"},
}


def utilisable(mot, forme, lang):
    """Filtres communs à tous les modes."""
    if mot in PARASITES.get(lang, ()):
        return False
    if len(mot) < 4:
        return False
    # le corpus est trop maigre avant 1825 : les sommets y sont des artefacts
    if forme["pic"] < 1825:
        return False
    if forme["max"] < 1.5:
        return False
    return True


def wordnet_connu(lang):
    """Renvoie un test d'appartenance à WordNet, ou un test toujours vrai si
    nltk n'est pas installé (le script reste utilisable sans)."""
    try:
        from nltk.corpus import wordnet as wn
        code = {"fr": "fra", "en": "eng"}[lang]
        wn.synsets("test", lang=code)          # force le chargement

        def connu(mot):
            try:
                return bool(wn.synsets(mot, lang=code))
            except Exception:
                return False
        return connu
    except Exception:
        print("  (nltk absent : filtre WordNet désactivé)", file=sys.stderr)
        return lambda mot: True


def prepare(lang, data_dir, out_dir):
    lex = shapes.load(lang, data_dir)
    connu = wordnet_connu(lang)
    print(f"[{lang}] {len(lex)} mots chargés")

    listes = {"oublie": [], "naissance": [], "resurrection": []}
    millesimes = {}

    for mot, serie in lex.items():
        f = shapes.classe(serie)
        if not f or not utilisable(mot, f, lang):
            continue
        if not connu(mot):
            continue

        if f["forme"] == "cloche":
            listes["oublie"].append({"mot": mot, "note": f["note"], "pic": f["pic"]})
        elif f["forme"] == "decollage" and f["naissance"]:
            listes["naissance"].append({"mot": mot, "note": f["note"],
                                        "naissance": f["naissance"]})
            millesimes.setdefault(f["naissance"], []).append((mot, f["max"]))
        elif f["forme"] == "resurrection":
            listes["resurrection"].append({"mot": mot, "note": f["note"],
                                           "creux": f["creux"]})

    # millésimes : on ne garde que les années offrant assez de mots pour remplir
    # la grille de six
    listes["millesime"] = [
        {"annee": an, "note": len(mots),
         "mots": [m for m, _ in sorted(mots, key=lambda x: -x[1])[:6]]}
        for an, mots in sorted(millesimes.items()) if len(mots) >= 4
    ]

    os.makedirs(out_dir, exist_ok=True)
    for mode, items in listes.items():
        items.sort(key=lambda r: -r["note"])
        # on coupe la queue : le bas du classement, c'est du bruit
        garde = items[:max(40, int(len(items) * 0.75))]
        # mélange déterministe : l'ordre ne changera pas d'une exécution à
        # l'autre, mais deux jours de suite ne donneront pas deux mots voisins
        random.Random(f"{mode}-{lang}").shuffle(garde)
        p = os.path.join(out_dir, f"{mode}-{lang}.json")
        json.dump(garde, open(p, "w"), ensure_ascii=False)
        print(f"  {mode:14s} {len(garde):4d} candidats -> {p}")
    return listes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=["fr", "en"])
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="data/selection")
    a = ap.parse_args()
    prepare(a.lang, a.data_dir, a.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
