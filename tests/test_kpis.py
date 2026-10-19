"""Tests des indicateurs clés (audience/kpis.py)."""
from __future__ import annotations

import pandas as pd
import pytest

from audience.kpis import (
    calculer_kpis,
    compter_pays,
    formater_duree,
    formater_nombre,
    typo,
    variations,
)

CLES = {
    "sessions", "utilisateurs", "duree_moyenne_s", "panier_moyen_usd",
    "taux_conversion", "part_mobile", "chiffre_affaires_usd",
}
FINE = chr(0x202F)


@pytest.fixture
def sessions():
    return pd.DataFrame(
        {
            "user_id": [1, 1, 2, 3],
            "device": ["mobile", "desktop", "desktop", "tablet"],
            "duration_s": [10.0, 20.0, 30.0, 40.0],
            "cart_value_usd": [500.0, 0.0, 200.0, 0.0],
            "revenue_usd": [0.0, 0.0, 80.0, 0.0],
            "purchased": [False, False, True, False],
        }
    )


def test_kpis_valeurs(sessions):
    k = calculer_kpis(sessions)
    assert set(k) == CLES
    assert k["sessions"] == 4
    assert k["utilisateurs"] == 3
    assert k["duree_moyenne_s"] == pytest.approx(25.0)
    assert k["part_mobile"] == 0.25
    assert k["taux_conversion"] == 0.25
    assert k["chiffre_affaires_usd"] == pytest.approx(80.0)
    # panier moyen = revenu moyen des sessions avec achat (pas la valeur du panier)
    assert k["panier_moyen_usd"] == pytest.approx(80.0)


def test_panier_moyen_sans_achat(sessions):
    k = calculer_kpis(sessions.assign(revenue_usd=0.0, purchased=False))
    assert k["panier_moyen_usd"] is None
    assert k["taux_conversion"] == 0.0


def test_kpis_vide(sessions):
    k = calculer_kpis(sessions.iloc[0:0])
    assert set(k) == CLES
    assert k["sessions"] == 0 and k["utilisateurs"] == 0
    assert all(v is None for c, v in k.items() if c not in ("sessions", "utilisateurs"))


def test_variations():
    actuel = {"sessions": 110, "utilisateurs": 50, "duree_moyenne_s": 90.0,
              "panier_moyen_usd": None, "taux_conversion": 0.30,
              "part_mobile": 0.40, "chiffre_affaires_usd": 0.0}
    precedent = {"sessions": 100, "utilisateurs": 0, "duree_moyenne_s": 120.0,
                 "panier_moyen_usd": 50.0, "taux_conversion": 0.25,
                 "part_mobile": 0.50, "chiffre_affaires_usd": 200.0}
    v = variations(actuel, precedent)
    assert set(v) == set(actuel)
    assert v["sessions"] == pytest.approx(10.0)
    assert v["utilisateurs"] is None  # précédent nul
    assert v["duree_moyenne_s"] == pytest.approx(-25.0)
    assert v["panier_moyen_usd"] is None  # actuel inconnu
    assert v["taux_conversion"] == pytest.approx(5.0)  # points de pourcentage
    assert v["part_mobile"] == pytest.approx(-10.0)
    assert v["chiffre_affaires_usd"] == pytest.approx(-100.0)


def test_kpis_periode_precedente_vide(sessions):
    v = variations(calculer_kpis(sessions), calculer_kpis(sessions.iloc[0:0]))
    assert set(v) == CLES
    assert all(x is None for x in v.values())


def test_formater_duree():
    assert formater_duree(252) == "4 min 12 s"
    assert formater_duree(45) == "45 s"
    assert formater_duree(3900) == "1 h 05 min"
    assert formater_duree(0) == "0 s"
    assert formater_duree(59.6) == "1 min 00 s"
    assert formater_duree(None) == "n.d."


def test_formater_nombre():
    assert formater_nombre(42318) == f"42{FINE}318"
    assert formater_nombre(63.2, 2, " $") == f"63,20{FINE}$"  # unité insécable
    assert formater_nombre(1234567.891, 1) == f"1{FINE}234{FINE}567,9"
    assert formater_nombre(0) == "0"
    assert formater_nombre(None) == "n.d."


def test_typo_espaces_insecables():
    nbsp = chr(0x00A0)
    texte = typo("Mardi à 13 h : 159 sessions (0,9 %) ; « oui » ? 5 min 41 s, 12 USD, +1,2 pts")
    assert f"13{nbsp}h" in texte and f"{nbsp}: 159" in texte and f"0,9{nbsp}%" in texte
    assert f"{nbsp};" in texte and f"«{nbsp}oui{nbsp}»{nbsp}?" in texte
    assert f"5{nbsp}min{nbsp}41{nbsp}s" in texte and f"12{nbsp}USD" in texte and f"1,2{nbsp}pts" in texte
    assert "159 sessions" in texte  # pas d'unité : espace ordinaire conservée


def test_compter_pays_exclut_not_set():
    """« (not set) » et les valeurs manquantes ne sont pas des pays."""
    serie = pd.Series(["US", "FR", "US", "(not set)", None, "IN"])
    assert compter_pays(serie) == 3
    assert compter_pays(pd.Series([], dtype="object")) == 0
    assert compter_pays(pd.Series(["(not set)"])) == 0
