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
    periode_de_reference,
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


DEBUT_DONNEES = date(2020, 11, 1)


def test_reference_periode_precedente_couverte():
    """Du 1er au 30 décembre : la période précédente (novembre) est dans les données."""
    f = Filtres(date(2020, 12, 1), date(2020, 12, 30), appareils=("mobile",))
    comparee, reference, mode = periode_de_reference(f, DEBUT_DONNEES)
    assert mode == "precedente"
    assert comparee == f
    assert reference == periode_precedente(f)
    assert reference.appareils == ("mobile",)


def test_reference_moities_si_precedente_hors_donnees():
    """Période complète (92 jours) : seconde moitié contre première moitié."""
    f = Filtres(date(2020, 11, 1), date(2021, 1, 31), pays=("US",))
    comparee, reference, mode = periode_de_reference(f, DEBUT_DONNEES)
    assert mode == "moities"
    assert (reference.debut, reference.fin) == (date(2020, 11, 1), date(2020, 12, 16))
    assert (comparee.debut, comparee.fin) == (date(2020, 12, 17), date(2021, 1, 31))
    assert comparee.pays == reference.pays == ("US",)


def test_reference_moities_si_precedente_partiellement_hors_donnees():
    """Du 10 au 30 novembre : la période précédente commencerait le 19 octobre."""
    f = Filtres(date(2020, 11, 10), date(2020, 11, 30))
    comparee, reference, mode = periode_de_reference(f, DEBUT_DONNEES)
    assert mode == "moities"
    # 21 jours : deux moitiés de 10 jours, le jour du milieu (20 novembre) n'est pas comparé.
    assert (reference.debut, reference.fin) == (date(2020, 11, 10), date(2020, 11, 19))
    assert (comparee.debut, comparee.fin) == (date(2020, 11, 21), date(2020, 11, 30))


def test_reference_deux_jours():
    f = Filtres(date(2020, 11, 1), date(2020, 11, 2))
    comparee, reference, mode = periode_de_reference(f, DEBUT_DONNEES)
    assert mode == "moities"
    assert (reference.debut, reference.fin) == (date(2020, 11, 1), date(2020, 11, 1))
    assert (comparee.debut, comparee.fin) == (date(2020, 11, 2), date(2020, 11, 2))


def test_reference_un_jour_sans_comparaison():
    for jour in (date(2020, 11, 1), date(2020, 12, 15)):
        f = Filtres(jour, jour)
        _, _, mode = periode_de_reference(f, DEBUT_DONNEES)
        assert mode == "aucune"
