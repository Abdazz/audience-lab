"""Thèmes visuels d'Audience Lab : palettes, feuille de style Streamlit, habillage Plotly.

Deux thèmes : « sombre » (Nuit analytique, thème par défaut) et « clair »
(professionnel). Chaque thème fournit :

- une palette (`Theme`) partagée par le CSS et les graphiques ;
- `css(theme)` : une balise <style> à injecter avec
  `st.markdown(css(theme), unsafe_allow_html=True)` ;
- `appliquer_theme(fig, theme)` : habillage d'une figure Plotly (fonds, police,
  grille, légende, info-bulles, séparateurs décimaux français).

Important : afficher les figures avec `st.plotly_chart(fig, theme=None)`, sinon
Streamlit remplace l'habillage par son propre thème.

Classes CSS mises à disposition de app.py (à utiliser dans st.markdown) :

- `.al-header` : bloc d'en-tête (titre + sous-titre), carte large en haut de page ;
- `.al-titre` : titre principal, texte en dégradé (violet #8B5CF6 vers cyan
  #22D3EE en sombre, indigo vers bleu ciel en clair) ;
- `.al-sous-titre` : phrase de contexte sous le titre (texte secondaire) ;
- `.al-carte` : carte générique (surface, bordure, rayon, ombre douce en clair) ;
- `.al-constat` : carte de constat ; structure attendue :
  `<div class="al-constat"><div class="al-constat-icone">...</div>`
  `<div><div class="al-constat-titre">...</div><p>...</p></div></div>` ;
- `.al-legende` : courte légende d'interprétation sous un graphique ;
- `.al-pied` : pied de page (auteur, module, source) ;
- `.al-logo` : nom de l'application en dégradé dans la barre latérale ;
- `.al-badge` : petite pastille (par exemple « Données GA4 »).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import plotly.graph_objects as go

POLICE = "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
URL_POLICE = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
)


@dataclass(frozen=True)
class Theme:
    """Palette d'un thème. Les couleurs sont des chaînes hexadécimales."""

    nom: str
    fond: str
    surface: str
    bordure: str
    texte: str
    texte_secondaire: str
    accent: str
    accent_2: str
    positif: str
    negatif: str
    couleurs_appareils: dict[str, str] = field(default_factory=dict)
    sequence: list[str] = field(default_factory=list)
    echelle_continue: list[str] = field(default_factory=list)


SOMBRE = Theme(
    nom="sombre",
    fond="#0B1020",
    surface="#141B35",
    bordure="#232D55",
    texte="#E6E9F5",
    texte_secondaire="#94A3B8",
    accent="#8B5CF6",
    accent_2="#22D3EE",
    positif="#34D399",
    negatif="#F87171",
    couleurs_appareils={"desktop": "#8B5CF6", "mobile": "#22D3EE", "tablet": "#F472B6"},
    sequence=["#8B5CF6", "#22D3EE", "#F472B6", "#FBBF24", "#60A5FA", "#FB923C"],
    # Une seule famille de teintes (indigo -> violet -> lavande), du plus sombre
    # (proche de la surface) au plus clair : lecture « plus clair = plus fort ».
    echelle_continue=["#252A63", "#3A2F86", "#5835B4", "#7C4FE0", "#A78BFA", "#DDD6FE"],
)

CLAIR = Theme(
    nom="clair",
    fond="#F5F7FB",
    surface="#FFFFFF",
    bordure="#E5E9F2",
    texte="#0F172A",
    texte_secondaire="#64748B",
    accent="#4F46E5",
    accent_2="#0EA5E9",
    positif="#059669",
    negatif="#DC2626",
    couleurs_appareils={"desktop": "#4F46E5", "mobile": "#0EA5E9", "tablet": "#F59E0B"},
    sequence=["#4F46E5", "#0EA5E9", "#F59E0B", "#DB2777", "#0D9488", "#7C3AED"],
    echelle_continue=["#EEF2FF", "#C7D2FE", "#A5B4FC", "#818CF8", "#6366F1", "#4F46E5", "#3730A3"],
)

THEMES: dict[str, Theme] = {"sombre": SOMBRE, "clair": CLAIR}


def obtenir_theme(nom: str) -> Theme:
    """Thème demandé ; le thème sombre pour un nom inconnu."""
    return THEMES.get(nom, SOMBRE)


def rgba(hexa: str, alpha: float) -> str:
    """'#8B5CF6', 0.1 -> 'rgba(139, 92, 246, 0.1)'."""
    h = hexa.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


# ---------------------------------------------------------------------------
# Feuille de style Streamlit
# ---------------------------------------------------------------------------

def _variables(t: Theme) -> str:
    """Variables CSS du thème (seule partie qui dépend des couleurs)."""
    sombre = t.nom == "sombre"
    if sombre:
        degrade = f"linear-gradient(135deg, {t.accent} 0%, {t.accent_2} 100%)"
        bouton = f"linear-gradient(135deg, {t.accent} 0%, #6D5BF0 55%, {t.accent_2} 140%)"
        ombre = "0 1px 0 rgba(255, 255, 255, 0.03) inset, 0 8px 24px rgba(0, 0, 0, 0.25)"
        ombre_survol = f"0 10px 30px {rgba(t.accent, 0.25)}"
        fond_app = (
            f"radial-gradient(1200px 600px at 85% -10%, {rgba(t.accent, 0.10)}, transparent 60%),"
            f" radial-gradient(900px 500px at -10% 110%, {rgba(t.accent_2, 0.06)}, transparent 60%),"
            f" {t.fond}"
        )
        survol = "#1C2547"
        champ = "#0F1530"
        barre_laterale = "#0E1430"
    else:
        degrade = f"linear-gradient(135deg, {t.accent} 0%, {t.accent_2} 100%)"
        bouton = t.accent
        ombre = "0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.06)"
        ombre_survol = "0 6px 24px rgba(15, 23, 42, 0.10)"
        fond_app = t.fond
        survol = "#EEF2FF"
        champ = t.surface
        barre_laterale = t.surface
    return f"""
:root {{
  --al-police: {POLICE};
  --al-fond: {t.fond};
  --al-fond-app: {fond_app};
  --al-surface: {t.surface};
  --al-bordure: {t.bordure};
  --al-texte: {t.texte};
  --al-texte-2: {t.texte_secondaire};
  --al-accent: {t.accent};
  --al-accent-2: {t.accent_2};
  --al-accent-doux: {rgba(t.accent, 0.14 if sombre else 0.08)};
  --al-positif: {t.positif};
  --al-negatif: {t.negatif};
  --al-degrade: {degrade};
  --al-bouton: {bouton};
  --al-ombre: {ombre};
  --al-ombre-survol: {ombre_survol};
  --al-survol: {survol};
  --al-champ: {champ};
  --al-barre-laterale: {barre_laterale};
  --al-rayon: 14px;
  color-scheme: {"dark" if sombre else "light"};
}}
"""


_CSS_COMMUN = """
/* ---- Base : fond, police, texte ---------------------------------------- */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--al-fond-app) !important;
  background-attachment: fixed !important;
  color: var(--al-texte);
}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] div,
[class^="al-"], [class*=" al-"], [data-trigger], [data-trigger] [role="option"],
[data-baseweb="popover"], [data-baseweb="popover"] li {
  font-family: var(--al-police) !important;
}
.stApp, .stApp p, .stApp li, .stApp span, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
  color: var(--al-texte);
}
.stApp h1, .stApp h2, .stApp h3 { letter-spacing: -0.02em; font-weight: 700; }
.stApp small, .stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p { color: var(--al-texte-2) !important; }
.stApp a { color: var(--al-accent-2); }
.stApp hr { border-color: var(--al-bordure); }
[data-testid="stMainBlockContainer"] { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }

/* ---- En-tête Streamlit (barre du haut) ---------------------------------- */
[data-testid="stHeader"] {
  background: transparent !important;
  backdrop-filter: blur(8px);
}
[data-testid="stHeader"] button, [data-testid="stHeader"] svg { color: var(--al-texte-2) !important; }
[data-testid="stDecoration"] { background: var(--al-degrade) !important; height: 3px; }

/* ---- Barre latérale ---------------------------------------------------- */
[data-testid="stSidebar"] {
  background: var(--al-barre-laterale) !important;
  border-right: 1px solid var(--al-bordure);
}
[data-testid="stSidebar"] > div { background: transparent !important; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: var(--al-texte-2) !important;
  font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
}
[data-testid="stSidebar"] hr { margin: 1rem 0; }
[data-testid="stSidebarCollapseButton"] svg, [data-testid="stSidebarHeader"] svg { color: var(--al-texte-2) !important; }

/* ---- Onglets ------------------------------------------------------------ */
/* Streamlit >= 1.5x : onglets react-aria (stTab, role="tab") ; versions plus
   anciennes : onglets baseweb. Les deux familles de sélecteurs sont couvertes. */
.stTabs [role="tablist"] { gap: 0.25rem; border-bottom: 1px solid var(--al-bordure); }
.stTabs [role="tab"], [data-testid="stTab"] {
  color: var(--al-texte-2) !important;
  border-radius: 10px 10px 0 0;
  padding: 0.55rem 1rem !important;
  transition: color 0.15s ease, background-color 0.15s ease;
}
.stTabs [role="tab"] p { color: inherit !important; font-weight: 600; font-size: 0.95rem; }
.stTabs [role="tab"]:hover { color: var(--al-texte) !important; background: var(--al-accent-doux) !important; }
.stTabs [role="tab"][aria-selected="true"] { color: var(--al-texte) !important; }
.stTabs [role="tab"] .react-aria-SelectionIndicator, .stTabs [role="tab"] [class*="SelectionIndicator"] {
  background: var(--al-degrade) !important; height: 3px !important; border-radius: 3px;
}
.stTabs [data-baseweb="tab-list"] {
  gap: 0.25rem;
  border-bottom: 1px solid var(--al-bordure);
  background: transparent;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--al-texte-2) !important;
  height: 2.75rem; padding: 0 1rem;
  border-radius: 10px 10px 0 0;
  transition: color 0.15s ease, background-color 0.15s ease;
}
.stTabs [data-baseweb="tab"] p { color: inherit !important; font-weight: 600; font-size: 0.95rem; }
.stTabs [data-baseweb="tab"]:hover { color: var(--al-texte) !important; background: var(--al-accent-doux) !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--al-texte) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--al-degrade) !important; height: 3px; border-radius: 3px; }
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem; }

/* ---- Cartes KPI (st.metric) ----------------------------------------------- */
[data-testid="stMetric"] {
  background: var(--al-surface);
  border: 1px solid var(--al-bordure);
  border-radius: var(--al-rayon);
  padding: 1rem 1.15rem 0.9rem;
  box-shadow: var(--al-ombre);
  position: relative; overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
[data-testid="stMetric"]::before {
  content: ""; position: absolute; left: 0; top: 0; right: 0; height: 3px;
  background: var(--al-degrade); opacity: 0.9;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: var(--al-ombre-survol); }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
  color: var(--al-texte-2) !important;
  font-size: 0.85rem !important; font-weight: 600 !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
  color: var(--al-texte) !important;
  font-size: clamp(1.25rem, 1.6vw, 1.6rem) !important; font-weight: 700 !important; letter-spacing: -0.02em;
}
[data-testid="stMetricDelta"] { font-weight: 600; font-size: 0.85rem; }
[data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Up"]),
[data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Up"]) * { color: var(--al-positif) !important; }
[data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Down"]),
[data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Down"]) * { color: var(--al-negatif) !important; }

/* ---- Champs de filtre : sélecteurs, multisélections, dates, saisies ------- */
[data-testid="stWidgetLabel"] p { color: var(--al-texte-2) !important; font-weight: 500; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"],
[data-testid="stDateInput"] [data-baseweb="input"], [data-testid="stDateInputField"],
.stApp input, .stApp textarea {
  background-color: var(--al-champ) !important;
  color: var(--al-texte) !important;
  border-color: var(--al-bordure) !important;
}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-testid="stDateInputField"] {
  border-radius: 10px !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"]:focus-within,
[data-testid="stDateInputField"]:focus-within {
  border-color: var(--al-accent) !important;
  box-shadow: 0 0 0 3px var(--al-accent-doux) !important;
}
[data-baseweb="select"] span, [data-baseweb="select"] div, [data-baseweb="select"] input,
[data-testid="stDateInput"] input, [data-testid="stDateInput"] span { color: var(--al-texte) !important; }
[data-baseweb="select"] svg, [data-testid="stDateInput"] svg { color: var(--al-texte-2) !important; fill: currentColor; }
.stApp input::placeholder, [data-baseweb="select"] [aria-hidden="true"] { color: var(--al-texte-2) !important; }

/* Streamlit >= 1.5x : listes déroulantes react-aria (ComboBox, role="group") */
.react-aria-ComboBox [role="group"], [data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"][data-rac] {
  background-color: var(--al-champ) !important;
  border-color: var(--al-bordure) !important;
  border-radius: 10px !important;
  color: var(--al-texte) !important;
}
.react-aria-ComboBox [role="group"]:focus-within {
  border-color: var(--al-accent) !important;
  box-shadow: 0 0 0 3px var(--al-accent-doux) !important;
}
.react-aria-ComboBox input, .react-aria-ComboBox button { background: transparent !important; color: var(--al-texte) !important; }
.react-aria-ComboBox svg { color: var(--al-texte-2) !important; }
[data-testid="stMultiSelectTagsContainer"], [data-testid="stMultiSelectTagsContainer"] > span { background: transparent !important; }
[data-testid="stMultiSelect"] [data-tag] {
  background: var(--al-accent-doux) !important;
  border: 1px solid var(--al-accent) !important;
  border-radius: 999px !important;
  color: var(--al-texte) !important;
}
[data-testid="stMultiSelect"] [data-tag] span, [data-testid="stMultiSelect"] [data-tag] button { color: var(--al-texte) !important; background: transparent !important; }

/* Popovers react-aria (menus des listes, choix rapides de dates) */
[data-trigger], [data-testid$="Dropdown"], [data-testid="stFloatingOverlayPortal"] [role="dialog"],
[data-testid="stDateInputCalendar"] {
  background-color: var(--al-surface) !important;
  color: var(--al-texte) !important;
  border: 1px solid var(--al-bordure) !important;
  border-radius: 12px !important;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28) !important;
}
[data-trigger] [role="listbox"], [data-trigger] [role="menu"] { background: transparent !important; }
[data-trigger] [role="option"], [data-trigger] [role="menuitem"],
[data-trigger] [role="option"] *, [data-trigger] [role="menuitem"] * { color: var(--al-texte) !important; }
[data-trigger] [role="option"], [data-trigger] [role="menuitem"] { background-color: transparent !important; border-radius: 8px; }
[data-trigger] [role="option"][data-focused], [data-trigger] [role="option"][data-hovered],
[data-trigger] [role="menuitem"][data-focused], [data-trigger] [role="menuitem"][data-hovered] {
  background-color: var(--al-survol) !important;
}
[data-trigger] [role="option"][aria-selected="true"] { background-color: var(--al-accent-doux) !important; }

/* Calendrier react-aria : en-tête, jours, plage sélectionnée */
[data-testid="stDateInputCalendar"] *, [data-testid="stDateInputCalendar"] button { color: var(--al-texte) !important; }
[data-testid="stDateInputCalendar"] header button, [data-testid="stDateInputCalendar"] [role="application"],
[data-testid="stDateInputCalendar"] [role="grid"], [data-testid="stDateInputCalendar"] td,
[data-testid="stDateInputCalendar"] th { background-color: transparent !important; }
[data-testid="stDateInputCalendar"] th { color: var(--al-texte-2) !important; }
[data-testid="stDateInputCalendar"] [role="gridcell"] > div { border-radius: 8px !important; }
[data-testid="stDateInputCalendar"] [role="gridcell"] > div[data-hovered] { background-color: var(--al-survol) !important; }
[data-testid="stDateInputCalendar"] [role="gridcell"] > div[data-selected] { background-color: var(--al-accent-doux) !important; border-radius: 0 !important; }
[data-testid="stDateInputCalendar"] [role="gridcell"] > div[data-selection-start],
[data-testid="stDateInputCalendar"] [role="gridcell"] > div[data-selection-end] {
  background: var(--al-accent) !important; color: #FFFFFF !important; border-radius: 8px !important;
}
[data-testid="stDateInputCalendar"] [role="gridcell"] > div::after {
  background-color: var(--al-accent) !important; border-color: var(--al-accent) !important;
}
[data-testid="stDateInputCalendar"] [role="gridcell"] > div[data-outside-month] { color: var(--al-texte-2) !important; opacity: 0.55; }
[data-testid="stDateInputCalendar"] svg { color: var(--al-texte) !important; }

/* Interrupteur (st.toggle) */
[data-testid="stCheckbox"] label > div:not([data-testid]) { background-color: var(--al-bordure) !important; }
[data-testid="stCheckbox"] label[data-selected] > div:not([data-testid]) { background: var(--al-accent) !important; }

/* Pastilles de multisélection (baseweb, versions antérieures) */
[data-baseweb="tag"] {
  background: var(--al-accent-doux) !important;
  border: 1px solid var(--al-accent) !important;
  border-radius: 999px !important;
}
[data-baseweb="tag"] span, [data-baseweb="tag"] svg { color: var(--al-texte) !important; }

/* Menus déroulants, info-bulles et calendrier (rendus hors de l'application) */
[data-baseweb="popover"] > div, [data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"] {
  background-color: var(--al-surface) !important;
  color: var(--al-texte) !important;
  border-color: var(--al-bordure) !important;
}
[data-baseweb="popover"] > div {
  border: 1px solid var(--al-bordure);
  border-radius: 12px !important;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25) !important;
  overflow: hidden;
}
[data-baseweb="popover"] li, [data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] li span, [data-baseweb="popover"] li div { color: var(--al-texte) !important; background-color: transparent; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"], [data-baseweb="popover"] [data-highlighted="true"] {
  background-color: var(--al-survol) !important;
}
[data-baseweb="calendar"], [data-baseweb="calendar"] > div, [data-baseweb="calendar"] div[role="grid"],
[data-testid="stDateInputCalendar"] {
  background-color: var(--al-surface) !important;
  color: var(--al-texte) !important;
}
[data-baseweb="calendar"] div, [data-baseweb="calendar"] button,
[data-testid="stDateInputCalendar"] div, [data-testid="stDateInputCalendar"] button {
  color: var(--al-texte) !important;
}
[data-baseweb="calendar"] svg, [data-testid="stDateInputCalendar"] svg { color: var(--al-texte) !important; fill: currentColor; }
[data-baseweb="calendar"] [aria-roledescription="button"]:hover::after { border-color: var(--al-accent) !important; }
[data-baseweb="calendar"] [aria-selected="true"]::after,
[data-baseweb="calendar"] [aria-selected="true"]::before { background-color: var(--al-accent) !important; border-color: var(--al-accent) !important; }
[data-baseweb="calendar"] [aria-selected="true"] div { color: #FFFFFF !important; }
[data-baseweb="tooltip"], [data-baseweb="tooltip"] div {
  background-color: var(--al-surface) !important; color: var(--al-texte) !important;
}

/* Interrupteurs, cases, radios, curseurs */
.stApp [role="switch"], .stApp [data-baseweb="checkbox"] span { border-color: var(--al-bordure); }
.stApp [data-baseweb="checkbox"] input:checked + div, .stApp [role="radiogroup"] [aria-checked="true"] {
  background-color: var(--al-accent) !important;
}
.stApp [data-baseweb="slider"] [role="slider"] { background-color: var(--al-accent) !important; box-shadow: 0 0 0 4px var(--al-accent-doux); }

/* Boutons segmentés (granularité, métrique) */
[data-testid="stButtonGroup"] button {
  background: var(--al-surface) !important; color: var(--al-texte-2) !important;
  border-color: var(--al-bordure) !important;
}
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind*="Active"] {
  background: var(--al-accent-doux) !important; color: var(--al-texte) !important;
  border-color: var(--al-accent) !important;
}
[data-testid="stButtonGroup"] button p { color: inherit !important; }

/* ---- Boutons ------------------------------------------------------------ */
.stButton button, .stDownloadButton button {
  background: var(--al-bouton) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 0.55rem 1.1rem;
  box-shadow: 0 4px 14px var(--al-accent-doux);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}
.stButton button p, .stDownloadButton button p, .stButton button span, .stDownloadButton button span { color: #FFFFFF !important; }
.stButton button:hover, .stDownloadButton button:hover {
  transform: translateY(-1px); filter: brightness(1.08);
  box-shadow: var(--al-ombre-survol);
}
.stButton button:focus-visible, .stDownloadButton button:focus-visible { outline: 2px solid var(--al-accent-2); outline-offset: 2px; }
.stButton button[kind="secondary"], .stButton button[data-testid="stBaseButton-secondary"] {
  background: transparent !important; color: var(--al-texte) !important;
  border: 1px solid var(--al-bordure) !important; box-shadow: none;
}
.stButton button[kind="secondary"] p, .stButton button[data-testid="stBaseButton-secondary"] p { color: var(--al-texte) !important; }
.stButton button[kind="secondary"]:hover, .stButton button[data-testid="stBaseButton-secondary"]:hover {
  border-color: var(--al-accent) !important; background: var(--al-accent-doux) !important;
}

/* ---- Conteneurs de graphiques et de tableaux ------------------------------ */
[data-testid="stPlotlyChart"] {
  background: var(--al-surface);
  border: 1px solid var(--al-bordure);
  border-radius: var(--al-rayon);
  padding: 0.6rem 0.6rem 0.2rem;
  box-shadow: var(--al-ombre);
  overflow: hidden;
}
[data-testid="stPlotlyChart"] .modebar { background: transparent !important; }
[data-testid="stPlotlyChart"] .modebar-btn path { fill: var(--al-texte-2) !important; }
[data-testid="stDataFrame"] {
  border: 1px solid var(--al-bordure); border-radius: var(--al-rayon); overflow: hidden;
}
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stExpander"] details { background: var(--al-surface); border-color: var(--al-bordure) !important; border-radius: 12px; }

/* ---- Classes propres à Audience Lab -------------------------------------- */
.al-header {
  background: var(--al-surface);
  border: 1px solid var(--al-bordure);
  border-radius: 18px;
  padding: 1.4rem 1.6rem;
  margin-bottom: 1.2rem;
  box-shadow: var(--al-ombre);
  position: relative; overflow: hidden;
}
.al-header::after {
  content: ""; position: absolute; right: -80px; top: -80px; width: 260px; height: 260px;
  background: var(--al-degrade); opacity: 0.12; filter: blur(40px); border-radius: 50%;
  pointer-events: none;
}
.stApp .al-titre, .al-titre {
  display: inline-block; padding: 0 !important;
  font-size: 2.3rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.15;
  margin: 0;
  background: var(--al-degrade);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent !important;
}
.stApp .al-sous-titre, .al-sous-titre {
  color: var(--al-texte-2) !important; font-size: 1rem; margin: 0.45rem 0 0; line-height: 1.5;
}
.al-logo {
  display: table; margin-bottom: 0.35rem;
  font-size: 1.45rem; font-weight: 800; letter-spacing: -0.03em;
  background: var(--al-degrade);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
.stApp .al-badge, .al-badge {
  display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px; margin-bottom: 0.75rem;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
  color: var(--al-accent) !important; background: var(--al-accent-doux);
  border: 1px solid var(--al-accent);
}
.al-carte {
  background: var(--al-surface);
  border: 1px solid var(--al-bordure);
  border-radius: var(--al-rayon);
  padding: 1.1rem 1.25rem;
  box-shadow: var(--al-ombre);
}
.al-constat {
  display: flex; gap: 1rem; align-items: flex-start;
  background: var(--al-surface);
  border: 1px solid var(--al-bordure);
  border-radius: var(--al-rayon);
  padding: 1.1rem 1.25rem;
  margin-bottom: 0.9rem;
  box-shadow: var(--al-ombre);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.al-constat:hover { transform: translateY(-2px); box-shadow: var(--al-ombre-survol); border-color: var(--al-accent); }
.al-constat-icone {
  flex: 0 0 2.6rem; height: 2.6rem; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: var(--al-degrade); color: #FFFFFF !important; font-size: 1.25rem;
}
.al-constat-icone * { color: #FFFFFF !important; }
.stApp .al-constat-titre, .al-constat-titre { font-weight: 700; font-size: 1rem; margin-bottom: 0.2rem; color: var(--al-texte) !important; }
.stApp .al-constat p, .al-constat p { margin: 0; color: var(--al-texte-2) !important; line-height: 1.55; }
.stApp .al-legende, .al-legende {
  color: var(--al-texte-2) !important;
  font-size: 0.86rem; line-height: 1.5;
  margin: 0.5rem 0.25rem 1.4rem;
  padding-left: 0.75rem;
  border-left: 3px solid var(--al-accent);
}
.stApp .al-pied, .al-pied {
  margin-top: 2.5rem; padding-top: 1.1rem;
  border-top: 1px solid var(--al-bordure);
  color: var(--al-texte-2) !important; font-size: 0.82rem; text-align: center; line-height: 1.7;
}
.al-pied a { color: var(--al-accent-2) !important; text-decoration: none; }

/* ---- Apparition douce du contenu des onglets ------------------------------ */
@keyframes al-apparition { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.stTabs [data-baseweb="tab-panel"] > div { animation: al-apparition 0.35s ease-out; }
@media (prefers-reduced-motion: reduce) {
  .stTabs [data-baseweb="tab-panel"] > div, [data-testid="stMetric"], .al-constat { animation: none; transition: none; }
}
"""


def css(theme: Theme) -> str:
    """Feuille de style complète du thème, sous forme de balise <style>."""
    return (
        "<style>\n"
        f"@import url('{URL_POLICE}');\n"
        + _variables(theme)
        + _CSS_COMMUN
        + "</style>"
    )


# ---------------------------------------------------------------------------
# Habillage Plotly
# ---------------------------------------------------------------------------

def appliquer_theme(fig: go.Figure, theme: Theme) -> go.Figure:
    """Habille une figure Plotly aux couleurs du thème (modifie et renvoie fig)."""
    t = theme
    fig.update_layout(
        template="none",
        paper_bgcolor=t.surface,
        plot_bgcolor=t.surface,
        font=dict(family=POLICE, color=t.texte, size=13),
        colorway=t.sequence,
        separators=", ",
        margin=dict(l=12, r=20, t=64, b=12, autoexpand=True),
        title=dict(
            x=0, xref="container", xanchor="left", y=1, yref="container", yanchor="top",
            pad=dict(l=18, t=16),
            font=dict(size=16, color=t.texte, family=POLICE, weight=600),
            subtitle=dict(font=dict(size=12, color=t.texte_secondaire)),
        ),
        legend=dict(
            orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom",
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(size=12, color=t.texte_secondaire),
            title=dict(text=""),
        ),
        hoverlabel=dict(
            bgcolor=t.surface if t.nom == "clair" else "#1A2245",
            bordercolor=t.bordure,
            font=dict(family=POLICE, size=13, color=t.texte),
            align="left",
        ),
        coloraxis_colorbar=dict(
            outlinewidth=0, thickness=12, len=0.85,
            tickfont=dict(color=t.texte_secondaire, size=11),
            title=dict(font=dict(color=t.texte_secondaire, size=12)),
        ),
        hovermode="closest",
        bargap=0.35,
        barcornerradius=4,
    )
    axes = dict(
        showgrid=True, gridcolor=t.bordure, gridwidth=1,
        zeroline=False, showline=False,
        ticks="", tickfont=dict(color=t.texte_secondaire, size=12),
        title=dict(font=dict(color=t.texte_secondaire, size=12), standoff=12),
        automargin=True,
    )
    fig.update_xaxes(**axes)
    fig.update_yaxes(**axes)
    fig.update_geos(
        bgcolor=t.surface, showframe=False, showcoastlines=False,
        showland=True, landcolor="#EEF1F6" if t.nom == "clair" else "#1A2038",
        showcountries=True, countrycolor=t.surface, countrywidth=0.6,
        showocean=False, showlakes=False,
    )
    return fig
