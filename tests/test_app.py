"""Tests de l'application Streamlit (app.py) avec AppTest, sans navigateur."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
ONGLETS = ["Synthèse", "Temporalité", "Audience", "Engagement", "Conversion", "Données"]
LIBELLES_KPI = [
    "Sessions", "Utilisateurs", "Durée moyenne", "Panier moyen",
    "Taux de conversion", "Part mobile",
]
# Trinité-et-Tobago n'a qu'une session (11 janvier 2021) : aucune en décembre 2020.
PAYS_RARE = "TT"
PERIODE_SANS_SESSION = (date(2020, 12, 1), date(2020, 12, 31))


def _app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60)


def _textes(at: AppTest) -> list[str]:
    """Tous les textes affichés : markdown, légendes, alertes, html."""
    textes = []
    for nom in ("markdown", "caption", "info", "warning", "error", "success", "html"):
        textes.extend(str(e.value) for e in at.get(nom))
    return textes


def _filtres_vides(at: AppTest) -> AppTest:
    at.multiselect(key="f_pays").set_value([PAYS_RARE])
    at.date_input(key="f_periode").set_value(PERIODE_SANS_SESSION)
    return at.run()


def test_app_demarre():
    at = _app().run()
    assert not at.exception
    assert [t.label for t in at.tabs] == ONGLETS
    assert len(at.metric) >= 6
    assert [m.label for m in at.metric[:6]] == LIBELLES_KPI
    assert at.session_state["theme"] == "sombre"


def test_app_kpis_periode_complete():
    at = _app().run()
    valeurs = {m.label: m.value for m in at.metric}
    assert valeurs["Sessions"].replace(chr(0x202F), " ") == "18 101"
    assert valeurs["Panier moyen"] == "65,09 USD"
    assert "$" not in "".join(valeurs.values())


def test_app_theme_clair():
    at = _app()
    at.session_state["theme"] = "clair"
    at.run()
    assert not at.exception
    assert at.session_state["theme"] == "clair"
    assert at.toggle(key="bascule_theme").value is False


def test_app_bascule_theme():
    at = _app().run()
    at.toggle(key="bascule_theme").set_value(False).run()
    assert not at.exception
    assert at.session_state["theme"] == "clair"


def test_app_filtres_vides():
    at = _filtres_vides(_app().run())
    assert not at.exception
    assert any("Aucune donnée" in t for t in _textes(at))
    assert at.metric[0].value == "0"


@pytest.mark.parametrize("onglet", ONGLETS)
def test_app_onglets_sans_erreur(onglet):
    at = _app()
    at.session_state["onglet"] = onglet
    at.run()
    assert not at.exception
    assert at.session_state["onglet"] == onglet


@pytest.mark.parametrize("onglet", ONGLETS)
def test_app_onglets_filtres_vides(onglet):
    at = _app()
    at.session_state["onglet"] = onglet
    at = _filtres_vides(at.run())
    assert not at.exception
    assert any("Aucune donnée" in t for t in _textes(at))


def test_app_bouton_export():
    at = _app().run()
    assert len(at.get("download_button")) >= 1


def test_app_reinitialiser_filtres():
    at = _app().run()
    at.multiselect(key="f_pays").set_value(["US"])
    at.multiselect(key="f_appareils").set_value(["mobile"])
    at.run()
    assert at.metric[0].value.replace(chr(0x202F), " ") != "18 101"
    at.button(key="reinitialiser").click().run()
    assert not at.exception
    assert at.session_state["f_pays"] == []
    assert at.session_state["f_appareils"] == []
    assert at.metric[0].value.replace(chr(0x202F), " ") == "18 101"


def test_app_deltas_sur_periode_courte():
    """Décembre comparé à novembre : les variations s'affichent."""
    at = _app().run()
    at.date_input(key="f_periode").set_value((date(2020, 12, 1), date(2020, 12, 30)))
    at.run()
    assert not at.exception
    deltas = {m.label: m.delta for m in at.metric}
    assert deltas["Sessions"] and deltas["Sessions"].endswith("%")
    assert deltas["Taux de conversion"].endswith("pts")


@pytest.mark.parametrize("onglet", ONGLETS)
def test_app_un_jour_et_categorie(onglet):
    """Période d'un seul jour (sélection en cours) et filtre catégorie : aucun plantage."""
    at = _app()
    at.session_state["onglet"] = onglet
    at.run()
    at.date_input(key="f_periode").set_value((date(2020, 11, 27),))
    at.multiselect(key="f_categories").set_value(["Apparel"])
    at.run()
    assert not at.exception
    assert at.metric[0].value not in ("0", "")
