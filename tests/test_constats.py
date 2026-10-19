"""Tests des constats automatiques (audience/constats.py)."""
from __future__ import annotations

import re

import pandas as pd
import pytest

from audience.constats import Constat, generer_constats

ESPACES = {chr(0x202F): " ", chr(0x00A0): " "}


def _n(texte: str) -> str:
    """Texte avec espaces insécables ramenées à des espaces simples (comparaisons lisibles)."""
    for espace, simple in ESPACES.items():
        texte = texte.replace(espace, simple)
    return texte


JOURS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")


@pytest.fixture
def jeu():
    """6 sessions sur 3 jours (le 2020-12-02 est un mercredi, pic de trafic)."""
    dates = pd.to_datetime(
        ["2020-12-01", "2020-12-02", "2020-12-02", "2020-12-02", "2020-12-02", "2020-12-03"]
    )
    sessions = pd.DataFrame(
        {
            "session_key": list("abcdef"),
            "device": ["mobile", "desktop", "mobile", "desktop", "desktop", "mobile"],
            "date": dates,
            "weekday": dates.weekday,
            "hour": [10, 14, 14, 14, 9, 14],
            "purchased": [False, True, False, False, False, False],
        }
    )
    events = pd.DataFrame(
        {
            "session_key": ["a", "a", "b", "b", "b", "c", "c", "d", "e"],
            "type": [
                "add_to_cart", "begin_checkout",
                "add_to_cart", "begin_checkout", "purchase",
                "add_to_cart", "begin_checkout",
                "add_to_cart", "add_to_cart",
            ],
        }
    )
    return events, sessions


def test_constats_quatre(jeu):
    constats = generer_constats(*jeu)
    assert len(constats) == 4
    for c in constats:
        assert isinstance(c, Constat)
        assert c.titre and c.texte and c.icone


def test_constats_vide(jeu):
    events, sessions = jeu
    assert generer_constats(events, sessions.iloc[0:0]) == []


def test_constats_pic_de_trafic(jeu):
    pic = generer_constats(*jeu)[0]
    assert "2 décembre 2020" in _n(pic.texte)
    assert "4 sessions" in _n(pic.texte)
    assert "2,0" in pic.texte  # 4 sessions pour une moyenne de 2 par jour


def test_constats_appareils(jeu):
    texte = _n(generer_constats(*jeu)[1].texte)
    assert "mobile" in texte
    assert "50,0 %" in texte  # 3 sessions mobile sur 6
    assert "0,0 %" in texte  # aucun achat mobile


def test_constats_jour_en_francais(jeu):
    texte = _n(generer_constats(*jeu)[2].texte)
    assert any(j in texte for j in JOURS)
    assert "Mercredi" in texte and "14 h" in texte


def test_constats_entonnoir_taux_conditionnels(jeu):
    texte = _n(generer_constats(*jeu)[3].texte)
    # 5 sessions avec add_to_cart, 3 vont jusqu'à begin_checkout (60,0 %),
    # puis 1 sur 3 achète (33,3 %).
    assert "60,0 %" in texte and "33,3 %" in texte
    assert "add_to_cart" in texte and "begin_checkout" in texte and "purchase" in texte


def test_constats_entonnoir_absent_sans_add_to_cart(jeu):
    events, sessions = jeu
    sans = events[events.type != "add_to_cart"]
    constats = generer_constats(sans, sessions)
    assert len(constats) == 3


def test_constats_sans_cadratin(jeu):
    for c in generer_constats(*jeu):
        assert chr(0x2014) not in c.titre + c.texte + c.icone


def test_constats_typographie_francaise(jeu):
    """Pas d'espace sécable avant « % », « : » ou « ; », ni entre un nombre et « h »."""
    for c in generer_constats(*jeu):
        for motif in (" %", " :", " ;", " ?"):
            assert motif not in c.texte, (motif, c.texte)
        assert not re.search(r"\d h\b", c.texte)
