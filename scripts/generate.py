#!/usr/bin/env python3
"""
Générateur quotidien : écrit un petit JSON par mode et par langue, prêt à être
servi par GitHub Pages et lu par TRMNL.

Le plugin interpole le mode et la langue choisis par l'utilisateur dans son URL
de polling :

    https://<user>.github.io/Ngram/api/{{ mode }}-{{ langue }}.json

Chaque appareil ne télécharge donc que l'écran qu'il affiche. Le SVG est
entièrement pré-calculé ici : à l'affichage, le template Liquid ne fait que
l'insérer, sans le moindre calcul ni appel réseau.

Usage : python scripts/generate.py --date 2026-09-20
"""
import argparse, datetime, json, os, sys

import shapes, modes

OG = (800, 480)
X = (1040, 780)
MODES = ["oublie", "naissance", "resurrection", "millesime", "bilingue"]

TITRES = {
    "fr": {"oublie": "Le mot oublié", "naissance": "Le mot est né",
           "resurrection": "La résurrection", "millesime": "Le millésime",
           "bilingue": "Le même mot, deux langues"},
    "en": {"oublie": "A forgotten word", "naissance": "The word appears",
           "resurrection": "The comeback", "millesime": "Vintage year",
           "bilingue": "One word, two languages"},
}


def jour(date):
    """Numéro de jour absolu : sert d'index de rotation, stable et croissant."""
    return (date - datetime.date(2000, 1, 1)).days


def choisir(liste, date, decalage=0):
    if not liste:
        return None
    return liste[(jour(date) + decalage) % len(liste)]


def charger_selection(mode, lang, sel_dir):
    p = os.path.join(sel_dir, f"{mode}-{lang}.json")
    if not os.path.exists(p):
        return []
    return json.load(open(p, encoding="utf-8"))


def rendre(mode, lang, date, lex, lex_autre, sel_dir, paires):
    """Renvoie le payload complet d'un mode, ou None s'il n'y a rien à montrer."""
    titre = TITRES[lang][mode]

    if mode == "bilingue":
        couple = choisir(paires, date)
        if not couple:
            return None
        fr, en = couple["fr"], couple["en"]
        if fr not in lex or en not in lex_autre:
            return None
        svg = {k: modes.bilingue(fr, lex[fr], en, lex_autre[en], w, h)
               for k, (w, h) in (("og", OG), ("x", X))}
        sujet = f"{fr} / {en}"

    elif mode == "millesime":
        item = choisir(charger_selection(mode, lang, sel_dir), date)
        if not item:
            return None
        mots = [m for m in item["mots"] if m in lex]
        if len(mots) < 4:
            return None
        svg = {k: modes.millesime(item["annee"], mots, lex, w, h)
               for k, (w, h) in (("og", OG), ("x", X))}
        sujet = str(item["annee"])

    else:
        item = choisir(charger_selection(mode, lang, sel_dir), date)
        if not item or item["mot"] not in lex:
            return None
        mot, serie = item["mot"], lex[item["mot"]]
        fn = {"oublie": modes.mot_oublie, "naissance": modes.decollage,
              "resurrection": modes.resurrection}[mode]
        svg = {k: fn(mot, serie, w, h, lang) for k, (w, h) in (("og", OG), ("x", X))}
        sujet = mot

    return {"mode": mode, "langue": lang, "titre": titre, "sujet": sujet,
            "genere_le": date.isoformat(),
            "og": svg["og"], "x": svg["x"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="AAAA-MM-JJ, défaut aujourd'hui (UTC)")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--sel-dir", default="data/selection")
    ap.add_argument("--paires", default="data/paires-bilingues.json")
    ap.add_argument("--out-dir", default="api")
    a = ap.parse_args()

    date = (datetime.date.fromisoformat(a.date) if a.date
            else datetime.datetime.now(datetime.timezone.utc).date())
    os.makedirs(a.out_dir, exist_ok=True)

    lex = {l: shapes.load(l, a.data_dir) for l in ("fr", "en")}
    paires = json.load(open(a.paires, encoding="utf-8")) if os.path.exists(a.paires) else []

    ecrits, manquants = 0, []
    for lang in ("fr", "en"):
        dispo = []
        for mode in MODES:
            p = rendre(mode, lang, date, lex[lang], lex["en" if lang == "fr" else "fr"],
                       a.sel_dir, paires)
            if not p:
                manquants.append(f"{mode}-{lang}")
                continue
            chemin = os.path.join(a.out_dir, f"{mode}-{lang}.json")
            json.dump(p, open(chemin, "w"), ensure_ascii=False, separators=(",", ":"))
            ecrits += 1
            dispo.append(mode)
            print(f"  {chemin:34s} {os.path.getsize(chemin)/1024:5.1f} Ko  · {p['sujet']}")

        # rotation : le mode change chaque jour, parmi ceux qui ont du contenu
        if dispo:
            mode = dispo[jour(date) % len(dispo)]
            src = json.load(open(os.path.join(a.out_dir, f"{mode}-{lang}.json"),
                                 encoding="utf-8"))
            src["rotation"] = True
            chemin = os.path.join(a.out_dir, f"rotation-{lang}.json")
            json.dump(src, open(chemin, "w"), ensure_ascii=False, separators=(",", ":"))
            ecrits += 1
            print(f"  {chemin:34s} {os.path.getsize(chemin)/1024:5.1f} Ko  · "
                  f"aujourd'hui : {mode}")

    if manquants:
        print(f"  (pas encore de contenu pour : {', '.join(manquants)})")
    print(f"{ecrits} fichiers écrits pour le {date.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
