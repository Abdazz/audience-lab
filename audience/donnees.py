"""Chargement des données traitées et filtres de la barre latérale."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_EVENTS = RACINE / "data" / "processed" / "events_clean.parquet"
CHEMIN_SESSIONS = RACINE / "data" / "processed" / "sessions.parquet"


def charger_donnees() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lit les deux fichiers parquet : (events, sessions)."""
    return pd.read_parquet(CHEMIN_EVENTS), pd.read_parquet(CHEMIN_SESSIONS)


@dataclass(frozen=True)
class Filtres:
    """Critères de la barre latérale. Un tuple vide signifie : pas de filtre."""

    debut: date
    fin: date
    appareils: tuple[str, ...] = ()
    pays: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()


def normaliser_periode(valeur, defaut: tuple[date, date]) -> tuple[date, date]:
    """Rend (début, fin) à partir de la sortie brute de st.date_input."""
    if isinstance(valeur, date):
        valeur = (valeur,)
    dates = tuple(valeur or ())
    if len(dates) == 0:
        return defaut
    if len(dates) == 1:
        return (dates[0], dates[0])
    debut, fin = dates[0], dates[1]
    return (fin, debut) if debut > fin else (debut, fin)


def _masque_commun(df: pd.DataFrame, f: Filtres) -> pd.Series:
    jours = df["date"].dt.normalize()
    masque = (jours >= pd.Timestamp(f.debut)) & (jours <= pd.Timestamp(f.fin))
    if f.appareils:
        masque &= df["device"].isin(f.appareils)
    if f.pays:
        masque &= df["country"].isin(f.pays)
    return masque


def filtrer(
    events: pd.DataFrame, sessions: pd.DataFrame, f: Filtres
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Applique les filtres aux deux tables (catégories : via les événements)."""
    ev = events[_masque_commun(events, f)]
    se = sessions[_masque_commun(sessions, f)]
    if f.categories:
        ev = ev[ev["item_category"].isin(f.categories)]
        se = se[se["session_key"].isin(ev["session_key"].unique())]
    return ev, se


def periode_precedente(f: Filtres) -> Filtres:
    """Période de même durée, terminée la veille du début de f."""
    duree = f.fin - f.debut
    fin = f.debut - timedelta(days=1)
    return replace(f, debut=fin - duree, fin=fin)
