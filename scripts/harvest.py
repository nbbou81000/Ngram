#!/usr/bin/env python3
"""
Récolte des séries Google Books Ngram, langue par langue.

Le corpus Ngram est figé (arrêt en 2019) : une série récoltée aujourd'hui ne
changera plus jamais. On récolte donc UNE fois, puis plus jamais.

Les fichiers de sortie sont en JSONL et servent eux-mêmes d'état : à chaque
redémarrage, on relit les mots déjà présents et on reprend où on s'est arrêté.
Un run interrompu (timeout GitHub Actions, coupure réseau) ne perd rien.

Chaque run écrit son PROPRE fichier data/ngram-<lang>/part-NNNN.jsonl. Un fichier
déjà commité n'est donc jamais réécrit : Git ne stocke chaque octet qu'une fois.

Le script est fait pour être appelé par TRANCHES courtes (--max-calls 60, soit
environ 3 minutes), le workflow committant après chaque tranche. Un runner tué
en cours de route ne fait donc jamais perdre plus d'une tranche.

Codes de sortie, pour que le workflow sache quoi faire :
    0  tranche terminée normalement, il reste du travail
    3  plus rien à récolter pour cette langue
    4  arrêt sur échec réseau définitif (Google throttle) — réessayer plus tard

Usage :
    python scripts/harvest.py --lang fr --max-calls 60
"""
import argparse, json, os, random, sys, time, unicodedata
import urllib.parse, urllib.request

YEAR_START, YEAR_END = 1800, 2019
N_YEARS = YEAR_END - YEAR_START + 1
BATCH = 10                 # mots par appel (10 testé OK)
PAUSE = 3.0                # secondes entre deux appels
SMOOTHING = 3
UA = {"User-Agent": "Mozilla/5.0 (compatible; ngram-duels/1.0)"}
CORPUS = {"fr": "fr-2019", "en": "en-2019"}

# mots-outils à écarter : ils n'ont aucun intérêt en duel
STOP = {
 "fr": set("""le la les un une des du de au aux et ou mais donc or ni car que qui quoi dont
 ou est sont etre avoir fait faire dit dire plus moins tres bien tout tous toute toutes
 pour avec sans sous sur dans par vers chez entre pas ne non oui son sa ses mon ma mes
 ton ta tes notre nos votre vos leur leurs ce cet cette ces celui celle ceux elle elles
 il ils nous vous moi toi lui eux cela ceci ici la-bas alors ainsi aussi encore deja
 jamais toujours peut peu beaucoup trop assez comme quand meme autre autres chaque""".split()),
 "en": set("""the a an and or but so nor for yet of to in on at by with from into over
 under is are was were be been being have has had do does did will would shall should
 can could may might must not no yes this that these those it its he she they them him
 her his their our your my me you we us i as if then than there here when where how why
 what which who whom whose all any some each other another more most less very just
 also too still even only such same own out up down off about after before again""".split()),
}


def norm(w):
    return unicodedata.normalize("NFC", w.strip().lower())


def load_lexicon(path, lang, limit, min_len):
    """Lit une liste de fréquence (un mot par ligne, éventuellement 'mot compte')."""
    seen, out = set(), []
    with open(path, encoding="utf-8") as f:
        for line in f:
            w = norm(line.split()[0]) if line.split() else ""
            if not w or w in seen:
                continue
            if len(w) < min_len or not w.isalpha():
                continue
            if w in STOP.get(lang, ()):
                continue
            seen.add(w)
            out.append(w)
            if len(out) >= limit:
                break
    return out


def parts(out_dir):
    if not os.path.isdir(out_dir):
        return []
    return sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir)
                  if f.startswith("part-") and f.endswith(".jsonl"))


def already_done(out_dir):
    """Relit tous les fichiers déjà écrits : c'est l'état de reprise."""
    done = set()
    for p in parts(out_dir):
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["w"])
                except Exception:
                    pass
    return done


def next_part(out_dir):
    existing = parts(out_dir)
    n = 1 + max([int(os.path.basename(p)[5:9]) for p in existing], default=0)
    return os.path.join(out_dir, f"part-{n:04d}.jsonl")


def fetch(words, corpus):
    """Renvoie {mot: [220 valeurs brutes]} ou None si l'appel a échoué."""
    q = urllib.parse.urlencode({
        "content": ",".join(words), "year_start": YEAR_START, "year_end": YEAR_END,
        "corpus": corpus, "smoothing": SMOOTHING})
    url = "https://books.google.com/ngrams/json?" + q
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                payload = r.read().decode("utf-8")
            data = json.loads(payload)
            return {norm(x["ngram"]): x["timeseries"] for x in data
                    if x.get("type") == "NGRAM" and len(x.get("timeseries", [])) == N_YEARS}
        except Exception as e:
            wait = PAUSE * (2 ** attempt) + random.uniform(0, 2)
            print(f"    tentative {attempt+1}/5 échouée ({e}) — pause {wait:.0f}s", flush=True)
            time.sleep(wait)
    return None


def quantize(series):
    """ppm × 1000, en entiers : 0,001 ppm de résolution, fichier 3× plus léger."""
    return [int(round(v * 1e9)) for v in series]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=["fr", "en"])
    ap.add_argument("--lexicon", help="défaut : data/lexicon-<lang>.txt")
    ap.add_argument("--out-dir", help="défaut : data/ngram-<lang>/")
    ap.add_argument("--limit", type=int, default=30000, help="taille du lexique retenu")
    ap.add_argument("--min-len", type=int, default=4)
    ap.add_argument("--max-calls", type=int, default=600, help="appels max pour ce run")
    a = ap.parse_args()

    lex_path = a.lexicon or f"data/lexicon-{a.lang}.txt"
    out_dir = a.out_dir or f"data/ngram-{a.lang}"
    os.makedirs(out_dir, exist_ok=True)

    words = load_lexicon(lex_path, a.lang, a.limit, a.min_len)
    done = already_done(out_dir)
    todo = [w for w in words if w not in done]
    print(f"[{a.lang}] lexique={len(words)} déjà fait={len(done)} reste={len(todo)}", flush=True)
    if not todo:
        print("terminé : rien à récolter.")
        return 3

    corpus = CORPUS[a.lang]
    calls = kept = 0
    status = 0
    t0 = time.time()
    out_path = next_part(out_dir)
    print(f"[{a.lang}] écriture dans {out_path}", flush=True)
    with open(out_path, "a", encoding="utf-8") as out:
        for i in range(0, len(todo), BATCH):
            if calls >= a.max_calls:
                print("quota d'appels atteint pour ce run.", flush=True)
                break
            batch = todo[i:i + BATCH]
            res = fetch(batch, corpus)
            calls += 1
            if res is None:
                print("échec définitif sur ce lot — on arrête proprement, "
                      "le prochain run reprendra ici.", flush=True)
                status = 4
                break
            for w in batch:
                s = res.get(w)
                # un mot absent du corpus est écrit avec une série vide :
                # il ne sera jamais redemandé.
                out.write(json.dumps({"w": w, "s": quantize(s) if s else []},
                                     ensure_ascii=False) + "\n")
                kept += 1 if s else 0
            out.flush()
            if calls % 20 == 0:
                sp = calls / max(time.time() - t0, 1) * 60
                print(f"  {calls} appels · {i+len(batch)}/{len(todo)} mots · "
                      f"{sp:.0f} appels/min", flush=True)
            time.sleep(PAUSE)

    # un fichier de tranche vide ne sert à rien : on le retire
    if os.path.exists(out_path) and os.path.getsize(out_path) == 0:
        os.remove(out_path)

    print(f"[{a.lang}] tranche terminée : {calls} appels, "
          f"{kept} séries non vides ajoutées.", flush=True)
    return status


if __name__ == "__main__":
    sys.exit(main())
