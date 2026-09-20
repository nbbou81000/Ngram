#!/usr/bin/env python3
"""
Rendu éditorial des modes, en français et en anglais.

Tous les libellés affichés passent par LABELS : aucun texte n'est écrit en dur
dans les fonctions de rendu. Ajouter une langue revient à ajouter une clé.
"""
import shapes

Y0, Y1 = 1800, 2019
N = Y1 - Y0 + 1
SANS = "Inter,Helvetica,sans-serif"
ANNEE_COURANTE = 2026

LABELS = {
    "fr": {
        "oublie": "le mot oublié", "naissance": "le mot est né",
        "resurrection": "la résurrection", "millesime": "le millésime",
        "bilingue": "le même mot, deux langues",
        "sommet": "sommet", "aujourdhui": "aujourd'hui", "apparition": "apparition",
        "oubli": "oubli", "retour": "retour", "apogee": "son apogée",
        "entree": "entré dans la langue", "plus_bas": "son plus bas",
        "ecart": "ans d'écart entre les sommets",
        "reste": "{pct} % du sommet", "vers": "vers {an}",
        "creux_en": "creux en {an}", "ppm_en": "{v} ppm en {an}",
        "nes_en": "mots nés en", "il_y_a": "il y a {n} ans",
        "francais": "français", "anglais": "anglais",
        "credit": "Google Books Ngram · corpus français 1800–2019",
        "credit_bi": "Google Books Ngram · corpus français et anglais",
        "credit_mil": "Google Books Ngram · première apparition durable dans le corpus",
    },
    "en": {
        "oublie": "a forgotten word", "naissance": "the word appears",
        "resurrection": "the comeback", "millesime": "vintage year",
        "bilingue": "one word, two languages",
        "sommet": "peak", "aujourdhui": "today", "apparition": "first appearance",
        "oubli": "low point", "retour": "comeback", "apogee": "its high-water mark",
        "entree": "entered the language", "plus_bas": "its lowest ebb",
        "ecart": "years between the two peaks",
        "reste": "{pct} % of its peak", "vers": "around {an}",
        "creux_en": "bottomed out in {an}", "ppm_en": "{v} ppm in {an}",
        "nes_en": "words born in", "il_y_a": "{n} years ago",
        "francais": "French", "anglais": "English",
        "credit": "Google Books Ngram · English corpus, 1800–2019",
        "credit_bi": "Google Books Ngram · French and English corpora",
        "credit_mil": "Google Books Ngram · first lasting appearance in the corpus",
    },
}


def L(lang, cle, **kw):
    s = LABELS[lang][cle]
    return s.format(**kw) if kw else s


DEFS = """<defs>
<pattern id="tr" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="7" height="7" fill="#fff"/><rect width="1.5" height="7" fill="#000"/></pattern>
<pattern id="trd" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
<rect width="9" height="9" fill="#fff"/><rect width="2.4" height="9" fill="#000"/></pattern>
</defs>"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def t(x, y, s, size=14, weight="500", anchor="start", fill="#000", ls=None):
    a = (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" '
         f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"')
    if ls:
        a += f' letter-spacing="{ls}"'
    return a + f'>{esc(s)}</text>'


class Chassis:
    """Graphe cadré à gauche, panneau de lecture à droite. Toutes tailles."""

    def __init__(self, W, H, ratio=0.66):
        self.W, self.H = W, H
        self.cw = int(W * ratio)
        self.pad_l, self.pad_r = 48, 18
        self.pad_t, self.pad_b = 28, 46
        self.w = self.cw - self.pad_l - self.pad_r
        self.h = H - self.pad_t - self.pad_b
        self.x0, self.y0 = self.pad_l, self.pad_t
        self.base = self.y0 + self.h
        self.px = self.cw + 12
        self.ymax = 1.0
        self.s = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
                  f'xmlns="http://www.w3.org/2000/svg">', DEFS,
                  f'<rect width="{W}" height="{H}" fill="#fff"/>']

    def scale(self, valeur_max, headroom=1.12):
        self.ymax = valeur_max * headroom

    def X(self, year):
        return self.x0 + self.w * (year - Y0) / (N - 1)

    def Y(self, v):
        return self.base - self.h * min(v / self.ymax, 1.0)

    def grille(self):
        for f in (0.25, 0.5, 0.75, 1.0):
            y = self.base - self.h * f
            self.s.append(f'<line x1="{self.x0}" y1="{y:.1f}" x2="{self.x0+self.w}" '
                          f'y2="{y:.1f}" stroke="#000" stroke-width="1" stroke-dasharray="2 7"/>')
            v = self.ymax * f
            self.s.append(t(self.x0 - 9, y + 5, f"{v:.0f}" if self.ymax > 8 else f"{v:.1f}",
                            13, "600", "end"))
        self.s.append(t(self.x0 - 9, self.y0 - 10, "ppm", 11, "700", "end"))

    def axe_x(self, pas=40):
        for yr in range(1800, 2020, pas):
            self.s.append(t(self.X(yr), self.base + 25, yr, 14, "600", "middle"))
        self.s.append(f'<line x1="{self.x0}" y1="{self.base}" x2="{self.x0+self.w}" '
                      f'y2="{self.base}" stroke="#000" stroke-width="2.5"/>')

    def courbe(self, serie, trame="tr", epaisseur=4.5, tirets=None, pas=2):
        idx = list(range(0, N, pas))
        if idx[-1] != N - 1:
            idx.append(N - 1)
        pts = [(round(self.X(Y0 + i)), round(self.Y(serie[i]))) for i in idx]
        d = " ".join(f"{x},{y}" for x, y in pts)
        if trame:
            self.s.append(f'<path d="M {pts[0][0]},{round(self.base)} L {d} '
                          f'L {pts[-1][0]},{round(self.base)} Z" fill="url(#{trame})"/>')
        da = f' stroke-dasharray="{tirets}"' if tirets else ""
        self.s.append(f'<path d="M {d}" fill="none" stroke="#000" '
                      f'stroke-width="{epaisseur}"{da}/>')

    def repere(self, year, valeur, etiquette=None, haut=True):
        x, y = self.X(year), self.Y(valeur)
        self.s.append(f'<line x1="{x:.1f}" y1="{self.y0}" x2="{x:.1f}" y2="{self.base}" '
                      f'stroke="#000" stroke-width="2" stroke-dasharray="5 4"/>')
        self.s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="#fff" '
                      f'stroke="#000" stroke-width="3.5"/>')
        if etiquette:
            bw = 8 * len(str(etiquette)) + 20
            bx = min(max(x - bw / 2, self.x0), self.x0 + self.w - bw)
            by = self.y0 - 22 if haut else self.base - 34
            self.s.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw}" height="26" fill="#000"/>')
            self.s.append(t(bx + bw / 2, by + 18, etiquette, 15, "700", "middle", "#fff"))

    def panneau(self, bandeau, sujet, lignes, hero=None, hero_label=None):
        W, H, px = self.W, self.H, self.px
        self.s.append(f'<line x1="{self.cw}" y1="16" x2="{self.cw}" y2="{H-16}" '
                      f'stroke="#000" stroke-width="2"/>')
        self.s.append(f'<rect x="{px}" y="18" width="{W-px-16}" height="24" fill="#000"/>')
        self.s.append(t(px + 9, 36, bandeau.upper(), 13, "700", "start", "#fff", ls="1.8"))
        taille = 34 if len(sujet) <= 11 else (27 if len(sujet) <= 15 else 21)
        self.s.append(t(px, 78, sujet, taille, "800"))
        y = 106
        for label, valeur in lignes:
            self.s.append(t(px, y, label.upper(), 11.5, "700", ls="1.2"))
            self.s.append(t(px, y + 22, valeur, 17, "500"))
            y += 46
        if hero:
            self.s.append(f'<line x1="{px}" y1="{H-118}" x2="{W-16}" y2="{H-118}" '
                          f'stroke="#000" stroke-width="2"/>')
            if hero_label:
                self.s.append(t(px, H - 92, hero_label.upper(), 12, "700", ls="1.6"))
            self.s.append(t(px, H - 34, hero, 62, "800"))

    def credit(self, txt):
        self.s.append(t(self.x0, self.H - 10, txt, 11, "500"))

    def out(self):
        return "\n".join(self.s + ["</svg>"])


# ---------------------------------------------------------------- modes
def mot_oublie(mot, serie, W=800, H=480, lang="fr"):
    c = shapes.classe(serie)
    ch = Chassis(W, H)
    ch.scale(max(serie))
    ch.grille()
    ch.courbe(serie)
    ch.repere(c["pic"], max(serie), f"{L(lang,'sommet')} {c['pic']}")
    ch.axe_x()
    ch.panneau(L(lang, "oublie"), mot,
               [(L(lang, "sommet"), f"{c['pic']} · {c['max']} ppm"),
                (L(lang, "aujourdhui"), L(lang, "reste", pct=round(c["reste"] * 100)))],
               hero=str(c["pic"]), hero_label=L(lang, "apogee"))
    ch.credit(L(lang, "credit"))
    return ch.out()


def decollage(mot, serie, W=800, H=480, lang="fr"):
    c = shapes.classe(serie)
    ne = c["naissance"]
    ch = Chassis(W, H)
    ch.scale(max(serie))
    ch.grille()
    ch.courbe(serie)
    ch.repere(ne, serie[ne - Y0], str(ne))
    ch.axe_x()
    ch.panneau(L(lang, "naissance"), mot,
               [(L(lang, "apparition"), L(lang, "vers", an=ne)),
                (L(lang, "sommet"), f"{c['pic']} · {c['max']} ppm")],
               hero=str(ne), hero_label=L(lang, "entree"))
    ch.credit(L(lang, "credit"))
    return ch.out()


def resurrection(mot, serie, W=800, H=480, lang="fr"):
    c = shapes.classe(serie)
    creux = c["creux"]
    ch = Chassis(W, H)
    ch.scale(max(serie))
    ch.grille()
    ch.courbe(serie)
    ch.repere(c["pic"], max(serie), f"{L(lang,'sommet')} {c['pic']}")
    ch.repere(creux, serie[creux - Y0], f"{L(lang,'oubli')} {creux}", haut=False)
    ch.axe_x()
    ch.panneau(L(lang, "resurrection"), mot,
               [(L(lang, "sommet"), f"{c['pic']} · {c['max']} ppm"),
                (L(lang, "oubli"), L(lang, "creux_en", an=creux)),
                (L(lang, "retour"), L(lang, "ppm_en", v=f"{serie[-1]:.1f}", an=2019))],
               hero=str(creux), hero_label=L(lang, "plus_bas"))
    ch.credit(L(lang, "credit"))
    return ch.out()


def millesime(annee, mots, lex, W=800, H=480, lang="fr"):
    s = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'xmlns="http://www.w3.org/2000/svg">', DEFS,
         f'<rect width="{W}" height="{H}" fill="#fff"/>']
    bh = int(H * 0.27)
    s.append(f'<rect x="0" y="0" width="{W}" height="{bh}" fill="#000"/>')
    s.append(t(24, bh * 0.44, L(lang, "nes_en").upper(), 15, "700", fill="#fff", ls="2.4"))
    s.append(t(24, bh * 0.94, annee, int(bh * 0.62), "800", fill="#fff"))
    s.append(t(W - 24, bh * 0.9, L(lang, "il_y_a", n=ANNEE_COURANTE - annee),
               17, "600", "end", "#fff"))

    cols, rows = 3, 2
    gw = (W - 48) / cols
    gh = (H - bh - 34) / rows
    for k, mot in enumerate(mots[:cols * rows]):
        serie = lex[mot]
        cx = 24 + (k % cols) * gw
        cy = bh + 18 + (k // cols) * gh
        cw_, chh = gw - 18, gh - 44
        mx = max(serie)
        # une vignette fait ~230 px de large : 220 points, c'est trois fois trop.
        idx = list(range(0, N, 3)) + [N - 1]
        pts = [(round(cx + cw_ * i / (N - 1)), round(cy + chh - chh * (serie[i] / mx)))
               for i in idx]
        d = " ".join(f"{x},{y}" for x, y in pts)
        s.append(f'<path d="M {pts[0][0]},{round(cy+chh)} L {d} '
                 f'L {pts[-1][0]},{round(cy+chh)} Z" fill="url(#tr)"/>')
        s.append(f'<path d="M {d}" fill="none" stroke="#000" stroke-width="3"/>')
        s.append(f'<line x1="{cx:.1f}" y1="{cy+chh:.1f}" x2="{cx+cw_:.1f}" '
                 f'y2="{cy+chh:.1f}" stroke="#000" stroke-width="2"/>')
        s.append(t(cx, cy + chh + 26, mot, 21, "800"))
        s.append(t(cx + cw_, cy + chh + 25, f"{mx:.0f} ppm", 13, "600", "end"))
    s.append(t(24, H - 8, L(lang, "credit_mil"), 11, "500"))
    return "\n".join(s + ["</svg>"])


def bilingue(mot_fr, serie_fr, mot_en, serie_en, W=800, H=480, lang="fr"):
    ch = Chassis(W, H)
    ch.scale(max(max(serie_fr), max(serie_en)))
    ch.grille()
    ch.courbe(serie_en, trame="trd", epaisseur=3, tirets="9 5")
    ch.courbe(serie_fr, trame=None, epaisseur=4.5)
    ch.axe_x()
    pf = serie_fr.index(max(serie_fr)) + Y0
    pe = serie_en.index(max(serie_en)) + Y0
    ch.panneau(L(lang, "bilingue"), f"{mot_fr} / {mot_en}",
               [(L(lang, "francais") + " ▬", f"{L(lang,'sommet')} {pf} · {max(serie_fr):.0f} ppm"),
                (L(lang, "anglais") + " ▭", f"{L(lang,'sommet')} {pe} · {max(serie_en):.0f} ppm")],
               hero=str(abs(pf - pe)), hero_label=L(lang, "ecart"))
    ch.credit(L(lang, "credit_bi"))
    return ch.out()
