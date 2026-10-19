"""Télécharge les trois fichiers bruts du Google Merchandise Store.

Source : Observable (@observablehq/google-merchandise-sales-data), sous-ensemble
des données Google Analytics 4 (période 2020-11-01 au 2021-01-31).
Les fichiers sont servis compressés en gzip, sans extension .gz.

Usage : python scripts/telecharger_donnees.py
"""
from __future__ import annotations

import gzip
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_BRUT = RACINE / "data" / "raw"

BASE_URL = "https://static.observableusercontent.com/files/"

# nom -> (url, en-tête attendu, nombre de lignes de données attendu)
FICHIERS = {
    "events": (
        BASE_URL
        + "845a898c568ec809581cc9b237a87804da7d499860cf1a7ef55e55f52f22d59d"
        "20c4a32eee620cd970c9bf33d31cf6bf30e4424c4614e3459496931d36cf4f61",
        "user_id,ga_session_id,country,device,type,item_id,date",
        758_884,
    ),
    "items": (
        BASE_URL
        + "d435b958c46cabed96246426f0bb4d41c3346ea595ff216ff979918e0f94cb44"
        "e738caa3a76a023d90ff959ec62f42a2755e1fc7a7299af6f7d7b4e56982566e",
        "id,name,brand,variant,category,price_in_usd",
        # ids de 0 à 1380 : 1 381 lignes (la spec indique 1 380, le plus grand id)
        1_381,
    ),
    "users": (
        BASE_URL
        + "7526de4ae1295798cf559eba1644fb8ae72da71faad134a5ea249d88f93c6d60"
        "9542460cf192751d3866b5b10ff0f1152b11dc4a9cd88e2ea769fae1db91fcde",
        "id,ltv,date",
        270_154,
    ),
}


def decompresser(octets: bytes) -> bytes:
    """Décompresse du gzip ; renvoie les octets tels quels si ce n'est pas du gzip."""
    if octets[:2] == b"\x1f\x8b":
        return gzip.decompress(octets)
    return octets


def verifier(nom: str, contenu: bytes, entete: str, nb_lignes: int) -> None:
    """Contrôle l'en-tête et le nombre de lignes de données ; lève ValueError sinon."""
    texte = contenu.decode("utf-8")
    lignes = texte.splitlines()
    if not lignes or lignes[0].strip() != entete:
        premiere = lignes[0] if lignes else ""
        raise ValueError(f"{nom} : en-tête inattendu {premiere!r} (attendu {entete!r})")
    trouve = len(lignes) - 1
    if trouve != nb_lignes:
        raise ValueError(f"{nom} : {trouve} lignes de données (attendu {nb_lignes})")


def telecharger(url: str) -> bytes:
    requete = urllib.request.Request(url, headers={"User-Agent": "audience-lab/1.0"})
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        return reponse.read()


def main() -> int:
    DOSSIER_BRUT.mkdir(parents=True, exist_ok=True)
    for nom, (url, entete, nb_lignes) in FICHIERS.items():
        print(f"Téléchargement de {nom}...")
        contenu = decompresser(telecharger(url))
        verifier(nom, contenu, entete, nb_lignes)
        destination = DOSSIER_BRUT / f"{nom}.csv"
        destination.write_bytes(contenu)
        print(f"  OK : {destination.relative_to(RACINE)} ({nb_lignes} lignes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
