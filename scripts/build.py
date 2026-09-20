#!/usr/bin/env python3
"""
Construit TOUS les écrans, une fois pour toutes.

Le corpus Ngram est figé en 2019 : un écran calculé aujourd'hui sera identique
dans dix ans. Il n'y a donc aucune raison de recalculer quoi que ce soit chaque
nuit. Ce script tourne à la main, après une récolte, et c'est tout.

Sortie :
    api/<mode>-<langue>/<slug>.json   un écran complet, ~14 Ko
    api/index-<mode>-<langue>.json    la liste des slugs disponibles

Le hasard n'est pas ici : il est dans le transform du plugin, qui tire au sort
un slug dans l'index à chaque rafraîchissement.

Usage : python scripts/build.py
"""
import argparse, datetime, json, os, re, sys, unicodedata

import shapes, generate

BASE = datetime.date(2000, 1, 1)


def slug(texte):
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "x"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--sel-dir", default="data/selection")
    ap.add_argument("--paires", default="data/paires-bilingues.json")
    ap.add_argument("--out-dir", default="api")
    ap.add_argument("--lang", choices=["fr", "en"], help="une seule langue")
    ap.add_argument("--mode", help="un seul mode")
    a = ap.parse_args()

    lex = {l: shapes.load(l, a.data_dir) for l in ("fr", "en")}
    paires = json.load(open(a.paires, encoding="utf-8")) if os.path.exists(a.paires) else []

    total_fichiers = total_octets = 0
    langues = (a.lang,) if a.lang else ("fr", "en")
    modes_voulus = (a.mode,) if a.mode else tuple(generate.MODES)
    for lang in langues:
        autre = lex["en" if lang == "fr" else "fr"]
        for mode in modes_voulus:
            # combien d'entrées ce mode a-t-il ? on parcourt la liste entière
            if mode == "bilingue":
                n = len(paires)
            else:
                n = len(generate.charger_selection(mode, lang, a.sel_dir))
            if not n:
                print(f"  {mode}-{lang} : vide")
                continue

            dossier = os.path.join(a.out_dir, f"{mode}-{lang}")
            os.makedirs(dossier, exist_ok=True)
            slugs, octets = [], 0

            for i in range(n):
                date = BASE + datetime.timedelta(days=i)
                p = generate.rendre(mode, lang, date, lex[lang], autre,
                                    a.sel_dir, paires, lexiques=lex)
                if not p:
                    continue
                s = slug(p["sujet"])
                if s in slugs:          # la rotation peut repasser sur un sujet
                    continue
                p.pop("genere_le", None)   # un écran figé n'a pas de date
                chemin = os.path.join(dossier, f"{s}.json")
                json.dump(p, open(chemin, "w"), ensure_ascii=False, separators=(",", ":"))
                octets += os.path.getsize(chemin)
                slugs.append(s)

            index = {"mode": mode, "langue": lang, "titre": modes_titre(lang, mode),
                     "base": f"{mode}-{lang}", "ecrans": slugs}
            ichemin = os.path.join(a.out_dir, f"index-{mode}-{lang}.json")
            json.dump(index, open(ichemin, "w"), ensure_ascii=False, separators=(",", ":"))
            total_fichiers += len(slugs)
            total_octets += octets
            print(f"  {mode}-{lang:2s} : {len(slugs):4d} écrans · {octets/1e6:5.2f} Mo")

    # index général : permet au transform de tirer aussi le MODE au hasard.
    # Reconstruit à chaque passage, à partir des index présents sur le disque,
    # donc correct même quand on ne construit qu'un mode à la fois.
    for lang in ("fr", "en"):
        dispo = [m for m in generate.MODES
                 if os.path.exists(os.path.join(a.out_dir, f"index-{m}-{lang}.json"))]
        json.dump({"langue": lang, "modes": dispo},
                  open(os.path.join(a.out_dir, f"index-rotation-{lang}.json"), "w"),
                  ensure_ascii=False, separators=(",", ":"))

    print(f"{total_fichiers} écrans, {total_octets/1e6:.1f} Mo au total")
    return 0


def modes_titre(lang, mode):
    import modes as M
    return M.L(lang, mode).capitalize()


if __name__ == "__main__":
    sys.exit(main())
