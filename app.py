"""Audience Lab : tableau de bord de l'audience de la Google Merchandise Store.

Point d'entrée Streamlit (``streamlit run app.py``). Les calculs vivent dans le
paquet ``audience`` (données, indicateurs, constats, thèmes, graphiques) ; ce
fichier assemble l'interface, de haut en bas :

1. configuration de la page et état de session ;
2. chargement des données, mis en cache ;
3. thème (clair par défaut, bascule vers le sombre) et feuille de style ;
4. barre latérale : filtres, réinitialisation, export CSV, source ;
5. en-tête et bandeau des six indicateurs clés ;
6. six onglets : Synthèse, Temporalité, Audience, Engagement, Conversion, Données ;
7. pied de page.

Interface en français ; les valeurs de données (desktop, add_to_cart, Apparel,
codes pays...) restent dans leur langue d'origine.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from audience import graphiques as g
from audience.constats import JOURS_FR, MOIS_FR, Constat, generer_constats
from audience.donnees import (
    Filtres, charger_donnees, filtrer, normaliser_periode, periode_de_reference,
)
from audience.kpis import (
    CLES_POINTS, PAYS_NON_IDENTIFIE, calculer_kpis, compter_pays, formater_duree,
    formater_nombre, typo, variations,
)
from audience.theme import THEMES, Theme, css, obtenir_theme

# ---------------------------------------------------------------------------
# 1. Configuration de la page et constantes
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Audience Lab",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

ONGLETS = ["Synthèse", "Temporalité", "Audience", "Engagement", "Conversion", "Données"]
CLES_FILTRES = ("f_periode", "f_appareils", "f_pays", "f_categories")
NOM_EXPORT = "audience_lab_sessions_filtrees.csv"
LIGNES_APERCU = 500
NBSP = chr(0xA0)  # espace insécable (guillemets français)

SOUS_TITRE = "Audience de la Google Merchandise Store · novembre 2020 à janvier 2021"
PIED = (
    "Abdoul-Aziz ZOROM · Master 1 IA, Université Aube-Nouvelle · "
    "Visualisation de données (Dr. Zakaria Sawadogo) · "
    "Données : Google Merchandise Store (GA4, démo publique)"
)

GRANULARITES = {"Jour": "D", "Semaine": "W"}
METRIQUES_CATEGORIES = {"add_to_cart": "Ajouts au panier", "revenue": "Chiffre d'affaires"}
METRIQUES_ENGAGEMENT = {
    "duration_s": "Durée de session",
    "n_events": "Actions par session",
    "cart_value_usd": "Valeur du panier",
}

# Indicateurs du bandeau : clé de calculer_kpis, libellé, icône, définition.
INDICATEURS = (
    ("sessions", "Sessions", ":material/bar_chart:",
     "Nombre de sessions (visites) distinctes : un utilisateur et un identifiant "
     "de session GA4. Variation en % par rapport à la période précédente."),
    ("utilisateurs", "Utilisateurs", ":material/group:",
     "Nombre d'utilisateurs distincts ayant au moins une session dans la sélection. "
     "Variation en %."),
    ("duree_moyenne_s", "Durée moyenne", ":material/timer:",
     "Durée moyenne d'une session : temps écoulé entre son premier et son dernier "
     "événement (0 s pour une session d'un seul horodatage). Variation en %."),
    ("panier_moyen_usd", "Panier moyen", ":material/shopping_cart:",
     "Montant moyen d'une session avec achat : somme des prix des articles achetés "
     "(purchase), en USD. Variation en %."),
    ("taux_conversion", "Taux de conversion", ":material/conversion_path:",
     "Part des sessions comportant au moins un achat (purchase). "
     "Variation en points de pourcentage (pts)."),
    ("part_mobile", "Part mobile", ":material/smartphone:",
     "Part des sessions réalisées sur un appareil mobile. "
     "Variation en points de pourcentage (pts)."),
)

# Colonnes de l'aperçu (onglet Données) et leur en-tête français.
COLONNES_APERCU = {
    "session_key": "Session",
    "start": "Début",
    "device": "Appareil",
    "country": "Pays",
    "main_category": "Catégorie principale",
    "duration_s": "Durée (s)",
    "n_events": "Actions",
    "n_items": "Articles distincts",
    "cart_value_usd": "Valeur panier (USD)",
    "revenue_usd": "Chiffre d'affaires (USD)",
    "reached_checkout": "Paiement commencé",
    "purchased": "Achat",
}
COLONNES_NUMERIQUES = {"duration_s", "n_events", "n_items", "cart_value_usd", "revenue_usd"}
COLONNES_MONTANTS = {"cart_value_usd", "revenue_usd"}  # toujours deux décimales
METRIQUES_LOG_PAR_DEFAUT = {"duration_s", "cart_value_usd"}  # longues traînes
COLONNES_BOOLEENNES = {"reached_checkout", "purchased"}

# Styles propres à la mise en page de app.py ; ils réutilisent les variables
# CSS du thème (--al-*) définies par audience.theme.css().
CSS_APP = """
<style>
/* En-tête : carte large qui contient le titre et la bascule de thème */
.st-key-al_entete {
  background: var(--al-surface); border: 1px solid var(--al-bordure);
  border-radius: 18px; padding: 1.35rem 1.6rem 1.25rem; box-shadow: var(--al-ombre);
  position: relative; overflow: hidden; margin-bottom: 0.35rem;
}
.st-key-al_entete::after {
  content: ""; position: absolute; right: -90px; top: -110px; width: 320px; height: 320px;
  background: var(--al-degrade); opacity: 0.16; filter: blur(48px); border-radius: 50%;
  pointer-events: none;
}
.st-key-al_entete [data-testid="stCheckbox"] { justify-content: flex-end; }
.al-surtitre {
  font-size: 0.74rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--al-accent-2) !important; margin-bottom: 0.3rem;
}
.al-puces { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.95rem; }
.al-puce {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.28rem 0.75rem; border-radius: 999px;
  background: var(--al-accent-doux); border: 1px solid var(--al-bordure);
  font-size: 0.8rem; color: var(--al-texte-2) !important; line-height: 1.3;
}
.al-puce b { color: var(--al-texte) !important; font-weight: 700; }
.al-puce .material-symbols-rounded { font-size: 1rem; color: var(--al-accent-2) !important; }

/* Icônes Material Symbols (police fournie par Streamlit) */
.material-symbols-rounded {
  font-family: "Material Symbols Rounded" !important; font-weight: normal; font-style: normal;
  font-size: 1.3rem; line-height: 1; letter-spacing: normal; text-transform: none;
  display: inline-block; white-space: nowrap; direction: ltr;
  -webkit-font-smoothing: antialiased; font-feature-settings: "liga";
}

/* Note sous le bandeau d'indicateurs */
.al-note-kpi {
  display: flex; align-items: center; gap: 0.45rem;
  color: var(--al-texte-2) !important; font-size: 0.82rem; margin: 0.15rem 0 0.4rem 0.2rem;
}
.al-note-kpi .material-symbols-rounded { font-size: 1.05rem; color: var(--al-accent) !important; }
.al-note-kpi b { color: var(--al-texte) !important; font-weight: 600; }

/* Titres de section dans les onglets et dans la barre latérale */
.al-section { margin: 0.2rem 0 0.8rem; }
.al-section-titre {
  font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; color: var(--al-texte) !important;
}
.al-section-texte { font-size: 0.86rem; color: var(--al-texte-2) !important; margin-top: 0.15rem; }
.al-etiquette {
  display: inline-flex; align-items: center; gap: 0.35rem; margin: 0 0 0.45rem 0.1rem;
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--al-accent) !important;
}
.al-etiquette::before {
  content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--al-degrade);
}
.al-barre-titre {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--al-texte-2) !important; margin: 0.6rem 0 0.2rem;
}
.al-logo-sous { font-size: 0.8rem; color: var(--al-texte-2) !important; margin: -0.1rem 0 0.4rem; }
.al-barre-note { font-size: 0.78rem; line-height: 1.55; color: var(--al-texte-2) !important; }
.al-barre-note b { color: var(--al-texte) !important; font-weight: 600; }

/* Constats en grille adaptative */
.al-grille-constats {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;
}
.al-grille-constats .al-constat { margin: 0; height: 100%; box-sizing: border-box; }
.al-constat-icone .material-symbols-rounded { font-size: 1.35rem; }

/* Carte « À propos des données » et repères */
.al-apropos h4 {
  margin: 0 0 0.7rem; font-size: 1rem; font-weight: 700; color: var(--al-texte) !important;
  display: flex; align-items: center; gap: 0.45rem;
}
.al-apropos h4 .material-symbols-rounded { color: var(--al-accent) !important; font-size: 1.2rem; }
.al-apropos dl { margin: 0; }
.al-apropos dt {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--al-texte-2) !important; margin-top: 0.75rem;
}
.al-apropos dd { margin: 0.15rem 0 0; font-size: 0.88rem; line-height: 1.5; color: var(--al-texte) !important; }
.al-apropos ul { margin: 0.2rem 0 0; padding-left: 1.1rem; }
.al-apropos li { font-size: 0.86rem; line-height: 1.5; color: var(--al-texte) !important; margin: 0.15rem 0; }
.al-reperes { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem; }
.al-repere {
  background: var(--al-surface); border: 1px solid var(--al-bordure); border-radius: 12px;
  padding: 0.75rem 0.9rem; box-shadow: var(--al-ombre);
}
.al-repere-valeur { font-size: 1.2rem; font-weight: 800; letter-spacing: -0.02em; color: var(--al-texte) !important; }
.al-repere-libelle { font-size: 0.75rem; color: var(--al-texte-2) !important; margin-top: 0.1rem; }
.al-repere-note { font-size: 0.68rem; color: var(--al-texte-2) !important; opacity: 0.85; }

/* État vide */
.al-vide {
  display: flex; flex-direction: column; align-items: center; text-align: center; gap: 0.5rem;
  background: var(--al-surface); border: 1px dashed var(--al-bordure); border-radius: var(--al-rayon);
  padding: 2.6rem 1.5rem; margin: 0.5rem 0 1rem;
}
.al-vide .material-symbols-rounded {
  font-size: 2rem; width: 3.4rem; height: 3.4rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--al-accent-doux); color: var(--al-accent) !important;
}
.al-vide-titre { font-size: 1.1rem; font-weight: 700; color: var(--al-texte) !important; }
.al-vide-texte { font-size: 0.9rem; color: var(--al-texte-2) !important; max-width: 520px; line-height: 1.55; }

/* Conversion par appareil */
.al-conv { display: flex; flex-direction: column; gap: 0.75rem; }
.al-conv-carte {
  background: var(--al-surface); border: 1px solid var(--al-bordure); border-radius: var(--al-rayon);
  padding: 0.95rem 1.1rem; box-shadow: var(--al-ombre);
}
.al-conv-haut { display: flex; align-items: baseline; justify-content: space-between; gap: 0.5rem; }
.al-conv-appareil { font-weight: 600; font-size: 0.92rem; color: var(--al-texte) !important; display: flex; align-items: center; gap: 0.45rem; }
.al-conv-taux { font-weight: 800; font-size: 1.35rem; letter-spacing: -0.02em; color: var(--al-texte) !important; }
.al-conv-barre { height: 6px; border-radius: 999px; background: var(--al-bordure); margin: 0.55rem 0 0.45rem; overflow: hidden; }
.al-conv-barre > div { height: 100%; border-radius: 999px; }
.al-conv-detail { font-size: 0.78rem; color: var(--al-texte-2) !important; }
.al-point { display: inline-block; width: 9px; height: 9px; border-radius: 50%; flex: 0 0 9px; }

/* Tableau HTML de l'onglet Données */
.al-table-entete { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.al-table-conteneur {
  max-height: 560px; overflow: auto; border: 1px solid var(--al-bordure);
  border-radius: var(--al-rayon); background: var(--al-surface); box-shadow: var(--al-ombre);
}
table.al-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.8rem; }
.al-table th {
  position: sticky; top: 0; z-index: 1; background: var(--al-surface);
  text-align: left; padding: 0.6rem 0.6rem; white-space: normal; line-height: 1.3; vertical-align: bottom;
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--al-texte-2) !important; border-bottom: 1px solid var(--al-bordure);
  box-shadow: 0 1px 0 var(--al-bordure);
}
.al-table td {
  padding: 0.45rem 0.6rem; white-space: nowrap; color: var(--al-texte) !important;
  border-bottom: 1px solid var(--al-bordure); font-variant-numeric: tabular-nums;
}
.al-table tbody tr:nth-child(even) td { background: color-mix(in srgb, var(--al-accent) 5%, transparent); }
.al-table tbody tr:hover td { background: var(--al-survol); }
.al-table .num { text-align: right; }
.al-table .centre { text-align: center; }
.al-table .code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace !important; font-size: 0.78rem; color: var(--al-texte-2) !important; }
.al-oui { color: var(--al-positif) !important; font-weight: 700; }
.al-non { color: var(--al-texte-2) !important; opacity: 0.6; }
.al-appareil { display: inline-flex; align-items: center; gap: 0.4rem; }

/* Rangée de contrôles locaux au-dessus des graphiques */
.st-key-controles_temporalite, .st-key-controles_engagement { margin-bottom: 0.35rem; }

/* Cartes KPI : marges resserrées pour six cartes de front, petites courbes thémées */
[data-testid="stMainBlockContainer"] { padding-left: 2.5rem; padding-right: 2.5rem; }
[data-testid="stMetric"] { padding: 0.9rem 0.95rem 0.7rem !important; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { font-size: 0.8rem !important; }
/* Libellés sur deux lignes au besoin (écrans étroits, projection) : hauteur réservée
   identique pour toutes les cartes afin que les valeurs restent alignées. */
[data-testid="stMetricLabel"] { min-height: 2.5em; align-items: flex-start !important; }
[data-testid="stMetricLabel"] .stMarkdownEllipsis, [data-testid="stMetricLabel"] .stMarkdownEllipsis * {
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
  line-height: 1.25 !important;
}
[data-testid="stMetricChart"] svg { background-color: transparent !important; }
/* Courbe grise (aucune variation comparable) : on la passe aux couleurs du thème */
[data-testid="stMetricChart"] .mark-area path[fill="rgba(128, 132, 149, 0.2)"] {
  fill: var(--al-accent) !important; fill-opacity: 0.16;
}
[data-testid="stMetricChart"] .mark-line path[stroke="#555867"] {
  stroke: var(--al-accent) !important; stroke-width: 1.6px;
}
[data-testid="stMetricChart"] .mark-symbol path[stroke="#555867"] { stroke: var(--al-accent) !important; }

/* Constats : texte un peu plus compact que le corps de page */
.al-grille-constats .al-constat p { font-size: 0.9rem; }
.al-grille-constats .al-constat-titre { font-size: 0.98rem; }

/* L'icône d'aide du champ de dates ne doit pas être remplie par la règle des svg du champ */
[data-testid="stDateInput"] [data-testid="stTooltipIcon"] svg, [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"] svg {
  fill: none !important;
}

/* Icônes d'aide « ? » lisibles dans les deux thèmes */
[data-testid="stTooltipIcon"] svg, [data-testid="stTooltipHoverTarget"] svg {
  color: var(--al-texte-2) !important; stroke: currentColor !important; opacity: 0.85;
}
/* Pas d'anneau de focus après un clic de souris sur un onglet (clavier : conservé) */
.stTabs [role="tab"]:focus:not(:focus-visible) { outline: none !important; box-shadow: none !important; }
/* Interrupteur éteint : piste assez contrastée sur fond clair */
[data-testid="stCheckbox"] label:not([data-selected]) > div:not([data-testid]) {
  background-color: color-mix(in srgb, var(--al-texte-2) 45%, transparent) !important;
}
/* Bouton secondaire : l'icône suit la couleur du texte (et non le blanc des boutons pleins) */
.stButton button[kind="secondary"] span, .stButton button[data-testid="stBaseButton-secondary"] span {
  color: var(--al-texte) !important;
}

/* Pied de page : séparateurs plus discrets */
.al-pied .al-sep { opacity: 0.5; margin: 0 0.15rem; }
</style>
"""


# ---------------------------------------------------------------------------
# 2. Données : chargement mis en cache et référentiels des filtres
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Chargement des données…")
def charger() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Événements et sessions nettoyés (lus une seule fois par processus)."""
    return charger_donnees()


@st.cache_data(show_spinner=False)
def referentiel() -> dict:
    """Bornes de dates et listes d'options des filtres, calculées une fois."""
    events, sessions = charger()
    jours = sessions["date"].dt.date
    pays = (
        sessions.groupby("country")
        .agg(n=("session_key", "size"), nom=("country_name", "first"))
        .sort_values(["n"], ascending=False)
    )
    noms = {code: (nom if isinstance(nom, str) and nom else code) for code, nom in pays["nom"].items()}
    return {
        "debut": jours.min(),
        "fin": jours.max(),
        "appareils": [a for a in g.APPAREILS if a in set(sessions["device"])],
        "pays": list(pays.index),
        "noms_pays": noms,
        "categories": sorted(events["item_category"].dropna().unique()),
        "n_sessions": len(sessions),
        "n_utilisateurs": int(sessions["user_id"].nunique()),
        "n_evenements": len(events),
        "n_pays": compter_pays(sessions["country"]),
        "n_pays_non_identifies": int((sessions["country"] == PAYS_NON_IDENTIFIE).sum()),
    }


@st.cache_data(show_spinner=False, max_entries=64)
def positions_filtrees(f: Filtres) -> tuple[np.ndarray, np.ndarray]:
    """Résultat de `filtrer` pour f, en cache sous forme de positions de lignes.

    Garder les positions (quelques Mo) plutôt que les tables (jusqu'à 170 Mo par filtre
    une fois sérialisées) : la reconstruction par `take` coûte environ 2 ms, alors que
    relire une table complète depuis le cache en coûte plus de 100.
    """
    ev, se = filtrer(EVENTS, SESSIONS, f)
    return (
        EVENTS.index.get_indexer(ev.index).astype(np.int32),
        SESSIONS.index.get_indexer(se.index).astype(np.int32),
    )


def tables(f: Filtres) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Événements et sessions retenus par f (filtrage mis en cache)."""
    pos_ev, pos_se = positions_filtrees(f)
    return EVENTS.take(pos_ev), SESSIONS.take(pos_se)


@st.cache_data(show_spinner=False, max_entries=256)
def kpis_caches(f: Filtres) -> dict:
    """Indicateurs clés de f (période affichée, période ou moitiés de référence)."""
    return calculer_kpis(tables(f)[1])


# Figures : (événements, sessions, thème, paramètres) -> figure Plotly.
CONSTRUCTEURS = {
    "evolution": lambda ev, se, t, **p: g.fig_evolution(se, p["granularite"], p["par_appareil"], theme=t),
    "heatmap": lambda ev, se, t: g.fig_heatmap_heure_jour(se, theme=t),
    "appareils": lambda ev, se, t: g.fig_parts_appareils(se, theme=t),
    "categories": lambda ev, se, t, **p: g.fig_categories(ev, p["metrique"], theme=t),
    "carte": lambda ev, se, t: g.fig_carte_pays(se, theme=t),
    "top_pays": lambda ev, se, t: g.fig_top_pays(se, theme=t),
    "boite": lambda ev, se, t, **p: g.fig_engagement_boite(se, p["metrique"], False, theme=t),
    "densite": lambda ev, se, t, **p: g.fig_engagement_densite(se, p["metrique"], p["log"], theme=t),
    "entonnoir": lambda ev, se, t: g.fig_entonnoir(se, ev, theme=t),
}


@st.cache_data(show_spinner=False, max_entries=128)
def figure_cachee(nom: str, f: Filtres, theme_nom: str, **params):
    """Figure Plotly mise en cache par (figure, filtres, thème, réglages) : un retour
    sur un onglet déjà vu ne recalcule rien."""
    ev, se = tables(f)
    return CONSTRUCTEURS[nom](ev, se, obtenir_theme(theme_nom), **params)


def figure(nom: str, **params):
    return figure_cachee(nom, FILTRES, THEME.nom, **params)


@st.cache_data(show_spinner=False, max_entries=64)
def constats_caches(f: Filtres) -> list[Constat]:
    """Constats de l'onglet Synthèse (calcul le plus coûteux : mis en cache par filtre)."""
    return generer_constats(*tables(f))


# ---------------------------------------------------------------------------
# Outils de mise en forme
# ---------------------------------------------------------------------------

def html_fr(contenu: str) -> None:
    """Affiche un bloc HTML rédigé, avec espaces insécables à la française."""
    st.html(typo(contenu))


def esc(texte) -> str:
    """Échappe un texte destiné à du HTML."""
    return html.escape(str(texte), quote=True)


def icone(nom: str) -> str:
    """Icône Material Symbols ; accepte « trending_up » ou « :material/trending_up: »."""
    nom = nom.strip(":").removeprefix("material/")
    return f'<span class="material-symbols-rounded" aria-hidden="true">{esc(nom)}</span>'


def date_courte(jour: date) -> str:
    return f"{jour.day:02d}/{jour.month:02d}/{jour.year}"


def date_longue(jour) -> str:
    jour = pd.Timestamp(jour)
    premier = "1er" if jour.day == 1 else str(jour.day)
    return f"{premier} {MOIS_FR[jour.month - 1]} {jour.year}"


def usd(x: float | None, decimales: int = 0) -> str:
    """Montant « 65,09 USD » : espace insécable pleine (la fine colle trop au sigle en gras)."""
    texte = formater_nombre(x, decimales)
    return texte if x is None else texte + NBSP + "USD"


def pct(x: float | None, decimales: int = 1) -> str:
    return formater_nombre(None if x is None else x * 100, decimales, " %")


def valeur_metrique(metrique: str, x: float) -> str:
    """Valeur lisible d'une métrique d'engagement."""
    if metrique == "duration_s":
        return formater_duree(x)
    if metrique == "n_events":
        return formater_nombre(x, 0, " actions")
    return usd(x, 0)


def libelle_pays(code: str) -> str:
    """« US · United States » (code seul s'il n'a pas de nom distinct)."""
    nom = referentiel()["noms_pays"].get(code, code)
    return code if nom == code else f"{code} · {nom}"


# ---------------------------------------------------------------------------
# 3. État de session et thème
# ---------------------------------------------------------------------------

ss = st.session_state
ss.setdefault("theme", "clair")  # thème clair par défaut
if ss["theme"] not in THEMES:
    ss["theme"] = "clair"
# La bascule suit toujours ss["theme"] (même si celui-ci est fixé ailleurs, par exemple
# par les tests) ; on la synchronise avant sa création.
ss["bascule_theme"] = ss["theme"] == "sombre"


def basculer_theme() -> None:
    """Rappel de la bascule « Mode sombre » : met à jour le thème actif."""
    ss["theme"] = "sombre" if ss["bascule_theme"] else "clair"


def reinitialiser_filtres() -> None:
    """Rappel du bouton « Réinitialiser » : les filtres reprennent leur valeur par défaut."""
    for cle in CLES_FILTRES:
        ss.pop(cle, None)


THEME: Theme = obtenir_theme(ss["theme"])
st.markdown(css(THEME), unsafe_allow_html=True)
st.markdown(CSS_APP, unsafe_allow_html=True)

EVENTS, SESSIONS = charger()
REF = referentiel()


# ---------------------------------------------------------------------------
# 4. Barre latérale : filtres, réinitialisation, export, source
# ---------------------------------------------------------------------------

with st.sidebar:
    st.html(
        '<div class="al-logo">Audience Lab</div>'
        '<div class="al-logo-sous">Google Merchandise Store · GA4</div>'
    )
    st.html('<div class="al-barre-titre">Filtres</div>')

    periode_brute = st.date_input(
        "Période",
        value=(REF["debut"], REF["fin"]),
        min_value=REF["debut"],
        max_value=REF["fin"],
        format="DD/MM/YYYY",
        key="f_periode",
        help="Données disponibles du 1er novembre 2020 au 31 janvier 2021.",
    )
    appareils = st.multiselect(
        "Appareils", REF["appareils"], key="f_appareils",
        placeholder="Tous les appareils", select_all=False,
    )
    pays = st.multiselect(
        "Pays", REF["pays"], key="f_pays", format_func=libelle_pays,
        placeholder="Tous les pays", select_all=False,
        help="Pays classés du plus au moins représenté ; tapez un code ou un nom pour chercher.",
    )
    categories = st.multiselect(
        "Catégories de produits", REF["categories"], key="f_categories",
        placeholder="Toutes les catégories", select_all=False,
        help="Ne garde que les sessions ayant au moins un événement sur ces catégories.",
    )
    st.button(
        "Réinitialiser les filtres", key="reinitialiser", on_click=reinitialiser_filtres,
        icon=":material/restart_alt:", type="secondary", width="stretch",
    )

# Filtres effectifs (une liste vide signifie « pas de filtre »).
DEBUT, FIN = normaliser_periode(periode_brute, (REF["debut"], REF["fin"]))
FILTRES = Filtres(DEBUT, FIN, tuple(appareils), tuple(pays), tuple(categories))
EV, SE = tables(FILTRES)
VIDE = len(SE) == 0
# Base des variations : période précédente si couverte, sinon moitiés de la période.
COMPAREE, REFERENCE, MODE_COMPARAISON = periode_de_reference(FILTRES, REF["debut"])


def csv_sessions() -> bytes:
    """CSV des sessions filtrées (valeurs inchangées), lisible par Excel (BOM UTF-8)."""
    return SE.to_csv(index=False).encode("utf-8-sig")


def bouton_export(cle: str) -> None:
    st.download_button(
        "Exporter en CSV",
        data=csv_sessions,
        file_name=NOM_EXPORT,
        mime="text/csv",
        key=cle,
        on_click="ignore",
        icon=":material/download:",
        type="primary",
        width="stretch",
        disabled=VIDE,
        help="Fichier CSV encodé en UTF-8 (compatible Excel), une ligne par session.",
    )


with st.sidebar:
    st.html('<div class="al-barre-titre">Export</div>')
    bouton_export("export_csv")
    html_fr(
        f'<div class="al-barre-note">{formater_nombre(len(SE))} sessions dans la sélection.</div>'
    )
    html_fr(
        '<div class="al-barre-titre">Source</div>'
        '<div class="al-barre-note">Google Merchandise Store, échantillon GA4 obfusqué '
        "publié par Google (BigQuery <i>ga4_obfuscated_sample_ecommerce</i>), "
        "diffusé sur Kaggle et Observable. Événements add_to_cart, begin_checkout "
        "et purchase du <b>1er novembre 2020</b> au <b>31 janvier 2021</b>.</div>"
    )


# ---------------------------------------------------------------------------
# 5. En-tête et bandeau d'indicateurs clés
# ---------------------------------------------------------------------------

def nombre_filtres_actifs() -> int:
    n = sum(bool(x) for x in (appareils, pays, categories))
    return n + int((DEBUT, FIN) != (REF["debut"], REF["fin"]))


def entete() -> None:
    actifs = nombre_filtres_actifs()
    texte_filtres = (
        "Aucun filtre actif" if actifs == 0
        else f"<b>{actifs}</b> filtre{'s' if actifs > 1 else ''} actif{'s' if actifs > 1 else ''}"
    )
    puces = (
        f'<span class="al-puce">{icone("bar_chart")}<span><b>{formater_nombre(len(SE))}</b>'
        f" sessions filtrées sur {formater_nombre(REF['n_sessions'])}</span></span>"
        f'<span class="al-puce">{icone("calendar_month")}<span>Du <b>{date_courte(DEBUT)}</b>'
        f" au <b>{date_courte(FIN)}</b></span></span>"
        f'<span class="al-puce">{icone("filter_alt")}<span>{texte_filtres}</span></span>'
    )
    with st.container(key="al_entete"):
        gauche, droite = st.columns([5, 1], vertical_alignment="top")
        with gauche:
            html_fr(
                '<div class="al-surtitre">Tableau de bord d\'audience</div>'
                '<div class="al-titre">Audience Lab</div>'
                f'<p class="al-sous-titre">{esc(SOUS_TITRE)}</p>'
                f'<div class="al-puces">{puces}</div>'
            )
        with droite:
            st.toggle(
                "Mode sombre", key="bascule_theme", on_change=basculer_theme,
                help="Passe du thème clair (par défaut) au thème sombre (Nuit analytique), adapté à la projection.",
            )


def series_quotidiennes(se: pd.DataFrame) -> dict[str, list[float] | None]:
    """Petites courbes des cartes KPI : valeur par jour (moyenne glissante 7 jours pour les ratios)."""
    if se.empty:
        return {}
    jour = se["date"].dt.normalize()
    calendrier = pd.date_range(jour.min(), jour.max(), freq="D")
    if len(calendrier) < 3:
        return {}

    def par_jour(serie: pd.Series) -> pd.Series:
        return serie.groupby(jour).sum().reindex(calendrier, fill_value=0)

    def glissant(num: pd.Series, den: pd.Series) -> pd.Series:
        return num.rolling(7, min_periods=1).sum() / den.rolling(7, min_periods=1).sum()

    n = par_jour(pd.Series(1, index=se.index))
    achats = par_jour(se["purchased"].astype(int))
    series = {
        "sessions": n,
        "utilisateurs": se.groupby(jour)["user_id"].nunique().reindex(calendrier, fill_value=0),
        "duree_moyenne_s": glissant(par_jour(se["duration_s"]), n),
        "panier_moyen_usd": glissant(par_jour(se["revenue_usd"].where(se["purchased"], 0)), achats),
        "taux_conversion": glissant(achats, n),
        "part_mobile": glissant(par_jour((se["device"] == "mobile").astype(int)), n),
    }
    resultat = {}
    for cle, serie in series.items():
        valeurs = serie.replace([float("inf"), float("-inf")], pd.NA).dropna().astype(float)
        resultat[cle] = valeurs.round(4).tolist() if len(valeurs) >= 3 else None
    return resultat


@st.cache_data(show_spinner=False, max_entries=64)
def series_cachees(f: Filtres) -> dict[str, list[float] | None]:
    return series_quotidiennes(tables(f)[1])


def valeur_kpi(cle: str, v) -> str:
    if cle in ("sessions", "utilisateurs"):
        return formater_nombre(v or 0)
    if cle == "duree_moyenne_s":
        return formater_duree(v)
    if cle == "panier_moyen_usd":
        return usd(v, 2)
    return pct(v)


def delta_kpi(cle: str, d: float | None) -> tuple[str | None, str, str]:
    """(texte du delta, couleur, flèche) ; % pour les volumes, pts pour les taux."""
    if d is None:
        # Sans comparaison possible, la petite courbe prend la couleur d'accent.
        return None, "violet", "off"
    unite = " pts" if cle in CLES_POINTS else " %"  # espace rendue insécable par formater_nombre
    if round(d, 1) == 0:
        return formater_nombre(0, 1, unite), "off", "off"
    signe = "+" if d > 0 else "-"
    return f"{signe}{formater_nombre(abs(d), 1, unite)}", "normal", "auto"


def bandeau_kpis() -> None:
    actuel = kpis_caches(FILTRES)
    if MODE_COMPARAISON == "aucune":
        deltas: dict = {}
    else:
        deltas = variations(kpis_caches(COMPAREE), kpis_caches(REFERENCE))
    series = series_cachees(FILTRES)

    colonnes = st.columns(len(INDICATEURS), gap="small")
    for colonne, (cle, libelle, icone_kpi, aide) in zip(colonnes, INDICATEURS):
        texte, couleur, fleche = delta_kpi(cle, deltas.get(cle))
        with colonne:
            st.metric(
                libelle, typo(valeur_kpi(cle, actuel[cle])),
                delta=texte, delta_color=couleur, delta_arrow=fleche,
                help=typo(aide), icon=icone_kpi,
                chart_data=series.get(cle), chart_type="area",
                height="stretch",
            )
    html_fr(f'<div class="al-note-kpi">{icone("compare_arrows")}<span>{note_variations(deltas)}</span></div>')


def note_variations(deltas: dict) -> str:
    """Phrase sous le bandeau : base de comparaison des variations."""
    def du_au(f: Filtres) -> str:
        return f"du {date_courte(f.debut)} au {date_courte(f.fin)}"

    courbes = " Courbes : évolution jour par jour (moyenne glissante sur 7 jours pour les taux)."
    if MODE_COMPARAISON == "aucune":
        return "Variations non calculées pour une période d'un seul jour." + courbes
    if MODE_COMPARAISON == "precedente":
        base = f"la <b>période précédente de même durée</b> ({du_au(REFERENCE)}), mêmes filtres"
        if all(v is None for v in deltas.values()):
            return f"Variations par rapport à {base} : indisponibles, aucune session comparable."
        return f"Variations : comparaison avec {base}." + courbes
    base = (
        f"<b>seconde moitié</b> de la période ({du_au(COMPAREE)}) comparée à la "
        f"<b>première moitié</b> ({du_au(REFERENCE)}), la période précédente n'étant pas "
        "couverte par les données"
    )
    if all(v is None for v in deltas.values()):
        return f"Variations ({base}) : indisponibles, une des moitiés est sans session."
    return f"Variations : {base}." + courbes


# ---------------------------------------------------------------------------
# Éléments communs des onglets
# ---------------------------------------------------------------------------

CONFIG_PLOTLY_BASE = {
    "displaylogo": False,
    "scrollZoom": False,
    "modeBarButtonsToRemove": [
        "lasso2d", "select2d", "autoScale2d", "toggleSpikelines",
        "hoverClosestCartesian", "hoverCompareCartesian",
    ],
}


def graphique(
    fig, nom: str, legende: str, etiquette: str | None = None, etroit: bool = False
) -> None:
    """Affiche une figure thémée (theme=None : on garde notre habillage) et sa légende.

    `etroit` : figure en demi-largeur ; un long sous-titre passe alors sur deux lignes.
    """
    sous_titre = fig.layout.title.subtitle.text
    if etroit and sous_titre and len(sous_titre) > 70 and " ; " in sous_titre:
        fig.update_layout(
            title_subtitle_text=sous_titre.replace(" ; ", "<br>", 1),
            margin_t=(fig.layout.margin.t or 64) + 18,
        )
    if etiquette:
        st.html(f'<div class="al-etiquette">{esc(etiquette)}</div>')
    config = dict(CONFIG_PLOTLY_BASE)
    config["toImageButtonOptions"] = {
        "format": "png", "filename": f"audience_lab_{nom}", "scale": 2,
    }
    titre = fig.layout.title.text or nom
    st.plotly_chart(
        fig, theme=None, width="stretch", config=config, key=f"graphique_{nom}",
        alt=titre,
    )
    html_fr(f'<div class="al-legende">{legende}</div>')


def section(titre: str, texte: str = "") -> None:
    sous = f'<div class="al-section-texte">{texte}</div>' if texte else ""
    html_fr(f'<div class="al-section"><div class="al-section-titre">{esc(titre)}</div>{sous}</div>')


def etat_vide() -> None:
    """Message affiché à la place des graphiques quand les filtres ne laissent rien."""
    html_fr(
        '<div class="al-vide">'
        f'{icone("filter_alt_off")}'
        '<div class="al-vide-titre">Aucune donnée pour ces filtres</div>'
        '<div class="al-vide-texte">Aucune session ne correspond à la combinaison choisie. '
        "Élargissez la période ou retirez un pays, un appareil ou une catégorie, "
        f"ou cliquez sur «{NBSP}Réinitialiser les filtres{NBSP}».</div>"
        "</div>"
    )


def periode_pic(se: pd.DataFrame, hebdo: bool) -> tuple[pd.Timestamp, int]:
    jours = se["date"].dt.normalize()
    if hebdo:
        jours = jours - pd.to_timedelta(jours.dt.weekday, unit="D")
    comptes = jours.value_counts()
    return comptes.idxmax(), int(comptes.max())


def mediane_par_appareil(se: pd.DataFrame, metrique: str) -> str:
    medianes = se.groupby("device")[metrique].median()
    morceaux = [
        f"{a} <b>{valeur_metrique(metrique, medianes[a])}</b>"
        for a in g.APPAREILS if a in medianes.index
    ]
    return ", ".join(morceaux)


# ---------------------------------------------------------------------------
# 6. Onglets
# ---------------------------------------------------------------------------

def onglet_synthese() -> None:
    gauche, droite = st.columns([1.85, 1], gap="large")
    with gauche:
        section("Constats clés", "Rédigés automatiquement à partir des données filtrées : "
                "ils changent avec la période, l'appareil, le pays et la catégorie.")
        if VIDE:
            etat_vide()
        else:
            cartes = "".join(
                '<div class="al-constat">'
                f'<div class="al-constat-icone">{icone(c.icone)}</div>'
                f'<div><div class="al-constat-titre">{esc(c.titre)}</div><p>{esc(c.texte)}</p></div>'
                "</div>"
                for c in constats_caches(FILTRES)
            )
            html_fr(f'<div class="al-grille-constats">{cartes}</div>')
    with droite:
        kpis = calculer_kpis(SE)
        n_achats = int(SE["purchased"].sum()) if not VIDE else 0
        reperes = [
            (usd(kpis["chiffre_affaires_usd"] or 0, 0), "Chiffre d'affaires", ""),
            (formater_nombre(n_achats), "Sessions avec achat", ""),
            (formater_nombre(len(EV)), "Événements", ""),
            (formater_nombre(compter_pays(SE["country"])), "Pays représentés",
             f"hors « {PAYS_NON_IDENTIFIE} »"),
        ]
        html_fr(
            '<div class="al-reperes">'
            + "".join(
                f'<div class="al-repere"><div class="al-repere-valeur">{v}</div>'
                f'<div class="al-repere-libelle">{esc(l)}</div>'
                + (f'<div class="al-repere-note">{esc(n)}</div>' if n else "")
                + "</div>"
                for v, l, n in reperes
            )
            + "</div>"
        )
        html_fr(
            '<div class="al-carte al-apropos">'
            f'<h4>{icone("info")} À propos des données</h4>'
            "<dl>"
            "<dt>Source</dt><dd>Google Merchandise Store, boutique en ligne de produits "
            "dérivés Google : échantillon Google Analytics 4 publié par Google "
            "(BigQuery <i>ga4_obfuscated_sample_ecommerce</i>), via Kaggle et Observable.</dd>"
            "<dt>Période</dt><dd>Du 1er novembre 2020 au 31 janvier 2021 (92 jours) : "
            "Black Friday, Cyber Monday, Noël et le creux de janvier.</dd>"
            f"<dt>Volume</dt><dd>{formater_nombre(REF['n_sessions'])} sessions, "
            f"{formater_nombre(REF['n_utilisateurs'])} utilisateurs, "
            f"{formater_nombre(REF['n_evenements'])} événements (add_to_cart, "
            f"begin_checkout, purchase), {formater_nombre(REF['n_pays'])} pays "
            f"(hors « {PAYS_NON_IDENTIFIE} », pays non identifié de "
            f"{formater_nombre(REF['n_pays_non_identifies'])} sessions).</dd>"
            "<dt>Limites</dt><dd><ul>"
            "<li>Fuseau horaire non documenté par la source (heures probablement "
            "celles de la propriété GA, aux États-Unis).</li>"
            "<li>Échantillon obfusqué par Google : volumes et montants indicatifs, "
            "pas l'activité réelle de la boutique.</li>"
            "<li>Seuls trois types d'événements : pas de pages vues ni de source de trafic.</li>"
            "</ul></dd>"
            "</dl></div>"
        )


def onglet_temporalite() -> None:
    section("Quand les visiteurs viennent-ils ?",
            "Saisonnalité de fin d'année et rythme de la semaine.")
    if VIDE:
        etat_vide()
        return
    with st.container(horizontal=True, vertical_alignment="bottom", key="controles_temporalite"):
        choix = st.segmented_control(
            "Granularité", list(GRANULARITES), default="Jour", required=True,
            key="granularite", persist_state="page",
        )
        par_appareil = st.toggle(
            "Détail par appareil", key="evo_appareil", persist_state="page",
            help="Une courbe par appareil (desktop, mobile, tablet).",
        )
    hebdo = GRANULARITES.get(choix or "Jour", "D") == "W"
    fig = figure("evolution", granularite="W" if hebdo else "D", par_appareil=par_appareil)
    pic, n_pic = periode_pic(SE, hebdo)
    quand = f"la semaine du {date_longue(pic)}" if hebdo else f"le {date_longue(pic)}"
    reperes = [lib for jour, lib, _ in g.EVENEMENTS if pd.Timestamp(DEBUT) <= jour <= pd.Timestamp(FIN)]
    phrase_reperes = (
        f" Les lignes verticales repèrent {', '.join(reperes[:-1]) + ' et ' + reperes[-1] if len(reperes) > 1 else reperes[0]}."
        if reperes else ""
    )
    graphique(
        fig, "evolution",
        f"Pic {'hebdomadaire' if hebdo else 'journalier'} : <b>{quand}</b>, avec "
        f"<b>{formater_nombre(n_pic)}</b> sessions.{phrase_reperes} "
        "Survolez la courbe pour lire chaque valeur ; la granularité semaine lisse les variations quotidiennes.",
        etiquette="Évolution temporelle",
    )

    creneaux = SE.groupby(["weekday", "hour"]).size()
    (jour, heure), n_creneau = creneaux.idxmax(), int(creneaux.max())
    ouvre = SE[(SE["weekday"] < 5) & SE["hour"].between(8, 17)]
    graphique(
        figure("heatmap"), "heatmap_heure_jour",
        f"Créneau le plus actif : <b>{JOURS_FR[int(jour)].lower()} à {int(heure)} h</b> "
        f"({formater_nombre(n_creneau)} sessions démarrées). Les jours ouvrés de 8 h à 18 h "
        f"concentrent {pct(len(ouvre) / len(SE))} des sessions. Plus la teinte est intense, "
        "plus le trafic est fort ; heures selon un fuseau non documenté par la source.",
        etiquette="Heatmap heure x jour",
    )


def onglet_audience() -> None:
    section("D'où viennent-ils, et sur quel appareil ?",
            "Répartition des sessions par appareil, par catégorie de produit et par pays.")
    if VIDE:
        etat_vide()
        return
    # Le choix de mesure des catégories est placé au-dessus des deux graphiques, pour
    # que l'anneau et les barres démarrent à la même hauteur.
    with st.container(horizontal=True, horizontal_alignment="right"):
        metrique = st.segmented_control(
            "Mesure des catégories", list(METRIQUES_CATEGORIES), default="add_to_cart",
            required=True, format_func=METRIQUES_CATEGORIES.get, key="aud_metrique",
            persist_state="page",
        ) or "add_to_cart"
    fig_categories = figure("categories", metrique=metrique)
    fig_appareils = figure("appareils")
    fig_appareils.update_layout(height=max(fig_appareils.layout.height, fig_categories.layout.height or 0))
    gauche, droite = st.columns([1, 1.35], gap="medium")
    with gauche:
        parts = SE["device"].value_counts(normalize=True)
        detail = ", ".join(f"{a} <b>{pct(parts[a])}</b>" for a in g.APPAREILS if a in parts.index)
        graphique(
            fig_appareils, "parts_appareils",
            f"Parts des sessions : {detail}. Le total des sessions filtrées figure au centre de l'anneau.",
            etiquette="Comparaison catégorielle",
        )
    with droite:
        if metrique == "revenue":
            valeurs = EV[EV["type"] == "purchase"].groupby("item_category")["price_in_usd"].sum()
            objet = "du chiffre d'affaires"
        else:
            valeurs = EV.loc[EV["type"] == "add_to_cart", "item_category"].value_counts()
            objet = "des ajouts au panier"
        valeurs = valeurs[valeurs > 0].sort_values(ascending=False)
        if valeurs.empty:
            legende = f"Aucune valeur {objet} sur cette sélection."
        else:
            part1 = valeurs.iloc[0] / valeurs.sum()
            part3 = valeurs.head(3).sum() / valeurs.sum()
            legende = (
                f"<b>{esc(valeurs.index[0])}</b> arrive en tête avec {pct(part1)} {objet} ; "
                f"les trois premières catégories en réunissent {pct(part3)}. "
                "Changez de mesure pour comparer volume d'intérêt et chiffre d'affaires."
            )
        graphique(fig_categories, f"categories_{metrique}", legende,
                  etiquette="Comparaison catégorielle")

    gauche, droite = st.columns([1.6, 1], gap="medium")
    par_pays = SE["country"].value_counts()
    premier = par_pays.index[0]
    with gauche:
        graphique(
            figure("carte"), "carte_pays",
            f"<b>{esc(REF['noms_pays'].get(premier, premier))}</b> concentre "
            f"{pct(par_pays.iloc[0] / len(SE))} des sessions, sur "
            f"{formater_nombre(compter_pays(SE['country']))} pays représentés "
            f"(hors « {PAYS_NON_IDENTIFIE} »). L'échelle de couleur "
            "logarithmique laisse voir les petits marchés ; survolez un pays pour le détail.",
        )
    with droite:
        graphique(
            figure("top_pays"), "top_pays",
            f"Les dix premiers pays totalisent {pct(par_pays.head(10).sum() / len(SE))} "
            "du trafic : l'audience reste très concentrée.",
        )


def onglet_engagement() -> None:
    section("À quel point s'engagent-ils ?",
            "Distribution de l'engagement par session selon l'appareil.")
    if VIDE:
        etat_vide()
        return
    with st.container(horizontal=True, vertical_alignment="bottom", key="controles_engagement"):
        metrique = st.segmented_control(
            "Métrique", list(METRIQUES_ENGAGEMENT), default="duration_s", required=True,
            format_func=METRIQUES_ENGAGEMENT.get, key="eng_metrique", persist_state="page",
        ) or "duration_s"
        # Une bascule par métrique : activée par défaut pour les longues traînes
        # (durée, valeur du panier), et le choix de l'utilisateur est conservé.
        log = st.toggle(
            "Distribution en échelle logarithmique", key=f"eng_log_{metrique}",
            value=metrique in METRIQUES_LOG_PAR_DEFAUT, persist_state="page",
            help="Déplie la longue traîne de la distribution (graphique de droite). "
                 "Les boîtes restent en échelle linéaire, resserrée sur les moustaches.",
        )
    serie = SE[metrique].dropna()
    moyenne, mediane = float(serie.mean()), float(serie.median())
    asymetrie = (
        f" La moyenne ({valeur_metrique(metrique, moyenne)}) dépasse nettement la médiane "
        f"({valeur_metrique(metrique, mediane)}) : quelques sessions extrêmes tirent la moyenne vers le haut."
        if mediane > 0 and moyenne > 1.5 * mediane else ""
    )
    gauche, droite = st.columns(2, gap="medium")
    with gauche:
        graphique(
            figure("boite", metrique=metrique), f"boite_{metrique}",
            f"Médianes : {mediane_par_appareil(SE, metrique)}. La boîte couvre la moitié "
            f"centrale des sessions.{asymetrie}",
            etiquette="Distribution par appareil", etroit=True,
        )
    with droite:
        nuls = int((SE[metrique] <= 0).sum())
        conseil = (
            " En échelle logarithmique, chaque graduation multiplie la valeur par 10"
            + (f" ; les {formater_nombre(nuls)} sessions à valeur nulle sont exclues." if nuls else ".")
            if log else " Activez l'échelle logarithmique pour déplier la longue traîne."
        )
        graphique(
            figure("densite", metrique=metrique, log=log), f"densite_{metrique}_{int(log)}",
            "Chaque appareil a une aire normalisée à 1 : on compare la forme des distributions, "
            f"pas les volumes.{conseil}",
            etiquette="Distribution par appareil", etroit=True,
        )


def onglet_conversion() -> None:
    section("Où les perd-on ?",
            "Entonnoir add_to_cart, begin_checkout, purchase et conversion par appareil.")
    if VIDE:
        etat_vide()
        return
    gauche, droite = st.columns([1.75, 1], gap="medium")
    paires = EV.loc[EV["type"].isin(g.ETAPES), ["session_key", "type"]].drop_duplicates()
    etapes = {t: set(paires.loc[paires["type"] == t, "session_key"]) for t in g.ETAPES}
    panier, paiement, achat = (etapes[t] for t in g.ETAPES)
    if panier:
        taux_paiement = len(panier & paiement) / len(panier)
        texte = f"<b>{pct(taux_paiement)}</b> des sessions add_to_cart atteignent begin_checkout"
        pertes = {"au passage au paiement (add_to_cart vers begin_checkout)": 1 - taux_paiement}
        if paiement:
            taux_achat = len(paiement & achat) / len(paiement)
            texte += (f", puis <b>{pct(taux_achat)}</b> des sessions "
                      "begin_checkout vont jusqu'à purchase")
            pertes["au dernier pas (begin_checkout vers purchase)"] = 1 - taux_achat
        etape, perte = max(pertes.items(), key=lambda kv: kv[1])
        texte += f". La plus forte déperdition se situe {etape} : {pct(perte)} des sessions s'y arrêtent."
    else:
        texte = "Aucune session add_to_cart dans la sélection."
    with gauche:
        graphique(
            figure("entonnoir"), "entonnoir",
            texte + " Barres empilées par appareil ; survolez un segment pour sa part.",
        )
    with droite:
        section("Taux de conversion par appareil", "Part des sessions avec au moins un achat.")
        stats = SE.groupby("device").agg(sessions=("purchased", "size"), achats=("purchased", "sum"))
        maxi = max(float((stats["achats"] / stats["sessions"]).max()), 1e-9)
        cartes = []
        for appareil in [a for a in g.APPAREILS if a in stats.index]:
            n, a = int(stats.loc[appareil, "sessions"]), int(stats.loc[appareil, "achats"])
            taux = a / n if n else 0.0
            couleur = THEME.couleurs_appareils.get(appareil, THEME.accent)
            cartes.append(
                '<div class="al-conv-carte"><div class="al-conv-haut">'
                f'<span class="al-conv-appareil"><span class="al-point" style="background:{couleur}"></span>'
                f"{esc(appareil)}</span>"
                f'<span class="al-conv-taux">{pct(taux)}</span></div>'
                f'<div class="al-conv-barre"><div style="width:{taux / maxi * 100:.1f}%;background:{couleur}"></div></div>'
                f'<div class="al-conv-detail">{formater_nombre(a)} sessions avec achat sur {formater_nombre(n)}</div>'
                "</div>"
            )
        html_fr(f'<div class="al-conv">{"".join(cartes)}</div>')
        taux = stats["achats"] / stats["sessions"]
        rappel = f"Le taux global figure dans le bandeau «{NBSP}Taux de conversion{NBSP}»."
        if taux.max() > 0:
            phrase = f"Barres proportionnelles au meilleur taux (<b>{esc(taux.idxmax())}</b>). {rappel}"
        else:
            phrase = f"Aucun achat dans la sélection : le taux est nul pour chaque appareil. {rappel}"
        html_fr(f'<div class="al-legende">{phrase}</div>')


def cellule(colonne: str, valeur) -> str:
    """Cellule HTML de l'aperçu : présentation française, valeur d'origine conservée."""
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return '<td class="centre al-non">n.d.</td>'
    if colonne in COLONNES_BOOLEENNES:
        return ('<td class="centre"><span class="al-oui" title="True">✓</span></td>' if valeur
                else '<td class="centre"><span class="al-non" title="False">✗</span></td>')
    if colonne in COLONNES_MONTANTS:
        return f'<td class="num">{formater_nombre(float(valeur), 2)}</td>'
    if colonne in COLONNES_NUMERIQUES:
        x = float(valeur)
        return f'<td class="num">{formater_nombre(x, 0 if x.is_integer() else 2)}</td>'
    if colonne == "start":
        return f"<td>{pd.Timestamp(valeur):%d/%m/%Y %H:%M:%S}</td>"
    if colonne == "device":
        couleur = THEME.couleurs_appareils.get(valeur, THEME.accent)
        return (f'<td><span class="al-appareil"><span class="al-point" style="background:{couleur}">'
                f"</span>{esc(valeur)}</span></td>")
    if colonne == "session_key":
        return f'<td class="code">{esc(valeur)}</td>'
    return f"<td>{esc(valeur)}</td>"


def tableau_html(se: pd.DataFrame) -> str:
    colonnes = list(COLONNES_APERCU)
    entetes = "".join(
        f'<th class="{"num" if c in COLONNES_NUMERIQUES else "centre" if c in COLONNES_BOOLEENNES else ""}">'
        f"{esc(COLONNES_APERCU[c])}</th>"
        for c in colonnes
    )
    lignes = "".join(
        "<tr>" + "".join(cellule(c, v) for c, v in zip(colonnes, ligne)) + "</tr>"
        for ligne in se[colonnes].head(LIGNES_APERCU).itertuples(index=False, name=None)
    )
    return (f'<div class="al-table-conteneur"><table class="al-table"><thead><tr>{entetes}</tr></thead>'
            f"<tbody>{lignes}</tbody></table></div>")


def onglet_donnees() -> None:
    gauche, droite = st.columns([3, 1.1], vertical_alignment="bottom")
    with gauche:
        section(
            "Sessions filtrées",
            f"Aperçu des {formater_nombre(min(LIGNES_APERCU, len(SE)))} premières sessions "
            f"sur {formater_nombre(len(SE))}, dans l'ordre chronologique. "
            "L'export CSV contient toutes les sessions filtrées et toutes les colonnes, valeurs inchangées.",
        )
    with droite:
        bouton_export("export_csv_donnees")
    if VIDE:
        etat_vide()
        return
    st.html(tableau_html(SE))
    html_fr(
        '<div class="al-legende">Une ligne par session. Durée : temps entre le premier et le dernier '
        "événement ; valeur panier : somme des prix ajoutés au panier ; chiffre d'affaires : "
        "somme des prix achetés. ✓ : oui, ✗ : non. Aussi disponible depuis la barre latérale.</div>"
    )


RENDUS = {
    "Synthèse": onglet_synthese,
    "Temporalité": onglet_temporalite,
    "Audience": onglet_audience,
    "Engagement": onglet_engagement,
    "Conversion": onglet_conversion,
    "Données": onglet_donnees,
}


# ---------------------------------------------------------------------------
# Assemblage de la page
# ---------------------------------------------------------------------------

entete()
bandeau_kpis()

# Onglets « paresseux » : seul l'onglet ouvert est calculé (on_change="rerun").
for onglet, nom in zip(st.tabs(ONGLETS, key="onglet", on_change="rerun"), ONGLETS):
    if onglet.open is False:
        continue
    with onglet:
        RENDUS[nom]()


# ---------------------------------------------------------------------------
# 7. Pied de page
# ---------------------------------------------------------------------------

html_fr(
    '<div class="al-pied">'
    + '<span class="al-sep"> · </span>'.join(f"<span>{esc(p.strip())}</span>" for p in PIED.split("·"))
    + "</div>"
)
