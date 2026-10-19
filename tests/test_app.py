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
PAYS_SANS_ACHAT = "IS"  # Islande : 10 sessions, aucun achat
FINE, NBSP = chr(0x202F), chr(0x00A0)
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
    assert at.session_state["theme"] == "clair"  # thème clair par défaut
    assert at.toggle(key="bascule_theme").value is False


def test_app_kpis_periode_complete():
    at = _app().run()
    valeurs = {m.label: m.value for m in at.metric}
    assert valeurs["Sessions"].replace(chr(0x202F), " ") == "18 101"
    assert valeurs["Panier moyen"] == f"65,09{NBSP}USD"  # unité insécable
    assert "$" not in "".join(valeurs.values())


def test_app_theme_sombre():
    """Le thème peut être fixé avant le premier rendu : la bascule le suit."""
    at = _app()
    at.session_state["theme"] = "sombre"
    at.run()
    assert not at.exception
    assert at.session_state["theme"] == "sombre"
    assert at.toggle(key="bascule_theme").value is True


def test_app_bascule_theme():
    """La bascule « Mode sombre » passe du thème clair au sombre, puis revient."""
    at = _app().run()
    at.toggle(key="bascule_theme").set_value(True).run()
    assert not at.exception
    assert at.session_state["theme"] == "sombre"
    at.toggle(key="bascule_theme").set_value(False).run()
    assert not at.exception
    assert at.session_state["theme"] == "clair"


def test_app_theme_inconnu_revient_au_clair():
    at = _app()
    at.session_state["theme"] = "inconnu"
    at.run()
    assert not at.exception
    assert at.session_state["theme"] == "clair"


def test_app_nombre_de_pays_hors_not_set():
    """108 pays : « (not set) » n'est pas compté, et l'aide le précise."""
    at = _app().run()
    reperes = " ".join(_html(at, "al-reperes"))
    assert '<div class="al-repere-valeur">108</div>' in reperes
    assert "(not set)" in reperes
    apropos = " ".join(_html(at, "al-carte al-apropos"))
    assert "108 pays" in apropos and "109" not in apropos
    at.session_state["onglet"] = "Audience"
    at.run()
    assert not at.exception
    legendes = " ".join(_html(at, "al-legende"))
    assert "108 pays" in legendes and "109" not in legendes


def test_app_limite_de_collecte_signalee():
    """Le défaut de collecte du début de période est signalé (barre latérale et carte)."""
    at = _app().run()
    espaces = {ord(FINE): " ", ord(NBSP): " "}
    apropos = " ".join(_html(at, "al-carte al-apropos")).translate(espaces)
    assert "avant le 16 novembre 2020, seuls les achats sont enregistrés" in apropos
    assert "en continu qu'à partir du 25 novembre" in apropos
    assert "variations affichées par défaut" in apropos
    barre = " ".join(_html(at, "al-barre-note")).translate(espaces)
    assert "avant le 16 novembre 2020, seuls les achats sont enregistrés" in barre


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


def _html(at: AppTest, classe: str) -> list[str]:
    return [str(e.value) for e in at.get("html") if f'class="{classe}' in str(e.value)]


def _note_kpi(at: AppTest) -> str:
    return " ".join(_html(at, "al-note-kpi"))


def test_app_variations_par_moities_sur_periode_complete():
    """Période complète : la période précédente sort des données, on compare les moitiés."""
    at = _app().run()
    deltas = {m.label: m.delta for m in at.metric}
    assert deltas["Sessions"].endswith("%")
    assert deltas["Taux de conversion"].endswith("pts")
    note = _note_kpi(at)
    assert "seconde moitié" in note and "première moitié" in note
    assert "17/12/2020" in note and "16/12/2020" in note


def test_app_variations_periode_precedente():
    at = _app().run()
    at.date_input(key="f_periode").set_value((date(2020, 12, 1), date(2020, 12, 30)))
    at.run()
    note = _note_kpi(at)
    assert "période précédente de même durée" in note and "01/11/2020" in note
    assert "moitié" not in note


def test_app_un_jour_sans_variation():
    at = _app().run()
    at.date_input(key="f_periode").set_value((date(2020, 12, 15), date(2020, 12, 15)))
    at.run()
    assert not at.exception
    assert all(not m.delta for m in at.metric)


def test_app_typographie_legendes():
    """Aucune espace sécable avant « % », « : », « ; », « ? » dans les textes rédigés."""
    for onglet in ONGLETS:
        at = _app()
        at.session_state["onglet"] = onglet
        at.run()
        for classe in ("al-legende", "al-note-kpi", "al-grille-constats", "al-section", "al-vide"):
            for texte in _html(at, classe):
                for motif in (" %", " :", " ;", " ?"):
                    assert motif not in texte, (onglet, classe, motif, texte[:160])
        for m in at.metric:
            assert " %" not in m.value and " %" not in (m.delta or "")


def test_app_montants_deux_decimales():
    at = _app()
    at.session_state["onglet"] = "Données"
    at.run()
    tableau = " ".join(_html(at, "al-table-conteneur"))
    assert '<td class="num">31,00</td>' in tableau  # chiffre d'affaires de la 1re session


def test_app_conversion_sans_achat_pas_de_meilleur_taux():
    at = _app()
    at.session_state["onglet"] = "Conversion"
    at.run()
    at.multiselect(key="f_pays").set_value([PAYS_SANS_ACHAT])
    at.run()
    assert not at.exception
    assert not any("meilleur taux" in t for t in _textes(at))


def test_app_engagement_log_par_defaut():
    at = _app()
    at.session_state["onglet"] = "Engagement"
    at.run()
    assert at.toggle(key="eng_log_duration_s").value is True
    at.segmented_control(key="eng_metrique").set_value("n_events").run()
    assert at.toggle(key="eng_log_n_events").value is False
    at.segmented_control(key="eng_metrique").set_value("cart_value_usd").run()
    assert at.toggle(key="eng_log_cart_value_usd").value is True
