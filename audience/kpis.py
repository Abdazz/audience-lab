"""Indicateurs clés de la page d'accueil et utilitaires de formatage français."""
from __future__ import annotations

import math

import pandas as pd

ESPACE_FINE = chr(0x202F)  # espace fine insécable (séparateur de milliers)
CLES_KPIS = (
    "sessions", "utilisateurs", "duree_moyenne_s", "panier_moyen_usd",
    "taux_conversion", "part_mobile", "chiffre_affaires_usd",
)
# Indicateurs exprimés en proportion : la variation est une différence en points.
CLES_POINTS = ("taux_conversion", "part_mobile")


def calculer_kpis(sessions: pd.DataFrame) -> dict[str, float | None]:
    """Indicateurs d'un ensemble de sessions (None quand ils ne sont pas définis)."""
    if len(sessions) == 0:
        resultat: dict[str, float | None] = {c: None for c in CLES_KPIS}
        resultat["sessions"] = 0
        resultat["utilisateurs"] = 0
        return resultat
    achats = sessions.loc[sessions["purchased"], "revenue_usd"]
    return {
        "sessions": int(len(sessions)),
        "utilisateurs": int(sessions["user_id"].nunique()),
        "duree_moyenne_s": float(sessions["duration_s"].mean()),
        # Panier moyen = revenu moyen des sessions avec achat (valeur de commande).
        "panier_moyen_usd": float(achats.mean()) if len(achats) else None,
        "taux_conversion": float(sessions["purchased"].mean()),
        "part_mobile": float((sessions["device"] == "mobile").mean()),
        "chiffre_affaires_usd": float(sessions["revenue_usd"].sum()),
    }


def variations(actuel: dict, precedent: dict) -> dict[str, float | None]:
    """Variation relative en % ; en points de pourcentage pour les proportions."""
    resultat: dict[str, float | None] = {}
    for cle in actuel:
        a, p = actuel[cle], precedent.get(cle)
        if a is None or p is None:
            resultat[cle] = None
        elif cle in CLES_POINTS:
            resultat[cle] = (a - p) * 100
        elif p == 0:
            resultat[cle] = None
        else:
            resultat[cle] = (a - p) / p * 100
    return resultat


def formater_duree(secondes: float | None) -> str:
    """'4 min 12 s', '45 s', '1 h 05 min' ; 'n.d.' si inconnue."""
    if secondes is None or (isinstance(secondes, float) and math.isnan(secondes)):
        return "n.d."
    total = int(round(secondes))
    if total < 60:
        return f"{total} s"
    if total < 3600:
        return f"{total // 60} min {total % 60:02d} s"
    return f"{total // 3600} h {(total % 3600) // 60:02d} min"


def formater_nombre(x, decimales: int = 0, suffixe: str = "") -> str:
    """Format français : espace fine insécable pour les milliers, virgule décimale."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n.d."
    texte = f"{x:,.{decimales}f}"
    texte = texte.replace(",", ESPACE_FINE).replace(".", ",")
    return texte + suffixe
