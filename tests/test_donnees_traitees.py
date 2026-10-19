"""Tests des données traitées produites par notebooks/01_preparation_donnees.ipynb."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_TRAITE = RACINE / "data" / "processed"
FICHIER_EVENTS = DOSSIER_TRAITE / "events_clean.parquet"
FICHIER_SESSIONS = DOSSIER_TRAITE / "sessions.parquet"
DOSSIER_FIGURES = RACINE / "rapport" / "figures"

COLONNES_EVENTS = [
    "user_id", "ga_session_id", "session_key", "country", "country_iso3",
    "country_name", "device", "type", "item_id", "item_name", "item_category",
    "item_brand", "price_in_usd", "timestamp", "date", "hour", "weekday", "month",
]
COLONNES_SESSIONS = [
    "session_key", "user_id", "ga_session_id", "country", "country_iso3",
    "country_name", "device", "start", "end", "date", "hour", "weekday",
    "duration_s", "n_events", "n_items", "cart_value_usd", "revenue_usd",
    "reached_checkout", "purchased", "main_category", "is_outlier_duration",
    "is_outlier_events",
]
FIGURES_ATTENDUES = [
    "evolution_trafic.png", "categories.png", "engagement_appareil.png",
    "heatmap_heure_jour.png", "correlation.png", "entonnoir.png",
]


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    return pd.read_parquet(FICHIER_EVENTS)


@pytest.fixture(scope="module")
def sessions() -> pd.DataFrame:
    return pd.read_parquet(FICHIER_SESSIONS)


def test_fichiers_existent():
    assert FICHIER_EVENTS.is_file()
    assert FICHIER_SESSIONS.is_file()


def test_schema_events(events):
    manquantes = set(COLONNES_EVENTS) - set(events.columns)
    assert not manquantes, f"Colonnes absentes : {manquantes}"
    assert pd.api.types.is_datetime64_any_dtype(events["timestamp"])
    assert pd.api.types.is_datetime64_any_dtype(events["date"])
    assert (events["date"] == events["date"].dt.normalize()).all()
    assert events["hour"].between(0, 23).all()
    assert events["weekday"].between(0, 6).all()
    assert events["month"].str.fullmatch(r"\d{4}-\d{2}").all()


def test_schema_sessions(sessions):
    manquantes = set(COLONNES_SESSIONS) - set(sessions.columns)
    assert not manquantes, f"Colonnes absentes : {manquantes}"
    assert pd.api.types.is_datetime64_any_dtype(sessions["start"])
    assert pd.api.types.is_datetime64_any_dtype(sessions["end"])
    assert pd.api.types.is_bool_dtype(sessions["purchased"])
    assert pd.api.types.is_bool_dtype(sessions["is_outlier_duration"])


def test_aucun_pays_manquant(events, sessions):
    assert events["country"].notna().all()
    assert sessions["country"].notna().all()
    assert len(events[events.country == "(not set)"]) > 0
    non_renseigne = events[events.country == "(not set)"]
    assert (non_renseigne["country_name"] == "(not set)").all()
    assert non_renseigne["country_iso3"].isna().all()


def test_aucun_doublon(events):
    assert events.duplicated().sum() == 0


def test_valeurs_non_traduites(events):
    assert set(events.device) == {"desktop", "mobile", "tablet"}
    assert set(events.type) == {"add_to_cart", "begin_checkout", "purchase"}


def test_coherence_sessions(events, sessions):
    assert sessions.session_key.is_unique
    assert sessions.n_events.sum() == len(events)
    revenu_events = events.loc[events.type == "purchase", "price_in_usd"].sum()
    assert abs(sessions.revenue_usd.sum() - revenu_events) < 1e-6
    assert (sessions.duration_s >= 0).all()
    assert ((sessions.revenue_usd > 0) == sessions.purchased).all()
    assert set(sessions.session_key) == set(events.session_key)


def test_periode(events):
    assert events.timestamp.min() >= pd.Timestamp("2020-11-01")
    assert events.timestamp.max() < pd.Timestamp("2021-02-01")


def test_figures_rapport():
    assert DOSSIER_FIGURES.is_dir()
    absentes = [nom for nom in FIGURES_ATTENDUES if not (DOSSIER_FIGURES / nom).is_file()]
    assert not absentes, f"Figures absentes : {absentes}"


@pytest.mark.parametrize("colonne, indicateur", [
    ("duration_s", "is_outlier_duration"),
    ("n_events", "is_outlier_events"),
])
def test_indicateurs_aberrants_iqr(sessions, colonne, indicateur):
    q1, q3 = sessions[colonne].quantile([0.25, 0.75])
    borne = q3 + 1.5 * (q3 - q1)
    attendu = sessions[colonne] > borne
    assert (sessions[indicateur] == attendu).all()
    assert sessions[indicateur].any()
