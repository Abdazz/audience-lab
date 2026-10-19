"""Constats automatiques de l'onglet Synthèse, calculés sur les données filtrées."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from audience.kpis import formater_nombre, typo

JOURS_FR = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
MOIS_FR = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
)


@dataclass
class Constat:
    """Un constat : titre court, phrase explicative, icône Material (syntaxe Streamlit)."""

    titre: str
    texte: str
    icone: str


def _pct(x: float) -> str:
    return formater_nombre(x * 100, 1, " %")


def _date_fr(jour: pd.Timestamp) -> str:
    premier = "1er" if jour.day == 1 else str(jour.day)
    return f"{premier} {MOIS_FR[jour.month - 1]} {jour.year}"


def _pic_trafic(sessions: pd.DataFrame) -> Constat:
    par_jour = sessions.groupby(sessions["date"].dt.normalize()).size()
    jour = par_jour.idxmax()
    # Moyenne sur tous les jours calendaires de la période observée (jours vides inclus).
    nb_jours = (par_jour.index.max() - par_jour.index.min()).days + 1
    moyenne = len(sessions) / nb_jours
    rapport = par_jour.max() / moyenne
    texte = (
        f"Le pic de trafic a lieu le {_date_fr(jour)} avec "
        f"{formater_nombre(par_jour.max())} sessions, soit "
        f"{formater_nombre(rapport, 1)} fois la moyenne journalière "
        f"({formater_nombre(moyenne, 1)} sessions par jour)."
    )
    return Constat("Pic de trafic", texte, ":material/trending_up:")


def _appareils(sessions: pd.DataFrame) -> Constat:
    mobile = sessions["device"] == "mobile"
    part_sessions = mobile.mean()
    achats = sessions["purchased"]
    nb_achats = int(achats.sum())
    if nb_achats == 0:
        texte = (
            f"Les sessions mobile représentent {_pct(part_sessions)} du trafic, "
            "mais aucun achat n'est enregistré sur cette sélection."
        )
    else:
        part_achats = (mobile & achats).sum() / nb_achats
        ecart = part_achats - part_sessions
        if abs(ecart) < 0.02:
            verdict = "le mobile convertit à peu près comme les autres appareils"
        elif ecart < 0:
            verdict = "le mobile convertit moins bien que les autres appareils"
        else:
            verdict = "le mobile convertit mieux que les autres appareils"
        texte = (
            f"Les sessions mobile représentent {_pct(part_sessions)} du trafic "
            f"mais {_pct(part_achats)} des achats : {verdict}."
        )
    return Constat("Appareils", texte, ":material/smartphone:")


def _moment_fort(sessions: pd.DataFrame) -> Constat:
    creneaux = sessions.groupby(["weekday", "hour"]).size()
    (jour, heure), nb = creneaux.idxmax(), creneaux.max()
    texte = (
        f"{JOURS_FR[int(jour)]} à {int(heure)} h est le créneau le plus actif : "
        f"{formater_nombre(nb)} sessions démarrent sur cette heure "
        f"({_pct(nb / len(sessions))} du total)."
    )
    return Constat("Moment fort", texte, ":material/schedule:")


def _entonnoir(events: pd.DataFrame, sessions: pd.DataFrame) -> Constat | None:
    """Taux conditionnels : add_to_cart -> begin_checkout -> purchase."""
    ev = events[events["session_key"].isin(sessions["session_key"])]
    par_type = {
        t: set(ev.loc[ev["type"] == t, "session_key"])
        for t in ("add_to_cart", "begin_checkout", "purchase")
    }
    panier, paiement, achat = (
        par_type["add_to_cart"], par_type["begin_checkout"], par_type["purchase"],
    )
    if not panier:
        return None
    taux_paiement = len(panier & paiement) / len(panier)
    phrases = [
        f"{_pct(taux_paiement)} des sessions avec add_to_cart atteignent begin_checkout"
    ]
    pertes = {"entre add_to_cart et begin_checkout": 1 - taux_paiement}
    if paiement:
        taux_achat = len(paiement & achat) / len(paiement)
        phrases.append(
            f"{_pct(taux_achat)} des sessions avec begin_checkout vont jusqu'à purchase"
        )
        pertes["entre begin_checkout et purchase"] = 1 - taux_achat
    etape, perte = max(pertes.items(), key=lambda kv: kv[1])
    texte = (
        " puis ".join(phrases)
        + f". La principale perte se situe {etape} ({_pct(perte)} des sessions concernées s'arrêtent à cette étape)."
    )
    return Constat("Entonnoir de conversion", texte, ":material/filter_alt:")


def generer_constats(events: pd.DataFrame, sessions: pd.DataFrame) -> list[Constat]:
    """Jusqu'à 4 constats ; liste vide si aucune session."""
    if len(sessions) == 0:
        return []
    constats = [_pic_trafic(sessions), _appareils(sessions), _moment_fort(sessions)]
    entonnoir = _entonnoir(events, sessions)
    if entonnoir is not None:
        constats.append(entonnoir)
    # Espaces insécables (« 39,9 % », « : 159 sessions », « 13 h ») : pas de coupure fautive.
    return [Constat(typo(c.titre), typo(c.texte), c.icone) for c in constats]
