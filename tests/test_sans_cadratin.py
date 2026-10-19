"""Garde-fou : aucun cadratin (U+2014) dans les fichiers texte du dépôt."""
from __future__ import annotations

import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CADRATIN = chr(0x2014)
EXTENSIONS = {
    ".py", ".md", ".ipynb", ".html", ".css", ".toml", ".txt", ".csv", ".json",
    ".ini", ".yml", ".yaml", ".cfg",
}
DOSSIERS_EXCLUS = {".venv", ".git", ".superpowers", "__pycache__"}


def _fichiers_candidats() -> list[Path]:
    """Fichiers suivis par git ou présents dans l'arbre de travail (non ignorés)."""
    try:
        sortie = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=RACINE, capture_output=True, check=True,
        ).stdout.decode("utf-8")
        chemins = [RACINE / p for p in sortie.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        chemins = [p for p in RACINE.rglob("*") if p.is_file()]
    retenus = []
    for chemin in chemins:
        relatif = chemin.relative_to(RACINE)
        if DOSSIERS_EXCLUS.intersection(relatif.parts):
            continue
        if chemin.suffix.lower() in EXTENSIONS and chemin.is_file():
            retenus.append(chemin)
    return sorted(set(retenus))


def test_aucun_cadratin_dans_le_depot():
    fautifs = []
    for chemin in _fichiers_candidats():
        with chemin.open(encoding="utf-8", errors="replace") as flux:
            for numero, ligne in enumerate(flux, start=1):
                if CADRATIN in ligne:
                    fautifs.append(f"{chemin.relative_to(RACINE)}:{numero}")
    assert not fautifs, "Cadratin interdit trouvé dans : " + ", ".join(fautifs)
