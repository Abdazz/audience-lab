"""Graphiques Plotly Express d'Audience Lab.

Chaque fonction reçoit des DataFrames déjà filtrés et un `Theme`, et renvoie une
figure habillée par `appliquer_theme`. Libellés en français, valeurs de données
(appareils, catégories, étapes, pays) laissées en anglais. Si les données sont
vides, la fonction renvoie une figure vide thémée portant le message
« Aucune donnée pour ces filtres ».
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from audience.constats import JOURS_FR
from audience.kpis import formater_nombre
from audience.theme import Theme, appliquer_theme, obtenir_theme, rgba

MESSAGE_VIDE = "Aucune donnée pour ces filtres"

APPAREILS = ("desktop", "mobile", "tablet")
ETAPES = ("add_to_cart", "begin_checkout", "purchase")

UNITES = {"duration_s": " s", "n_events": " actions", "cart_value_usd": " USD"}

LIBELLES_METRIQUES = {
    "duration_s": "Durée de session (s)",
    "n_events": "Actions par session",
    "cart_value_usd": "Valeur ajoutée au panier (USD)",
}

# Dates marquantes de la période (affichées si elles tombent dans les données).
EVENEMENTS = (
    (pd.Timestamp("2020-11-27"), "Black Friday", "right"),
    (pd.Timestamp("2020-11-30"), "Cyber Monday", "left"),
    (pd.Timestamp("2020-12-25"), "Noël", "left"),
)

MOIS_COURTS = (
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
)


# ---------------------------------------------------------------------------
# Outils communs
# ---------------------------------------------------------------------------

def figure_vide(theme: Theme, titre: str = "") -> go.Figure:
    """Figure thémée sans données, avec le message « Aucune donnée pour ces filtres »."""
    fig = go.Figure()
    appliquer_theme(fig, theme)
    fig.update_layout(title_text=titre, height=320)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(
        text=MESSAGE_VIDE, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(size=15, color=theme.texte_secondaire),
    )
    return fig


def _vide(*dfs: pd.DataFrame) -> bool:
    return any(df is None or len(df) == 0 for df in dfs)


def _date_courte(jour: pd.Timestamp, avec_annee: bool = False) -> str:
    texte = f"{jour.day} {MOIS_COURTS[jour.month - 1]}"
    return f"{texte} {jour.year}" if avec_annee else texte


def _date_longue(jour: pd.Timestamp) -> str:
    return f"{jour.day:02d}/{jour.month:02d}/{jour.year}"


def _graduations_dates(debut: pd.Timestamp, fin: pd.Timestamp) -> tuple[list, list]:
    """Graduations françaises de l'axe des dates, espacées selon la durée."""
    duree = (fin - debut).days
    if duree <= 10:
        valeurs = pd.date_range(debut, fin, freq="D")
    elif duree <= 45:
        valeurs = pd.date_range(debut, fin, freq="W-MON")
    else:
        valeurs = pd.date_range(debut.replace(day=1), fin, freq="SMS")  # 1er et 15
        valeurs = valeurs[valeurs >= debut]
    textes, annee = [], None
    for jour in valeurs:
        textes.append(_date_courte(jour, avec_annee=jour.year != annee))
        annee = jour.year
    return list(valeurs), textes


def _couleurs_appareils(theme: Theme) -> dict[str, str]:
    return dict(theme.couleurs_appareils)


def _sous_titre(fig: go.Figure, texte: str) -> None:
    """Sous-titre sous le titre ; la marge haute s'agrandit pour la légende."""
    fig.update_layout(title_subtitle_text=texte, margin_t=max(fig.layout.margin.t or 0, 96))


def _valeur_reelle(x: float) -> str:
    """Valeur lisible : une décimale sous 10, entier au-delà (format français)."""
    return formater_nombre(x, 1 if x < 10 else 0)


def _moustache_haute(valeurs: pd.Series) -> float:
    """Extrémité haute de la moustache (Q3 + 1,5 IQR, bornée par le maximum)."""
    q1, q3 = valeurs.quantile([0.25, 0.75])
    return float(min(valeurs.max(), q3 + 1.5 * (q3 - q1)))


def _couleur_texte_sur(fond: str) -> str:
    """Encre lisible sur un aplat : sombre sur les teintes claires, blanche sinon."""
    h = fond.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return "#0B1020" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.45 else "#FFFFFF"


# ---------------------------------------------------------------------------
# Temporalité
# ---------------------------------------------------------------------------

def fig_evolution(
    sessions: pd.DataFrame,
    granularite: str = "D",
    par_appareil: bool = False,
    theme: Theme | None = None,
) -> go.Figure:
    """Courbe du nombre de sessions par jour ("D") ou par semaine ("W")."""
    theme = theme or _theme_defaut()
    hebdo = granularite == "W"
    titre = "Évolution du trafic " + ("par semaine" if hebdo else "par jour")
    if _vide(sessions):
        return figure_vide(theme, titre)

    jours = sessions["date"].dt.normalize()
    if hebdo:
        # Semaines du lundi au dimanche, étiquetées par leur lundi.
        periode = (jours - pd.to_timedelta(jours.dt.weekday, unit="D")).rename("date")
    else:
        periode = jours.rename("date")
    debut, fin = periode.min(), periode.max()
    pas = "7D" if hebdo else "D"
    calendrier = pd.date_range(debut, fin, freq=pas)

    if par_appareil:
        compte = (
            sessions.assign(date=periode)
            .groupby(["date", "device"]).size()
            .unstack(fill_value=0)
            .reindex(calendrier, fill_value=0)
        )
        compte.index.name = "date"
        df = compte.reset_index().melt(id_vars="date", var_name="device", value_name="sessions")
    else:
        df = (
            periode.value_counts().reindex(calendrier, fill_value=0)
            .rename_axis("date").rename("sessions").reset_index()
        )
    prefixe = "Semaine du " if hebdo else ""
    df["libelle"] = prefixe + df["date"].map(_date_longue)

    fig = px.line(
        df, x="date", y="sessions",
        color="device" if par_appareil else None,
        color_discrete_map=_couleurs_appareils(theme),
        category_orders={"device": list(APPAREILS)},
        custom_data=["libelle"],
        labels={"date": "", "sessions": "Sessions", "device": "Appareil"},
        title=titre,
    )
    appliquer_theme(fig, theme)

    marqueurs = len(df["date"].unique()) <= 31
    if par_appareil:
        fig.update_traces(
            line=dict(width=2.2),
            hovertemplate="<b>%{fullData.name}</b> : %{y:,.0f} sessions<extra></extra>",
        )
        fig.update_layout(hovermode="x unified")
    else:
        fig.update_traces(
            line=dict(width=2.4, color=theme.accent),
            fill="tozeroy", fillcolor=rgba(theme.accent, 0.12),
            hovertemplate="<b>%{customdata[0]}</b><br>%{y:,.0f} sessions<extra></extra>",
        )
        fig.update_layout(hovermode="x")
    fig.update_traces(
        mode="lines+markers" if marqueurs else "lines",
        marker=dict(size=7, line=dict(width=2, color=theme.surface)),
    )
    if hebdo:
        premier, dernier = jours.min(), jours.max()
        if premier.weekday() != 0 or dernier.weekday() != 6:
            _sous_titre(fig, "Semaines du lundi au dimanche ; la première et la dernière"
                        " peuvent être incomplètes")

    valeurs, textes = _graduations_dates(debut, fin)
    fig.update_xaxes(
        tickvals=valeurs, ticktext=textes, showgrid=False,
        hoverformat=("Semaine du " if hebdo else "") + "%d/%m/%Y",
        showspikes=True, spikemode="across", spikethickness=1,
        spikecolor=theme.texte_secondaire, spikedash="solid",
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",.0f", title_text="Sessions")

    # Lignes verticales des dates marquantes, uniquement dans la période observée.
    fin_periode = sessions["date"].dt.normalize().max()
    debut_periode = sessions["date"].dt.normalize().min()
    for jour, libelle, cote in EVENEMENTS:
        if not (debut_periode <= jour <= fin_periode):
            continue
        fig.add_shape(
            type="line", x0=jour, x1=jour, y0=0, y1=1, xref="x", yref="paper",
            line=dict(color=theme.texte_secondaire, width=1), opacity=0.55, layer="below",
        )
        fig.add_annotation(
            x=jour, y=1, xref="x", yref="paper", yanchor="top",
            xanchor=cote, xshift=-4 if cote == "right" else 4,
            text=libelle, showarrow=False,
            font=dict(size=11, color=theme.texte_secondaire),
            bgcolor=rgba(theme.surface, 0.85),
        )
    fig.update_layout(height=420)
    return fig


def fig_heatmap_heure_jour(sessions: pd.DataFrame, theme: Theme | None = None) -> go.Figure:
    """Sessions par heure (colonnes) et jour de la semaine (lignes, lundi en haut)."""
    theme = theme or _theme_defaut()
    titre = "Sessions par heure et jour de la semaine"
    if _vide(sessions):
        return figure_vide(theme, titre)

    grille = (
        pd.crosstab(sessions["weekday"], sessions["hour"])
        .reindex(index=range(7), columns=range(24), fill_value=0)
    )
    fig = px.imshow(
        grille.to_numpy(),
        x=list(range(24)), y=list(JOURS_FR),
        color_continuous_scale=theme.echelle_continue,
        aspect="auto",
        labels={"x": "Heure", "y": "", "color": "Sessions"},
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        xgap=2, ygap=2,
        hovertemplate="<b>%{y}, %{x} h</b><br>%{z:,.0f} sessions<extra></extra>",
    )
    fig.update_xaxes(
        showgrid=False, tickmode="array", tickvals=list(range(0, 24, 2)),
        ticktext=[f"{h} h" for h in range(0, 24, 2)], side="bottom", title_text="",
    )
    fig.update_yaxes(showgrid=False)
    fig.update_layout(height=380, coloraxis_colorbar=dict(title_text="Sessions", tickformat=",.0f"))
    return fig


# ---------------------------------------------------------------------------
# Audience
# ---------------------------------------------------------------------------

def fig_parts_appareils(sessions: pd.DataFrame, theme: Theme | None = None) -> go.Figure:
    """Anneau de la répartition des sessions par appareil."""
    theme = theme or _theme_defaut()
    titre = "Répartition des sessions par appareil"
    if _vide(sessions):
        return figure_vide(theme, titre)

    parts = (
        sessions["device"].value_counts()
        .reindex([a for a in APPAREILS if a in set(sessions["device"])], fill_value=0)
        .rename_axis("device").rename("sessions").reset_index()
    )
    fig = px.pie(
        parts, names="device", values="sessions", hole=0.6,
        color="device", color_discrete_map=_couleurs_appareils(theme),
        category_orders={"device": list(APPAREILS)},
        labels={"device": "Appareil", "sessions": "Sessions"},
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        sort=False, direction="clockwise", rotation=0,
        marker=dict(line=dict(color=theme.surface, width=3)),
        texttemplate="%{percent:.1%}", textposition="outside",
        textfont=dict(size=13, color=theme.texte),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} sessions<br>%{percent:.1%}<extra></extra>",
    )
    fig.add_annotation(
        text=(
            f"<b style='font-size:24px'>{formater_nombre(len(sessions))}</b>"
            f"<br><span style='color:{theme.texte_secondaire}'>sessions</span>"
        ),
        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(size=13, color=theme.texte),
    )
    fig.update_layout(
        height=380, showlegend=True,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.08, yanchor="top"),
        margin=dict(t=72, b=40),
    )
    return fig


def fig_categories(
    events: pd.DataFrame, metrique: str = "add_to_cart", theme: Theme | None = None
) -> go.Figure:
    """Top 12 des catégories : ajouts au panier (nombre) ou chiffre d'affaires (USD)."""
    theme = theme or _theme_defaut()
    ca = metrique == "revenue"
    titre = (
        "Chiffre d'affaires par catégorie (top 12)" if ca
        else "Ajouts au panier par catégorie (top 12)"
    )
    if _vide(events):
        return figure_vide(theme, titre)

    if ca:
        achats = events[events["type"] == "purchase"]
        valeurs = achats.groupby("item_category")["price_in_usd"].sum()
        axe, format_valeur, unite = "Chiffre d'affaires (USD)", "%{x:,.0f}", " USD"
    else:
        valeurs = events.loc[events["type"] == "add_to_cart", "item_category"].value_counts()
        axe, format_valeur, unite = "Ajouts au panier", "%{x:,.0f}", ""
    valeurs = valeurs[valeurs > 0]
    if valeurs.empty:
        return figure_vide(theme, titre)

    top = valeurs.sort_values(ascending=False).head(12)
    df = top.rename_axis("item_category").rename("valeur").reset_index()
    df["part"] = df["valeur"] / valeurs.sum()
    df = df.iloc[::-1]  # la plus grande barre en haut

    fig = px.bar(
        df, x="valeur", y="item_category", orientation="h",
        custom_data=["part"],
        labels={"valeur": axe, "item_category": ""},
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        marker_color=theme.accent, marker_line_width=0,
        texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False,
        textfont=dict(size=12, color=theme.texte_secondaire),
        hovertemplate=(
            "<b>%{y}</b><br>" + format_valeur + unite +
            "<br>%{customdata[0]:.1%} du total<extra></extra>"
        ),
    )
    fig.update_xaxes(tickformat=",.0f", showgrid=True)  # unité dans le titre de l'axe
    fig.update_yaxes(showgrid=False, ticksuffix="  ")
    fig.update_layout(height=max(320, 34 * len(df) + 110), margin=dict(r=60))
    return fig


def _sessions_par_pays(sessions: pd.DataFrame) -> pd.DataFrame:
    return (
        sessions.groupby(["country", "country_iso3", "country_name"], dropna=False)
        .size().rename("sessions").reset_index()
        .sort_values("sessions", ascending=False)
    )


def fig_carte_pays(sessions: pd.DataFrame, theme: Theme | None = None) -> go.Figure:
    """Carte choroplèthe des sessions par pays (échelle de couleur logarithmique)."""
    theme = theme or _theme_defaut()
    titre = "Sessions par pays"
    if _vide(sessions):
        return figure_vide(theme, titre)
    df = _sessions_par_pays(sessions.dropna(subset=["country_iso3"]))
    if df.empty:
        return figure_vide(theme, titre)

    df["log_sessions"] = np.log10(df["sessions"])
    df["part"] = df["sessions"] / len(sessions)
    fig = px.choropleth(
        df, locations="country_iso3", locationmode="ISO-3", color="log_sessions",
        hover_name="country_name",
        custom_data=["country_name", "sessions", "part"],
        color_continuous_scale=theme.echelle_continue,
        projection="natural earth",
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        marker_line_color=theme.surface, marker_line_width=0.5,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} sessions"
            "<br>%{customdata[2]:.1%} du trafic<extra></extra>"
        ),
    )
    maxi = int(np.ceil(df["log_sessions"].max())) if df["log_sessions"].max() > 0 else 1
    graduations = list(range(0, maxi + 1))
    fig.update_layout(
        height=440, margin=dict(l=0, r=0, t=64, b=0),
        coloraxis=dict(cmin=-0.75, cmax=max(maxi, 1)),
        coloraxis_colorbar=dict(
            title_text="Sessions", tickvals=graduations,
            ticktext=[formater_nombre(10 ** k) for k in graduations],
        ),
    )
    _sous_titre(fig, "Échelle de couleur logarithmique : chaque palier multiplie le trafic par 10")
    fig.update_geos(fitbounds=False, lataxis_range=[-58, 85])
    return fig


def fig_top_pays(sessions: pd.DataFrame, theme: Theme | None = None) -> go.Figure:
    """Barres horizontales des 10 pays les plus représentés."""
    theme = theme or _theme_defaut()
    titre = "Top 10 des pays"
    if _vide(sessions):
        return figure_vide(theme, titre)

    df = _sessions_par_pays(sessions).head(10).copy()
    df["part"] = df["sessions"] / len(sessions)
    df["pays"] = df["country_name"].fillna(df["country"])
    df = df.iloc[::-1]
    fig = px.bar(
        df, x="sessions", y="pays", orientation="h",
        custom_data=["part", "country"],
        labels={"sessions": "Sessions", "pays": ""},
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        marker_color=theme.accent_2, marker_line_width=0,
        texttemplate="%{customdata[0]:.1%}", textposition="outside", cliponaxis=False,
        textfont=dict(size=12, color=theme.texte_secondaire),
        hovertemplate=(
            "<b>%{y}</b> (%{customdata[1]})<br>%{x:,.0f} sessions"
            "<br>%{customdata[0]:.1%} du trafic<extra></extra>"
        ),
    )
    fig.update_xaxes(tickformat=",.0f")
    fig.update_yaxes(showgrid=False, ticksuffix="  ")
    fig.update_layout(height=max(320, 34 * len(df) + 110), margin=dict(r=60))
    return fig


# ---------------------------------------------------------------------------
# Engagement
# ---------------------------------------------------------------------------

def _preparer_engagement(
    sessions: pd.DataFrame, metrique: str, log: bool
) -> tuple[pd.DataFrame, str]:
    """Filtre les valeurs nulles en échelle log ; renvoie (df, note)."""
    df = sessions[["device", metrique]].dropna()
    note = ""
    if log:
        nuls = int((df[metrique] <= 0).sum())
        df = df[df[metrique] > 0]
        note = "Échelle logarithmique"
        if nuls:
            note += f" ; {formater_nombre(nuls)} sessions à valeur nulle exclues"
    return df, note


def fig_engagement_boite(
    sessions: pd.DataFrame,
    metrique: str = "duration_s",
    log: bool = False,
    theme: Theme | None = None,
) -> go.Figure:
    """Boîtes à moustaches de la métrique d'engagement par appareil."""
    theme = theme or _theme_defaut()
    libelle = LIBELLES_METRIQUES.get(metrique, metrique)
    titre = f"{libelle} selon l'appareil"
    if _vide(sessions):
        return figure_vide(theme, titre)
    df, note = _preparer_engagement(sessions, metrique, log)
    if df.empty:
        return figure_vide(theme, titre)

    fig = px.box(
        df, x="device", y=metrique, color="device",
        color_discrete_map=_couleurs_appareils(theme),
        category_orders={"device": [a for a in APPAREILS if a in set(df["device"])]},
        log_y=log, points="outliers",
        labels={"device": "Appareil", metrique: libelle},
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        line=dict(width=1.6), whiskerwidth=0.4,
        marker=dict(size=4, opacity=0.35, line=dict(width=0)),
        boxmean=True, hoverinfo="skip",
    )
    for trace in fig.data:
        trace.fillcolor = rgba(theme.couleurs_appareils.get(trace.name, theme.accent), 0.22)

    # Info-bulle en français : un point invisible par appareil porte les statistiques
    # (les info-bulles natives des boîtes affichent q1, median... en anglais).
    stats = df.groupby("device")[metrique].describe()
    for appareil in [t.name for t in fig.data]:
        ligne = stats.loc[appareil]
        fig.add_trace(go.Scatter(
            x=[appareil], y=[ligne["50%"]], mode="markers",
            marker=dict(size=40, opacity=0), showlegend=False, name=appareil,
            customdata=[[ligne["count"], ligne["25%"], ligne["mean"], ligne["75%"]]],
            hovertemplate=(
                f"<b>{appareil}</b> · %{{customdata[0]:,.0f}} sessions"
                "<br>1er quartile : %{customdata[1]:,.0f}"
                "<br>Médiane : %{y:,.0f}"
                "<br>Moyenne : %{customdata[2]:,.0f}"
                "<br>3e quartile : %{customdata[3]:,.0f}<extra></extra>"
            ),
        ))
    fig.update_xaxes(showgrid=False, title_text="")
    fig.update_yaxes(title_text=libelle, tickformat=",.0f")
    if log:
        fig.update_yaxes(dtick=1)  # une graduation par puissance de 10
    else:
        # Axe resserré sur les moustaches pour que les boîtes restent lisibles.
        # Plus haute moustache parmi les appareils : aucune boîte n'est coupée.
        moustache = max(_moustache_haute(v) for _, v in df.groupby("device")[metrique])
        if moustache > 0:
            fig.update_yaxes(range=[0, moustache * 1.2])
            note = "Axe resserré sur les boîtes : valeurs extrêmes hors cadre (double-clic pour tout voir)"
    _sous_titre(fig, (note + " ; " if note else "") + "trait plein : médiane, pointillé : moyenne")
    fig.update_layout(height=420, showlegend=False, hovermode="x")
    return fig


def fig_engagement_densite(
    sessions: pd.DataFrame,
    metrique: str = "duration_s",
    log: bool = False,
    theme: Theme | None = None,
) -> go.Figure:
    """Histogrammes de densité superposés de la métrique, un par appareil."""
    theme = theme or _theme_defaut()
    libelle = LIBELLES_METRIQUES.get(metrique, metrique)
    titre = f"Distribution : {libelle.lower()}"
    if _vide(sessions):
        return figure_vide(theme, titre)
    df, note = _preparer_engagement(sessions, metrique, log)
    if df.empty:
        return figure_vide(theme, titre)

    colonne = metrique
    if log:
        colonne = "log10"
        df = df.assign(log10=np.log10(df[metrique]))
        debut, fin = float(df["log10"].min()), float(df["log10"].max())
    else:
        debut, fin = 0.0, float(df[metrique].quantile(0.99))
        note = "Axe limité au 99e centile"
    if fin <= debut:
        fin = debut + 1
    taille = (fin - debut) / 50
    if not log and np.allclose(df[metrique] % 1, 0):
        taille = max(1.0, float(np.ceil(taille)))  # valeurs entières : pas de classes vides

    fig = px.histogram(
        df, x=colonne, color="device",
        histnorm="probability density", barmode="overlay", opacity=0.55,
        color_discrete_map=_couleurs_appareils(theme),
        category_orders={"device": list(APPAREILS)},
        labels={"device": "Appareil", colonne: libelle},
        title=titre,
    )
    appliquer_theme(fig, theme)
    fig.update_traces(
        xbins=dict(start=debut, end=fin + taille, size=taille),
        hovertemplate="<b>%{fullData.name}</b><br>Densité : %{y:.3~g}<extra></extra>",
    )
    # Aplat léger + contour plein : les superpositions restent lisibles sans virer au brun.
    for trace in fig.data:
        couleur = theme.couleurs_appareils.get(trace.name, theme.accent)
        trace.marker = dict(color=rgba(couleur, 0.18), line=dict(color=couleur, width=1.5))
    fig.update_layout(barcornerradius=0, bargap=0.04, hovermode="x unified", height=420)
    fig.update_yaxes(title_text="Densité", tickformat=".2~g")
    if log:
        graduations = list(range(int(np.floor(debut)), int(np.ceil(fin)) + 1))
        fig.update_xaxes(
            title_text=f"{libelle}, échelle log",
            tickvals=graduations, ticktext=[formater_nombre(10 ** k) for k in graduations],
            unifiedhovertitle=dict(text=f"<b>{libelle}</b>"),
        )
        # L'axe porte des log10 : un point invisible par classe donne au survol
        # les bornes de la classe en valeurs réelles (« De 200 à 251 s »).
        bords = debut + taille * np.arange(len(np.arange(debut, fin + taille / 2, taille)) + 1)
        unite = UNITES.get(metrique, "")
        etiquettes = [
            [f"De {_valeur_reelle(10 ** a)} à {_valeur_reelle(10 ** b)}{unite}"]
            for a, b in zip(bords[:-1], bords[1:])
        ]
        fig.add_trace(go.Scatter(
            x=(bords[:-1] + bords[1:]) / 2, y=np.zeros(len(etiquettes)),
            mode="markers", marker=dict(opacity=0, color=theme.texte_secondaire),
            showlegend=False, name="Classe", customdata=etiquettes,
            hovertemplate="%{customdata[0]}<extra></extra>",
        ))
        fig.data = (fig.data[-1],) + tuple(fig.data[:-1])  # bornes en tête de l'info-bulle
    else:
        fig.update_xaxes(range=[debut, fin], tickformat=",.0f", title_text=libelle)
    _sous_titre(fig, note + " ; aire de chaque appareil normalisée à 1")
    return fig


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def fig_entonnoir(
    sessions: pd.DataFrame, events: pd.DataFrame, theme: Theme | None = None
) -> go.Figure:
    """Entonnoir : sessions ayant au moins un événement de chaque étape, par appareil."""
    theme = theme or _theme_defaut()
    titre = "Entonnoir de conversion par appareil"
    if _vide(sessions, events):
        return figure_vide(theme, titre)

    ev = events[events["type"].isin(ETAPES) & events["session_key"].isin(sessions["session_key"])]
    if ev.empty:
        return figure_vide(theme, titre)
    paires = ev[["session_key", "device", "type"]].drop_duplicates()
    df = (
        paires.groupby(["type", "device"]).size().rename("sessions").reset_index()
        .rename(columns={"type": "etape"})
    )
    # Part de chaque étape rapportée aux sessions add_to_cart du même appareil.
    base = df[df["etape"] == "add_to_cart"].set_index("device")["sessions"]
    df["part"] = df["sessions"] / df["device"].map(base)
    df["etape"] = pd.Categorical(df["etape"], categories=list(ETAPES), ordered=True)
    df = df.sort_values(["etape", "device"])

    cles = {t: set(paires.loc[paires["type"] == t, "session_key"]) for t in ETAPES}
    sans_panier = len(cles["begin_checkout"] - cles["add_to_cart"])

    appareils = [a for a in APPAREILS if a in set(df["device"])]
    fig = px.funnel(
        df, x="sessions", y="etape", color="device",
        color_discrete_map=_couleurs_appareils(theme),
        category_orders={"device": appareils, "etape": list(ETAPES)},
        custom_data=["part"],
        labels={"sessions": "Sessions", "etape": "Étape", "device": "Appareil"},
        title=titre,
    )
    appliquer_theme(fig, theme)
    for trace in fig.data:
        couleur = theme.couleurs_appareils.get(trace.name, theme.accent)
        trace.textfont = dict(color=_couleur_texte_sur(couleur), size=12)
    fig.update_traces(
        texttemplate="%{x:,.0f}", textposition="inside",
        marker=dict(line=dict(color=theme.surface, width=2)),
        connector=dict(visible=False),  # empilé par appareil : les liaisons se chevauchent
        hovertemplate=(
            "<b>%{fullData.name}</b> · %{y}<br>%{x:,.0f} sessions"
            "<br>%{customdata[0]:.1%} des sessions add_to_cart<extra></extra>"
        ),
    )
    sous_titre = "Sessions ayant atteint chaque étape"
    if sans_panier:
        sous_titre += (
            f" ; étapes non imbriquées : {formater_nombre(sans_panier)} sessions"
            " begin_checkout sans add_to_cart"
        )
    _sous_titre(fig, sous_titre)
    fig.update_yaxes(
        showgrid=False, title_text="", ticksuffix="  ",
        categoryorder="array", categoryarray=list(ETAPES), autorange="reversed",
    )
    fig.update_xaxes(showgrid=False, visible=False)
    fig.update_layout(height=400, funnelmode="stack", uniformtext=dict(minsize=11, mode="hide"))
    return fig


def _theme_defaut() -> Theme:
    return obtenir_theme("sombre")
