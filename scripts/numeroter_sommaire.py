"""Renseigne les numéros de page de la table des matières d'un rapport HTML.

Chromium ne gère pas ``target-counter()`` : on imprime donc une première fois le
rapport, on repère dans le texte du PDF (``pdftotext``) la page où commence chaque
section, puis on écrit ces numéros dans une copie du HTML, imprimée à son tour.

Convention du HTML : chaque entrée du sommaire est un ``<li class="n1">`` (section,
dont l'en-tête affiche son numéro sur deux chiffres, ou une lettre, juste avant le
titre, à 80 caractères près) ou ``<li class="n2">`` (sous-section, titre précédé de son numéro)
contenant ``<span class="idx">``, ``<span class="titre">`` et un
``<span class="page" data-cible="..."></span>`` vide, à remplir.

Usage : python3 scripts/numeroter_sommaire.py <rapport.html> <premier_passage.pdf> <sortie.html>
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ENTREE = re.compile(
    r'<li class="(n1|n2)">\s*<a href="#[^"]+">\s*'
    r'<span class="idx">(.*?)</span>\s*<span class="titre">(.*?)</span>.*?'
    r'<span class="page" data-cible="([^"]+)"></span>',
    re.S,
)


def normaliser(texte: str) -> str:
    """Texte comparable : entités décodées, ligatures dépliées, sans espaces ni balises."""
    texte = html.unescape(re.sub(r"<[^>]+>", "", texte))
    texte = unicodedata.normalize("NFKC", texte)
    return re.sub(r"\s+", "", texte).lower()


def pages_du_pdf(pdf: Path) -> list[str]:
    sortie = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                            capture_output=True, check=True, text=True).stdout
    return [normaliser(page) for page in sortie.split("\f")]


def main(source: Path, pdf: Path, destination: Path) -> None:
    contenu = source.read_text(encoding="utf-8")
    pages = pages_du_pdf(pdf)
    sommaire = next(i for i, p in enumerate(pages) if "tabledesmatières" in p)
    numeros: dict[str, int] = {}
    depart = sommaire + 1
    for niveau, idx, titre, cible in ENTREE.findall(contenu):
        numero = idx.zfill(2) if idx.isdigit() and niveau == "n1" else idx
        # Le numéro précède le titre, éventuellement séparé par un surtitre court.
        motif = re.compile(re.escape(normaliser(numero)) + r".{0,80}?" + re.escape(normaliser(titre)))
        trouve = next((i for i in range(depart, len(pages)) if motif.search(pages[i])), None)
        if trouve is None:
            raise SystemExit(f"Section introuvable dans le PDF : {idx} {titre}")
        numeros[cible] = trouve + 1
        depart = trouve
    remplace = re.sub(
        r'<span class="page" data-cible="([^"]+)"></span>',
        lambda m: f'<span class="page" data-cible="{m.group(1)}">{numeros[m.group(1)]}</span>',
        contenu,
    )
    destination.write_text(remplace, encoding="utf-8")
    print(f"Sommaire : {len(numeros)} entrées numérotées")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
