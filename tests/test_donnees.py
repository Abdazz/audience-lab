"""Tests du chargement et des filtres (audience/donnees.py)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from audience.donnees import (
    Filtres,
    charger_donnees,
    filtrer,
    normaliser_periode,
    periode_precedente,
)


@pytest.fixture
def jeu():
    """3 sessions, 2 appareils, 2 catégories, 2 jours."""
    events = pd.DataFrame(
        {
            "session_key": ["a", "a", "b", "c", "c"],
            "country": ["US", "US", "FR", "US", "US"],
            "device": ["mobile", "mobile", "desktop", "desktop", "desktop"],
            "type": ["add_to_cart", "purchase", "add_to_cart", "add_to_cart", "begin_checkout"],
            "item_category": ["Apparel", "Apparel", "Bags", "Bags", "Bags"],
            "date": pd.to_datetime(
                ["2020-12-01", "2020-12-01", "2020-12-01", "2020-12-02", "2020-12-02"]
            ),
        }
    )
    sessions = pd.DataFrame(
        {
            "session_key": ["a", "b", "c"],
            "country": ["US", "FR", "US"],
            "device": ["mobile", "desktop", "desktop"],
            "date": pd.to_datetime(["2020-12-01", "2020-12-01", "2020-12-02"]),
        }
    )
    return events, sessions


def _f(**kw):
    base = dict(
        debut=date(2020, 12, 1), fin=date(2020, 12, 2),
        appareils=(), pays=(), categories=(),
    )
    base.update(kw)
    return Filtres(**base)


def test_filtres_vides_ne_filtrent_pas(jeu):
    ev, se = filtrer(*jeu, _f())
    assert len(ev) == 5 and len(se) == 3


def test_filtrer_periode(jeu):
    ev, se = filtrer(*jeu, _f(debut=date(2020, 12, 2), fin=date(2020, 12, 2)))
    assert list(se.session_key) == ["c"]
    assert set(ev.session_key) == {"c"}
    ev, se = filtrer(*jeu, _f(debut=date(2020, 12, 1), fin=date(2020, 12, 1)))
    assert set(se.session_key) == {"a", "b"}  # bornes incluses


def test_filtrer_appareil(jeu):
    ev, se = filtrer(*jeu, _f(appareils=("mobile",)))
    assert list(se.session_key) == ["a"]
    assert set(ev.device) == {"mobile"}


def test_filtrer_pays(jeu):
    ev, se = filtrer(*jeu, _f(pays=("FR",)))
    assert list(se.session_key) == ["b"]


def test_filtrer_categorie_restreint_sessions(jeu):
    ev, se = filtrer(*jeu, _f(categories=("Apparel",)))
    assert set(ev.item_category) == {"Apparel"}
    assert list(se.session_key) == ["a"]


def test_normaliser_periode_un_jour():
    d = date(2020, 12, 5)
    defaut = (date(2020, 11, 1), date(2021, 1, 31))
    assert normaliser_periode((d,), defaut) == (d, d)


def test_normaliser_periode_vide():
    defaut = (date(2020, 11, 1), date(2021, 1, 31))
    assert normaliser_periode((), defaut) == defaut


def test_normaliser_periode_inversee():
    defaut = (date(2020, 11, 1), date(2021, 1, 31))
    a, b = date(2020, 12, 9), date(2020, 12, 3)
    assert normaliser_periode((a, b), defaut) == (b, a)


def test_periode_precedente():
    p = periode_precedente(
        _f(debut=date(2020, 12, 1), fin=date(2020, 12, 7), appareils=("mobile",))
    )
    assert (p.debut, p.fin) == (date(2020, 11, 24), date(2020, 11, 30))
    assert p.appareils == ("mobile",)


def test_charger_donnees():
    events, sessions = charger_donnees()
    assert len(events) > 0 and len(sessions) > 0
