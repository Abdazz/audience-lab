"""Tests des thèmes visuels (audience/theme.py)."""
from __future__ import annotations

import plotly.graph_objects as go

from audience.theme import THEMES, Theme, appliquer_theme, css, obtenir_theme


def test_obtenir_theme_defaut():
    assert obtenir_theme("sombre").nom == "sombre"
    assert obtenir_theme("clair").nom == "clair"
    assert obtenir_theme("inconnu").nom == "clair"  # thème par défaut
    assert set(THEMES) == {"sombre", "clair"}
    assert all(isinstance(t, Theme) for t in THEMES.values())


def test_valeurs_imposees():
    sombre, clair = THEMES["sombre"], THEMES["clair"]
    assert (sombre.fond, sombre.surface, sombre.bordure) == ("#0B1020", "#141B35", "#232D55")
    assert (clair.fond, clair.surface, clair.texte) == ("#F5F7FB", "#FFFFFF", "#0F172A")
    assert sombre.couleurs_appareils == {
        "desktop": "#8B5CF6", "mobile": "#22D3EE", "tablet": "#F472B6"
    }
    assert clair.couleurs_appareils == {
        "desktop": "#4F46E5", "mobile": "#0EA5E9", "tablet": "#F59E0B"
    }


def test_css_contient_couleurs():
    feuille_sombre = css(obtenir_theme("sombre"))
    feuille_claire = css(obtenir_theme("clair"))
    assert "#0B1020" in feuille_sombre
    assert "#F5F7FB" in feuille_claire
    for feuille in (feuille_sombre, feuille_claire):
        assert feuille.lstrip().startswith("<style>")
        assert "Inter" in feuille
        assert '[data-testid="stMetric"]' in feuille
        assert ".al-carte" in feuille
        # Base native claire : les info-bulles natives doivent suivre le thème actif.
        assert '[data-testid="stTooltipContent"]' in feuille


def test_appliquer_theme():
    for theme in THEMES.values():
        fig = appliquer_theme(go.Figure(go.Bar(x=[1, 2], y=[3, 4])), theme)
        assert fig.layout.paper_bgcolor == theme.surface
        assert fig.layout.plot_bgcolor == theme.surface
        assert fig.layout.font.color == theme.texte
        assert fig.layout.separators == ", "
