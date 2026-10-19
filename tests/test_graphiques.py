"""Tests des graphiques Plotly (audience/graphiques.py)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from audience import graphiques as g
from audience.donnees import charger_donnees
from audience.theme import THEMES


@pytest.fixture(scope="module")
def donnees():
    return charger_donnees()


def _constructeurs(events, sessions):
    """Une fabrique par figure : nom -> fonction(theme) -> Figure."""
    return {
        "evolution": lambda t: g.fig_evolution(sessions, theme=t),
        "evolution_semaine_appareil": lambda t: g.fig_evolution(
            sessions, granularite="W", par_appareil=True, theme=t
        ),
        "heatmap": lambda t: g.fig_heatmap_heure_jour(sessions, theme=t),
        "parts_appareils": lambda t: g.fig_parts_appareils(sessions, theme=t),
        "categories_panier": lambda t: g.fig_categories(events, "add_to_cart", theme=t),
        "categories_ca": lambda t: g.fig_categories(events, "revenue", theme=t),
        "carte_pays": lambda t: g.fig_carte_pays(sessions, theme=t),
        "top_pays": lambda t: g.fig_top_pays(sessions, theme=t),
        "boite": lambda t: g.fig_engagement_boite(sessions, "duration_s", False, theme=t),
        "boite_log": lambda t: g.fig_engagement_boite(sessions, "cart_value_usd", True, theme=t),
        "densite": lambda t: g.fig_engagement_densite(sessions, "n_events", False, theme=t),
        "densite_log": lambda t: g.fig_engagement_densite(sessions, "duration_s", True, theme=t),
        "entonnoir": lambda t: g.fig_entonnoir(sessions, events, theme=t),
    }


@pytest.mark.parametrize("nom_theme", ["sombre", "clair"])
def test_figures_suivent_theme(donnees, nom_theme):
    events, sessions = donnees
    theme = THEMES[nom_theme]
    for nom, fabrique in _constructeurs(events, sessions).items():
        fig = fabrique(theme)
        assert fig.layout.paper_bgcolor == theme.surface, nom
        assert fig.layout.font.color == theme.texte, nom
        assert len(fig.data) > 0, nom


def test_figures_df_vide(donnees):
    events, sessions = donnees
    vides = _constructeurs(events.iloc[0:0], sessions.iloc[0:0])
    for theme in THEMES.values():
        for nom, fabrique in vides.items():
            fig = fabrique(theme)
            textes = [a.text for a in fig.layout.annotations]
            assert any("Aucune donnée pour ces filtres" in t for t in textes), nom
            assert fig.layout.paper_bgcolor == theme.surface, nom


def test_heatmap_grille_complete(donnees):
    _, sessions = donnees
    un_jour = sessions[sessions["date"] == "2020-11-27"]
    fig = g.fig_heatmap_heure_jour(un_jour, theme=THEMES["sombre"])
    z = np.asarray(fig.data[0].z)
    assert z.shape == (7, 24)
    assert z.sum() == len(un_jour)
    assert list(fig.data[0].y) == ["Lundi", "Mardi", "Mercredi", "Jeudi",
                                   "Vendredi", "Samedi", "Dimanche"]
    # 2020-11-27 est un vendredi : les autres lignes sont des zéros.
    assert z[[0, 1, 2, 3, 5, 6]].sum() == 0


def test_evolution_annotations(donnees):
    _, sessions = donnees
    fig = g.fig_evolution(sessions, theme=THEMES["sombre"])
    assert len(fig.layout.annotations) == 3
    textes = " ".join(a.text for a in fig.layout.annotations)
    for libelle in ("Black Friday", "Cyber Monday", "Noël"):
        assert libelle in textes
    # Période sans aucun des trois événements : pas d'annotation.
    janvier = sessions[sessions["date"] >= "2021-01-01"]
    fig = g.fig_evolution(janvier, theme=THEMES["clair"])
    assert len(fig.layout.annotations) == 0


def test_evolution_semaine_moins_de_points(donnees):
    _, sessions = donnees
    jour = g.fig_evolution(sessions, "D", theme=THEMES["sombre"])
    semaine = g.fig_evolution(sessions, "W", theme=THEMES["sombre"])
    assert len(semaine.data[0].x) < len(jour.data[0].x)
    assert sum(semaine.data[0].y) == len(sessions)


def test_types_traces(donnees):
    events, sessions = donnees
    fabriques = _constructeurs(events, sessions)
    attendus = {
        "evolution": "scatter",
        "heatmap": "heatmap",
        "parts_appareils": "pie",
        "categories_panier": "bar",
        "carte_pays": "choropleth",
        "top_pays": "bar",
        "boite": "box",
        "densite": "histogram",
        "entonnoir": "funnel",
    }
    for nom, type_trace in attendus.items():
        fig = fabriques[nom](THEMES["sombre"])
        assert fig.data[0].type == type_trace, nom
        types = {trace.type for trace in fig.data}
        # Les boîtes portent en plus des points invisibles (info-bulles en français).
        autorises = {type_trace, "scatter"} if type_trace == "box" else {type_trace}
        assert types <= autorises, nom


def test_categories_top_12_trie(donnees):
    events, _ = donnees
    fig = g.fig_categories(events, "revenue", theme=THEMES["sombre"])
    barre = fig.data[0]
    assert barre.orientation == "h"
    assert len(barre.y) <= 12
    valeurs = list(barre.x)
    achats = events[events["type"] == "purchase"]
    attendu = achats.groupby("item_category")["price_in_usd"].sum().max()
    assert max(valeurs) == pytest.approx(attendu)


def test_entonnoir_sessions_par_etape(donnees):
    events, sessions = donnees
    fig = g.fig_entonnoir(sessions, events, theme=THEMES["sombre"])
    total = {}
    for trace in fig.data:
        for etape, valeur in zip(trace.y, trace.x):
            total[etape] = total.get(etape, 0) + valeur
    attendu = events.groupby("type")["session_key"].nunique()
    for etape in ("add_to_cart", "begin_checkout", "purchase"):
        assert total[etape] == attendu[etape]
    assert {trace.name for trace in fig.data} <= {"desktop", "mobile", "tablet"}


def test_top_pays_dix_barres(donnees):
    _, sessions = donnees
    fig = g.fig_top_pays(sessions, theme=THEMES["clair"])
    assert len(fig.data[0].y) == 10
