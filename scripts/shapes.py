#!/usr/bin/env python3
"""
Classe chaque mot par la FORME de sa courbe. Aucun appariement, donc aucun
problème de sémantique : un mot oublié est un mot oublié, point.

Formes détectées :
  cloche       monte, culmine, s'effondre       -> "le mot oublié"
  decollage    quasi nul, puis explose          -> "né en 18xx"
  resurrection chute puis remonte franchement   -> rare et savoureux
  effondrement décline sans jamais culminer
  plateau      stable                           (écarté, sans intérêt)

Usage : python scripts/shapes.py --lang fr --forme cloche --top 20
"""
import argparse, glob, json, os, sys

Y0, Y1 = 1800, 2019
N = Y1 - Y0 + 1
MIN_PPM = 0.8


def load(lang, data_dir="data"):
    out = {}
    for p in sorted(glob.glob(os.path.join(data_dir, f"ngram-{lang}", "part-*.jsonl"))):
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("s") and len(r["s"]) == N:
                out[r["w"]] = [v / 1000.0 for v in r["s"]]
    return out


def moyenne(s, a, b):
    seg = s[max(0, a):min(N, b)]
    return sum(seg) / max(len(seg), 1)


def classe(s):
    mx = max(s)
    if mx < MIN_PPM:
        return None
    ipic = s.index(mx)
    pic = Y0 + ipic
    debut = moyenne(s, 0, 30)
    fin = moyenne(s, N - 30, N)
    avant = moyenne(s, ipic - 30, ipic)
    apres = moyenne(s, ipic + 1, ipic + 31)

    # décollage : année où le mot franchit durablement 5 % de son sommet
    seuil = mx * 0.05
    naissance = None
    for i in range(N - 10):
        if s[i] >= seuil and all(v >= seuil * 0.6 for v in s[i:i + 10]):
            naissance = Y0 + i
            break

    chute = fin / mx                      # ce qu'il reste du sommet aujourd'hui
    montee = (mx + 1e-9) / (debut + 1e-9)

    # résurrection : un creux marqué entre le sommet et aujourd'hui, puis remontée
    creux = min(s[ipic:]) if ipic < N - 20 else mx
    remontee = (fin + 1e-9) / (creux + 1e-9)

    forme, note = "plateau", 0.0
    if 1830 < pic < 1985 and chute < 0.45 and montee > 2.5:
        forme = "cloche"
        note = (1 - chute) * min(montee, 20)
    elif naissance and naissance > 1860 and debut < mx * 0.04 and fin > mx * 0.5:
        forme = "decollage"
        note = min(mx, 50) * (fin / mx)
    elif remontee > 2.2 and creux < mx * 0.5 and fin > mx * 0.45 and ipic < N - 60:
        forme = "resurrection"
        note = remontee * (fin / mx)
    elif chute < 0.35 and montee < 2.0:
        forme = "effondrement"
        note = (1 - chute) * min(mx, 30)

    return {"forme": forme, "pic": pic, "max": round(mx, 1), "naissance": naissance,
            "reste": round(chute, 2), "note": round(note, 2),
            "creux": Y0 + ipic + s[ipic:].index(creux) if ipic < N - 20 else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--forme", default="cloche")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()

    lex = load(a.lang, a.data_dir)
    res = []
    compte = {}
    for w, s in lex.items():
        c = classe(s)
        if not c:
            continue
        compte[c["forme"]] = compte.get(c["forme"], 0) + 1
        if c["forme"] == a.forme:
            c["mot"] = w
            res.append(c)
    res.sort(key=lambda r: -r["note"])
    print(f"[{a.lang}] {len(lex)} mots · répartition : "
          + " · ".join(f"{k} {v}" for k, v in sorted(compte.items(), key=lambda x: -x[1])))
    for r in res[:a.top]:
        extra = (f"né vers {r['naissance']}" if r["forme"] == "decollage"
                 else f"creux {r['creux']}" if r["forme"] == "resurrection"
                 else f"il en reste {r['reste']*100:.0f} %")
        print(f"  {r['note']:6.1f}  {r['mot']:>18s}  sommet {r['pic']} à {r['max']:>6.1f} ppm · {extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
