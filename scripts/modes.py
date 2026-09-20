#!/usr/bin/env python3
"""Rendu éditorial des modes à un seul mot. Même châssis pour tous."""
import shapes

Y0, Y1 = 1800, 2019
N = Y1 - Y0 + 1
SANS = "Inter,Helvetica,sans-serif"

DEFS = """<defs>
<pattern id="tr" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="7" height="7" fill="#fff"/><rect width="1.5" height="7" fill="#000"/></pattern>
<pattern id="trd" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
<rect width="9" height="9" fill="#fff"/><rect width="2.4" height="9" fill="#000"/></pattern>
</defs>"""


def t(x, y, s, size=14, weight="500", anchor="start", fill="#000", ls=None, style=None):
    a = (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" '
         f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"')
    if ls:
        a += f' letter-spacing="{ls}"'
    if style:
        a += f' font-style="{style}"'
    return a + f'>{s}</text>'


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
        self.s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">', DEFS,
                  f'<rect width="{W}" height="{H}" fill="#fff"/>']
        self.ymax = 1.0

    # --- graphe ---------------------------------------------------------
    def scale(self, series, headroom=1.12):
        self.ymax = max(series) * headroom

    def X(self, year):
        return self.x0 + self.w * (year - Y0) / (N - 1)

    def Y(self, v):
        return self.base - self.h * min(v / self.ymax, 1.0)

    def grille(self, unit="ppm"):
        for f in (0.25, 0.5, 0.75, 1.0):
            y = self.base - self.h * f
            self.s.append(f'<line x1="{self.x0}" y1="{y:.1f}" x2="{self.x0+self.w}" '
                          f'y2="{y:.1f}" stroke="#000" stroke-width="1" stroke-dasharray="2 7"/>')
            self.s.append(t(self.x0 - 9, y + 5, f"{self.ymax*f:.0f}" if self.ymax > 8
                            else f"{self.ymax*f:.1f}", 13, "600", "end"))
        self.s.append(t(self.x0 - 9, self.y0 - 10, unit, 11, "700", "end"))

    def axe_x(self, pas=40):
        for yr in range(1800, 2020, pas):
            self.s.append(t(self.X(yr), self.base + 25, str(yr), 14, "600", "middle"))
        self.s.append(f'<line x1="{self.x0}" y1="{self.base}" x2="{self.x0+self.w}" '
                      f'y2="{self.base}" stroke="#000" stroke-width="2.5"/>')

    def courbe(self, series, trame="tr", epaisseur=4.5, tirets=None):
        pts = [(self.X(Y0 + i), self.Y(v)) for i, v in enumerate(series)]
        d = " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        if trame:
            self.s.append(f'<path d="M {pts[0][0]:.1f},{self.base:.1f} L {d} '
                          f'L {pts[-1][0]:.1f},{self.base:.1f} Z" fill="url(#{trame})"/>')
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
            bw = 8 * len(etiquette) + 20
            bx = min(max(x - bw / 2, self.x0), self.x0 + self.w - bw)
            by = self.y0 - 22 if haut else self.base - 34
            self.s.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw}" height="26" '
                          f'fill="#000"/>')
            self.s.append(t(bx + bw / 2, by + 18, etiquette, 15, "700", "middle", "#fff"))

    # --- panneau --------------------------------------------------------
    def panneau(self, mode, mot, lignes, hero=None, hero_label=None):
        W, H, px = self.W, self.H, self.px
        self.s.append(f'<line x1="{self.cw}" y1="16" x2="{self.cw}" y2="{H-16}" '
                      f'stroke="#000" stroke-width="2"/>')
        self.s.append(f'<rect x="{px}" y="18" width="{W-px-16}" height="24" fill="#000"/>')
        self.s.append(t(px + 9, 36, mode.upper(), 13, "700", "start", "#fff", ls="1.8"))

        taille = 34 if len(mot) <= 11 else (27 if len(mot) <= 15 else 21)
        self.s.append(t(px, 78, mot, taille, "800"))
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
        self.s.append(t(self.x0, self.H - 10, txt, 11, "500", fill="#000"))

    def out(self):
        return "\n".join(self.s + ["</svg>"])


# ---------------------------------------------------------------- modes
def mot_oublie(mot, serie, W=800, H=480, langue="fr"):
    c = shapes.classe(serie)
    ch = Chassis(W, H)
    ch.scale(serie)
    ch.grille()
    ch.courbe(serie)
    ch.repere(c["pic"], max(serie), f"sommet {c['pic']}")
    ch.axe_x()
    ch.panneau("le mot oublié" if langue == "fr" else "a forgotten word", mot,
               [("sommet", f"{c['pic']} · {c['max']} ppm"),
                ("aujourd'hui", f"{c['reste']*100:.0f} % du sommet")],
               hero=str(c["pic"]), hero_label="son apogée")
    ch.credit("Google Books Ngram · corpus français 1800–2019")
    return ch.out()


def decollage(mot, serie, W=800, H=480, langue="fr"):
    c = shapes.classe(serie)
    ne = c["naissance"]
    ch = Chassis(W, H)
    ch.scale(serie)
    ch.grille()
    ch.courbe(serie)
    ch.repere(ne, serie[ne - Y0], f"{ne}")
    ch.axe_x()
    ch.panneau("le mot est né" if langue == "fr" else "the word appears", mot,
               [("apparition", f"vers {ne}"),
                ("sommet", f"{c['pic']} · {c['max']} ppm")],
               hero=str(ne), hero_label="entré dans la langue")
    ch.credit("Google Books Ngram · corpus français 1800–2019")
    return ch.out()


def resurrection(mot, serie, W=800, H=480, langue="fr"):
    c = shapes.classe(serie)
    ch = Chassis(W, H)
    ch.scale(serie)
    ch.grille()
    ch.courbe(serie)
    ch.repere(c["pic"], max(serie), f"sommet {c['pic']}")
    creux = c["creux"]
    ch.repere(creux, serie[creux - Y0], f"creux {creux}", haut=False)
    ch.axe_x()
    ch.panneau("la résurrection", mot,
               [("sommet", f"{c['pic']} · {c['max']} ppm"),
                ("oubli", f"creux en {creux}"),
                ("retour", f"{serie[-1]:.1f} ppm en 2019")],
               hero=str(creux), hero_label="son plus bas")
    ch.credit("Google Books Ngram · corpus français 1800–2019")
    return ch.out()


def millesime(annee, mots, lex, W=800, H=480):
    """Plusieurs mots nés la même année : petites courbes en grille."""
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">', DEFS,
         f'<rect width="{W}" height="{H}" fill="#fff"/>']
    # bandeau
    bh = int(H * 0.27)
    s.append(f'<rect x="0" y="0" width="{W}" height="{bh}" fill="#000"/>')
    s.append(t(24, bh * 0.44, "MOTS NÉS EN", 15, "700", fill="#fff", ls="2.4"))
    s.append(t(24, bh * 0.94, str(annee), int(bh * 0.62), "800", fill="#fff"))
    s.append(t(W - 24, bh * 0.9, f"il y a {2026-annee} ans", 17, "600", "end", "#fff"))

    cols, rows = 3, 2
    gw = (W - 48) / cols
    gh = (H - bh - 34) / rows
    for k, mot in enumerate(mots[:cols * rows]):
        serie = lex[mot]
        cx = 24 + (k % cols) * gw
        cy = bh + 18 + (k // cols) * gh
        cw_, chh = gw - 18, gh - 44
        mx = max(serie)
        pts = [(cx + cw_ * i / (N - 1), cy + chh - chh * (v / mx)) for i, v in enumerate(serie)]
        d = " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        s.append(f'<path d="M {pts[0][0]:.1f},{cy+chh:.1f} L {d} '
                 f'L {pts[-1][0]:.1f},{cy+chh:.1f} Z" fill="url(#tr)"/>')
        s.append(f'<path d="M {d}" fill="none" stroke="#000" stroke-width="3"/>')
        s.append(f'<line x1="{cx:.1f}" y1="{cy+chh:.1f}" x2="{cx+cw_:.1f}" '
                 f'y2="{cy+chh:.1f}" stroke="#000" stroke-width="2"/>')
        s.append(t(cx, cy + chh + 26, mot, 21, "800"))
        s.append(t(cx + cw_, cy + chh + 25, f"{mx:.0f} ppm", 13, "600", "end"))
    s.append(t(24, H - 8, "Google Books Ngram · première apparition durable dans le corpus", 11, "500"))
    return "\n".join(s + ["</svg>"])


def bilingue(mot_fr, serie_fr, mot_en, serie_en, W=800, H=480):
    ch = Chassis(W, H)
    ch.scale([max(max(serie_fr), max(serie_en))] )
    ch.ymax = max(max(serie_fr), max(serie_en)) * 1.12
    ch.grille()
    ch.courbe(serie_en, trame="trd", epaisseur=3, tirets="9 5")
    ch.courbe(serie_fr, trame=None, epaisseur=4.5)
    ch.axe_x()
    pf = serie_fr.index(max(serie_fr)) + Y0
    pe = serie_en.index(max(serie_en)) + Y0
    ch.panneau("le même mot, deux langues", f"{mot_fr} / {mot_en}",
               [("français ▬", f"sommet {pf} · {max(serie_fr):.0f} ppm"),
                ("anglais ▭", f"sommet {pe} · {max(serie_en):.0f} ppm")],
               hero=str(abs(pf - pe)), hero_label="ans d'écart entre les sommets")
    ch.credit("Google Books Ngram · corpus français et anglais")
    return ch.out()
