# Audience Lab : plan de développement

> **Pour les agents d'exécution :** sous-skill requis : superpowers:subagent-driven-development (recommandé) ou superpowers:executing-plans pour exécuter ce plan tâche par tâche. Les étapes utilisent des cases à cocher (`- [ ]`).

**Objectif :** livrer ce soir un notebook de préparation, une application Streamlit `app.py` déployée en ligne (thèmes sombre et clair, KPI, 6 onglets), un rapport PDF et un support de soutenance, sur les données Google Merchandise Store.

**Architecture :** le notebook est le pipeline de nettoyage : il lit `data/raw/`, écrit `data/processed/*.parquet` et les figures Seaborn du rapport. L'application ne lit que les fichiers traités ; sa logique (filtres, KPI, constats, thèmes, graphiques) vit dans le paquet `audience/`, testé unitairement, et `app.py` ne fait que la mise en page. Rapport et diapositives sont des pages HTML imprimées en PDF par Chromium headless.

**Pile technique :** Python 3.12, pandas, numpy, pyarrow, seaborn, matplotlib, plotly, streamlit, pycountry, jupyter / nbconvert, pytest, Chromium headless.

**Spécification :** `docs/specs/2026-10-19-conception-tableau-de-bord.md`

## Contraintes globales

- Aucun caractère cadratin U+2014 dans aucun fichier du dépôt (code, notebook et ses sorties, HTML, Markdown, PDF extrait en texte). Remplacer par deux-points, virgule, parenthèses ou « - ».
- Valeurs de données jamais traduites (`desktop`, `mobile`, `tablet`, `add_to_cart`, `begin_checkout`, `purchase`, `Apparel`, codes pays). Tous les libellés, titres et textes en français.
- API du cours visibles : `px.line`, `px.bar`, `px.pie`, `px.box`, `px.histogram`, `px.imshow` ou `px.density_heatmap`, `px.choropleth`, `px.funnel`, `sns.boxplot`, `sns.histplot(kde=True)`, `sns.heatmap(annot=True, cmap=...)`, `st.sidebar`, `st.metric`, `st.plotly_chart`, `st.download_button`.
- Thème sombre : fond `#0B1020`, surface `#141B35`, bordure `#232D55`, texte `#E6E9F5`, texte secondaire `#94A3B8`, accents `#8B5CF6` et `#22D3EE`, rose `#F472B6`, positif `#34D399`, négatif `#F87171`.
- Thème clair : fond `#F5F7FB`, surface `#FFFFFF`, bordure `#E5E9F2`, texte `#0F172A`, texte secondaire `#64748B`, accent `#4F46E5`, secondaire `#0EA5E9`, ambre `#F59E0B`, positif `#059669`, négatif `#DC2626`.
- Thème par défaut : clair (décision de l'étudiant du 19 octobre 2026, le thème sombre reste accessible par la bascule).
- Auteur : Abdoul-Aziz ZOROM, Master 1 IA, Université Aube-Nouvelle ; enseignant : Dr. Zakaria Sawadogo ; date : 19 octobre 2026.
- Dépôt : `https://github.com/Abdazz/audience-lab`. Toute action publique (push, déploiement) seulement avec l'accord explicite de l'étudiant.
- `requirements.txt` avec versions exactes (celles installées) ; `.venv/` non versionné.

## Revue : points d'attention

1. Filtres qui ne laissent aucune donnée (ex. pays sans session sur la période) : chaque onglet affiche un message « Aucune donnée pour ces filtres », aucune exception. Test : `test_app_filtres_vides` (tâche 7) et `test_figures_df_vide` (tâche 6).
2. Thème sombre actif mais graphiques restés clairs : chaque figure doit porter le fond et la couleur de texte du thème. Test : `test_figures_suivent_theme` (tâche 6).
3. Période dont la période précédente est hors données (début au 2020-11-01) : delta absent (`None`), pas de division par zéro. Test : `test_kpis_periode_precedente_vide` (tâche 4).
4. Période d'un seul jour : la heatmap garde une grille complète 7 x 24 (zéros), la courbe s'affiche. Test : `test_heatmap_grille_complete` (tâche 6).
5. `st.date_input` en mode plage renvoie un seul élément pendant la sélection : l'application utilise alors ce jour comme début et fin, sans erreur. Test : `test_normaliser_periode_un_jour` (tâche 3).

---

### Tâche 1 : socle du projet et données brutes

**Fichiers :**
- Créer : `requirements.txt`, `.gitignore`, `scripts/telecharger_donnees.py`, `data/raw/events.csv`, `data/raw/items.csv`, `data/raw/users.csv`, `audience/__init__.py`, `tests/test_sans_cadratin.py`, `pytest.ini`
- Déplacer : `.superpowers/` reste hors dépôt (dans `.gitignore`)

**Interfaces :**
- Produit : `data/raw/*.csv` (format décrit dans la spec, section 3) ; paquet importable `audience`.

- [ ] **Étape 1 : environnement.** `python3 -m venv .venv && .venv/bin/pip install pandas numpy pyarrow seaborn matplotlib plotly streamlit pycountry jupyter nbconvert ipykernel pytest`, puis écrire `requirements.txt` avec les versions exactes de `pandas numpy pyarrow seaborn matplotlib plotly streamlit pycountry` (sans jupyter ni pytest, inutiles en ligne) et `requirements-dev.txt` qui inclut `-r requirements.txt` plus jupyter, nbconvert, ipykernel, pytest.
- [ ] **Étape 2 : `scripts/telecharger_donnees.py`.** Télécharge les trois URL de la spec (section 3), décompresse le gzip, écrit `data/raw/{events,items,users}.csv`, vérifie l'en-tête attendu (`user_id,ga_session_id,country,device,type,item_id,date` ; `id,name,brand,variant,category,price_in_usd` ; `id,ltv,date`) et le nombre de lignes (758 884 / 1 381 / 270 154). Exécuter.
- [ ] **Étape 3 : test anti-cadratin** `tests/test_sans_cadratin.py::test_aucun_cadratin_dans_le_depot` : parcourt tous les fichiers suivis (extensions `.py .md .ipynb .html .css .toml .txt .csv .json`, hors `.venv`, `.git`, `.superpowers`) et vérifie que `chr(0x2014)` n'apparaît dans aucun. Message d'échec : liste des fichiers et lignes fautifs.
- [ ] **Étape 4 : lancer** `.venv/bin/pytest -q` : PASS.
- [ ] **Étape 5 : `git init -b main`**, `.gitignore` (`.venv/ __pycache__/ .ipynb_checkpoints/ .superpowers/ .pytest_cache/`), premier commit `chore: socle du projet et données brutes`.

### Tâche 2 : notebook de préparation (pipeline de nettoyage)

**Fichiers :**
- Créer : `notebooks/01_preparation_donnees.ipynb`, `data/processed/events_clean.parquet`, `data/processed/sessions.parquet`, `rapport/figures/*.png`
- Test : `tests/test_donnees_traitees.py`

**Interfaces :**
- Consomme : `data/raw/*.csv`.
- Produit `events_clean.parquet` : `user_id:int64, ga_session_id:int64, session_key:str ("{user_id}_{ga_session_id}"), country:str, country_iso3:str|None, country_name:str, device:str, type:str, item_id:int64, item_name:str, item_category:str, item_brand:str, price_in_usd:float64, timestamp:datetime64[ns], date:datetime64[ns] (minuit), hour:int (0-23), weekday:int (0 = lundi), month:str ("2020-11")`.
- Produit `sessions.parquet` (une ligne par session) : `session_key, user_id, ga_session_id, country, country_iso3, country_name, device, start, end (datetime64), date (minuit du début), hour, weekday, duration_s:float, n_events:int, n_items:int, cart_value_usd:float (somme des prix des add_to_cart), revenue_usd:float (somme des prix des purchase), reached_checkout:bool, purchased:bool, main_category:str (catégorie la plus fréquente), is_outlier_duration:bool, is_outlier_events:bool`.

- [ ] **Étape 1 : tests** `tests/test_donnees_traitees.py` :
  - `test_fichiers_existent` : les deux parquet existent.
  - `test_schema_events` / `test_schema_sessions` : colonnes ci-dessus présentes, `timestamp` et `start` de type datetime.
  - `test_aucun_pays_manquant` : `country` sans NaN ; `(len(events[events.country == "(not set)"]) > 0)`.
  - `test_aucun_doublon` : `events.duplicated().sum() == 0`.
  - `test_valeurs_non_traduites` : `set(events.device) == {"desktop","mobile","tablet"}` et `set(events.type) == {"add_to_cart","begin_checkout","purchase"}`.
  - `test_coherence_sessions` : `sessions.session_key.is_unique` ; `sessions.n_events.sum() == len(events)` ; `abs(sessions.revenue_usd.sum() - events.loc[events.type=="purchase","price_in_usd"].sum()) < 1e-6` ; `(sessions.duration_s >= 0).all()` ; `((sessions.revenue_usd > 0) == sessions.purchased).all()`.
  - `test_periode` : `events.timestamp.min() >= "2020-11-01"` et `max() < "2021-02-01"`.
  - `test_figures_rapport` : présence de `rapport/figures/` avec au moins `evolution_trafic.png, categories.png, engagement_appareil.png, heatmap_heure_jour.png, correlation.png`.
- [ ] **Étape 2 : lancer** `.venv/bin/pytest tests/test_donnees_traitees.py -q` : FAIL (fichiers absents).
- [ ] **Étape 3 : écrire le notebook**, cellules Markdown en français avant chaque bloc, dans cet ordre :
  1. Titre, contexte, source et licence.
  2. Chargement des trois CSV ; `shape`, `dtypes`, `info()`, `head()`, `describe()`, cardinalités `nunique()`.
  3. Valeurs manquantes (`isna().sum()`, pourcentage) : `country` manquant remplacé par `"(not set)"` (convention Google Analytics), justification écrite.
  4. Doublons : compte, suppression avec `drop_duplicates()`, chiffres avant / après, justification (événements GA dupliqués au même horodatage).
  5. Conversion `pd.to_datetime`, démonstration d'indexation temporelle (`set_index("timestamp").resample("D").size()` et `df.plot()` style cours).
  6. Jointure `items` (préfixe `item_`), contrôle qu'aucune ligne n'est perdue ; enrichissement pays via `pycountry` (`country_iso3`, `country_name`, `"(not set)"` gardé tel quel, iso3 `None`).
  7. Variables dérivées : `date, hour, weekday, month`.
  8. Construction des sessions (`groupby("session_key").agg(...)`), colonnes de l'interface ci-dessus.
  9. Valeurs aberrantes : bornes IQR (Q3 + 1,5 x IQR) sur `duration_s` et `n_events`, boxplots avant décision, indicateurs `is_outlier_*` conservés (pas de suppression : ce sont de vrais comportements, l'application les garde et le rapport l'explique).
  10. KPI de l'étape 2 calculés et affichés (sessions, utilisateurs, événements, durée moyenne, valeur moyenne par session, répartition par appareil et par catégorie).
  11. Figures Seaborn / Matplotlib (style sobre, `dpi=200`, titres et axes en français) enregistrées dans `rapport/figures/` : `evolution_trafic.png` (sessions par jour), `categories.png` (barres des catégories), `engagement_appareil.png` (`sns.boxplot` + `sns.histplot(kde=True)` de la durée par appareil, échelle log justifiée), `heatmap_heure_jour.png` (`sns.heatmap(annot=True)`, jours lundi à dimanche en français), `correlation.png` (matrice de corrélation des variables numériques de session, `cmap="coolwarm"`), `entonnoir.png`.
  12. Interprétation courte sous chaque figure ; note sur le fuseau horaire non documenté.
  13. Export parquet.
- [ ] **Étape 4 : exécuter** `.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/01_preparation_donnees.ipynb` puis `.venv/bin/pytest -q` : PASS (y compris l'anti-cadratin sur les sorties du notebook).
- [ ] **Étape 5 : commit** `feat: notebook de préparation et données traitées`.

### Tâche 3 : chargement et filtres

**Fichiers :** Créer `audience/donnees.py` ; Test `tests/test_donnees.py`

**Interfaces :**
- Consomme : parquet de la tâche 2.
- Produit :
  - `CHEMIN_EVENTS: Path`, `CHEMIN_SESSIONS: Path` (relatifs à la racine du dépôt, calculés depuis `__file__`).
  - `charger_donnees() -> tuple[pd.DataFrame, pd.DataFrame]` : (events, sessions). Non décoré ; `app.py` l'enveloppe dans `st.cache_data`.
  - `@dataclass(frozen=True) class Filtres: debut: date; fin: date; appareils: tuple[str, ...]; pays: tuple[str, ...]; categories: tuple[str, ...]` (tuple vide = pas de filtre sur ce critère).
  - `normaliser_periode(valeur, defaut: tuple[date, date]) -> tuple[date, date]` : accepte un tuple de 0, 1 ou 2 dates (sortie brute de `st.date_input`) ; 1 date donne (d, d) ; 0 donne `defaut` ; dates inversées remises dans l'ordre.
  - `filtrer(events, sessions, f: Filtres) -> tuple[pd.DataFrame, pd.DataFrame]` : période sur `date` (bornes incluses) pour les deux tables ; appareils et pays sur les deux ; catégories : events filtrés sur `item_category`, sessions restreintes à celles ayant au moins un événement retenu.
  - `periode_precedente(f: Filtres) -> Filtres` : même durée, se terminant la veille de `f.debut`, autres critères identiques.

- [ ] **Étape 1 : tests** sur de petits DataFrames construits dans une fixture (3 sessions, 2 appareils, 2 catégories, 2 jours) : `test_filtrer_periode`, `test_filtrer_appareil`, `test_filtrer_categorie_restreint_sessions`, `test_filtres_vides_ne_filtrent_pas`, `test_normaliser_periode_un_jour` (`(d,)` donne `(d, d)`), `test_normaliser_periode_vide`, `test_normaliser_periode_inversee`, `test_periode_precedente` (1er au 7 déc. donne 24 au 30 nov.), `test_charger_donnees` (vraies données : 2 DataFrames non vides).
- [ ] **Étape 2 :** `.venv/bin/pytest tests/test_donnees.py -q` : FAIL (module absent).
- [ ] **Étape 3 :** implémenter `audience/donnees.py`.
- [ ] **Étape 4 :** pytest : PASS.
- [ ] **Étape 5 :** commit `feat: chargement et filtrage des données`.

### Tâche 4 : indicateurs clés

**Fichiers :** Créer `audience/kpis.py` ; Test `tests/test_kpis.py`

**Interfaces :**
- Consomme : `filtrer`, `periode_precedente`, `Filtres` (tâche 3).
- Produit :
  - `calculer_kpis(sessions: pd.DataFrame) -> dict[str, float | None]` avec les clés exactes `sessions, utilisateurs, duree_moyenne_s, panier_moyen_usd, taux_conversion, part_mobile, chiffre_affaires_usd`. DataFrame vide : `sessions = utilisateurs = 0`, autres `None`.
  - `variations(actuel: dict, precedent: dict) -> dict[str, float | None]` : variation relative en % pour chaque clé ; `None` si la valeur précédente est `None` ou 0. Pour `taux_conversion` et `part_mobile`, différence en points de pourcentage.
  - `formater_duree(secondes: float | None) -> str` : `"4 min 12 s"`, `"45 s"`, `"1 h 05 min"`, `None` donne `"n.d."`.
  - `formater_nombre(x, decimales=0, suffixe="") -> str` : format français (espace fine insécable U+202F pour les milliers, virgule décimale), ex. `formater_nombre(42318)` donne `"42 318"`, `formater_nombre(63.2, 2, " $")` donne `"63,20 $"`.

- [ ] **Étape 1 : tests** `test_kpis_valeurs` (fixture : 4 sessions dont 1 mobile et 1 achat : `part_mobile == 0.25`, `taux_conversion == 0.25`), `test_kpis_vide`, `test_variations`, `test_kpis_periode_precedente_vide` (variations avec précédent vide : toutes `None`, aucune exception), `test_formater_duree`, `test_formater_nombre`.
- [ ] **Étape 2 :** pytest : FAIL.
- [ ] **Étape 3 :** implémenter.
- [ ] **Étape 4 :** pytest : PASS.
- [ ] **Étape 5 :** commit `feat: calcul des indicateurs clés`.

### Tâche 5 : constats automatiques (onglet Synthèse)

**Fichiers :** Créer `audience/constats.py` ; Test `tests/test_constats.py`

**Interfaces :**
- Consomme : sessions et events filtrés ; `formater_nombre` (tâche 4).
- Produit : `@dataclass class Constat: titre: str; texte: str; icone: str` et `generer_constats(events, sessions) -> list[Constat]` renvoyant 4 constats quand les données le permettent (liste vide si `sessions` vide) :
  1. Pic de trafic : jour au plus grand nombre de sessions et rapport à la moyenne journalière.
  2. Appareils : part des sessions mobiles comparée à leur part des achats.
  3. Moment fort : couple (jour de la semaine, heure) le plus actif, jour en français.
  4. Entonnoir : % des sessions avec add_to_cart qui atteignent begin_checkout puis purchase ; principale perte.
  Les valeurs de données citées restent en anglais (`mobile`, `purchase`). Aucun cadratin.

- [ ] **Étape 1 : tests** `test_constats_quatre` (fixture : 4 objets, titres non vides), `test_constats_vide` (`[]`), `test_constats_jour_en_francais` (le texte du constat 3 contient un nom de jour parmi `Lundi ... Dimanche`), `test_constats_sans_cadratin`.
- [ ] **Étape 2 à 5 :** FAIL, implémenter, PASS, commit `feat: constats automatiques de synthèse`.

### Tâche 6 : thèmes et graphiques Plotly

**Fichiers :** Créer `audience/theme.py`, `audience/graphiques.py` ; Test `tests/test_theme.py`, `tests/test_graphiques.py`

**Interfaces :**
- Produit dans `theme.py` :
  - `@dataclass(frozen=True) class Theme: nom: str ("sombre"|"clair"); fond; surface; bordure; texte; texte_secondaire; accent; accent_2; positif; negatif; couleurs_appareils: dict[str, str]; sequence: list[str]; echelle_continue: list[str]` avec les valeurs des contraintes globales. `couleurs_appareils` : sombre `{"desktop": "#8B5CF6", "mobile": "#22D3EE", "tablet": "#F472B6"}`, clair `{"desktop": "#4F46E5", "mobile": "#0EA5E9", "tablet": "#F59E0B"}`.
  - `THEMES: dict[str, Theme]` et `obtenir_theme(nom: str) -> Theme` (nom inconnu : sombre).
  - `css(theme: Theme) -> str` : feuille de style injectée par `st.markdown(..., unsafe_allow_html=True)` couvrant fond de l'app, barre latérale, en-tête, onglets (onglet actif souligné par l'accent), cartes `st.metric` (surface, bordure, rayon 14 px, ombre douce en clair, valeur en gros, delta coloré), widgets de filtre, boutons (dégradé accent en sombre, accent plein en clair), conteneurs de graphiques, police Inter (Google Fonts).
  - `appliquer_theme(fig: go.Figure, theme: Theme) -> go.Figure` : `paper_bgcolor` et `plot_bgcolor` = `theme.surface`, police couleur `theme.texte`, grille `theme.bordure`, marges et légende harmonisées, info-bulles lisibles.
- Produit dans `graphiques.py`, chaque fonction `(... , theme: Theme) -> go.Figure`, déjà passée par `appliquer_theme`, libellés en français :
  - `fig_evolution(sessions, granularite: str = "D", par_appareil: bool = False, theme)` : `px.line` du nombre de sessions par jour (`"D"`) ou semaine (`"W"`), lignes verticales annotées Black Friday 2020-11-27, Cyber Monday 2020-11-30, Noël 2020-12-25 (si dans la période).
  - `fig_heatmap_heure_jour(sessions, theme)` : grille complète 7 lignes (Lundi à Dimanche) x 24 colonnes, zéros pour les cases vides, `px.imshow` avec `echelle_continue`.
  - `fig_parts_appareils(sessions, theme)` : `px.pie(hole=0.6)`.
  - `fig_categories(events, metrique: str = "add_to_cart" | "revenue", theme)` : `px.bar` horizontal trié, top 12.
  - `fig_carte_pays(sessions, theme)` : `px.choropleth` sur `country_iso3` (lignes sans iso3 ignorées).
  - `fig_top_pays(sessions, theme)` : `px.bar` top 10.
  - `fig_engagement_boite(sessions, metrique: str = "duration_s" | "n_events" | "cart_value_usd", log: bool, theme)` : `px.box` par appareil.
  - `fig_engagement_densite(sessions, metrique, log: bool, theme)` : `px.histogram(histnorm="probability density", barmode="overlay", opacity=0.55)` par appareil.
  - `fig_entonnoir(sessions, events, theme)` : `px.funnel` des étapes add_to_cart, begin_checkout, purchase (nombre de sessions atteignant chaque étape), `color="device"`.
  - Toute fonction recevant un DataFrame vide renvoie une figure vide thémée portant l'annotation « Aucune donnée pour ces filtres ».

- [ ] **Étape 1 : tests** `test_obtenir_theme_defaut`, `test_css_contient_couleurs` (le CSS sombre contient `#0B1020`, le clair `#F5F7FB`), `test_figures_suivent_theme` (pour chaque fonction et chaque thème, `fig.layout.paper_bgcolor == theme.surface`), `test_figures_df_vide` (chaque fonction sur DataFrame vide : pas d'exception, annotation présente), `test_heatmap_grille_complete` (sessions d'un seul jour : matrice 7 x 24), `test_evolution_annotations` (période complète : 3 annotations), `test_types_traces` (pie, bar, box, funnel, choropleth attendus).
- [ ] **Étape 2 à 5 :** FAIL, implémenter, PASS, commit `feat: thèmes et graphiques interactifs`.

### Tâche 7 : application Streamlit

**Fichiers :** Créer `app.py`, `.streamlit/config.toml` ; Test `tests/test_app.py`

**Interfaces :**
- Consomme : tout `audience/`.
- Clés `st.session_state` (utilisées par les tests) : `"theme"` (`"clair"` par défaut), widgets avec `key=` : `"f_periode"`, `"f_appareils"`, `"f_pays"`, `"f_categories"`, `"granularite"`.

- [ ] **Étape 1 : tests** avec `streamlit.testing.v1.AppTest.from_file("app.py", default_timeout=60)` :
  - `test_app_demarre` : `at.run()` sans exception ; 6 onglets ; au moins 6 `metric`.
  - `test_app_theme_clair` : `at.session_state["theme"] = "clair"`, run, pas d'exception.
  - `test_app_filtres_vides` : sélection d'un pays et d'une période sans session commune, run : pas d'exception, au moins un message contenant « Aucune donnée ».
  - `test_app_bouton_export` : un `download_button` présent (vérifier via `at.get("download_button")`).
- [ ] **Étape 2 :** pytest : FAIL.
- [ ] **Étape 3 : implémenter `app.py`** (commenté en français), structure :
  1. `st.set_page_config(page_title="Audience Lab", page_icon=..., layout="wide", initial_sidebar_state="expanded")`.
  2. Chargement via `@st.cache_data` autour de `charger_donnees`.
  3. Thème : `st.session_state.setdefault("theme", "sombre")`, bascule (`st.toggle` libellé « Mode sombre ») dans l'en-tête ; injection de `css(theme)` ; graphiques affichés avec `st.plotly_chart(fig, use_container_width=True, theme=None)`.
  4. Barre latérale : logo texte en dégradé, filtres (période `st.date_input` en plage bornée aux données, multiselects appareils, pays affichés `"US · United States"`, catégories), bouton « Réinitialiser les filtres », bouton d'export CSV des sessions filtrées (`encoding="utf-8-sig"`, nom `audience_lab_sessions_filtrees.csv`), note de source.
  5. En-tête : titre, sous-titre (boutique, période, nombre de sessions filtrées).
  6. Bandeau de 6 `st.metric` avec `delta` issus de `variations` (delta absent si `None`, `delta_color="inverse"` aucun cas), libellés : Sessions, Utilisateurs, Durée moyenne, Panier moyen, Taux de conversion, Part mobile.
  7. `st.tabs(["Synthèse", "Temporalité", "Audience", "Engagement", "Conversion", "Données"])` avec le contenu de la spec (section 4.2), contrôles locaux (granularité jour / semaine, métrique d'engagement, échelle log), courte légende d'interprétation sous chaque graphique.
  8. Onglet Données : aperçu des 500 premières sessions filtrées et rappel du bouton d'export. Si `st.dataframe` ne suit pas le thème sombre/clair (vérification visuelle), passer à un tableau HTML stylé.
  9. Pied de page : auteur, module, source des données.
- [ ] **Étape 4 :** pytest : PASS.
- [ ] **Étape 5 : vérification visuelle** : `.venv/bin/streamlit run app.py --server.headless true`, ouvrir dans le navigateur, parcourir les 6 onglets dans les deux thèmes, tester un filtre vide, télécharger le CSV ; corriger tout défaut visuel (contrastes, débordements, graphiques non thémés). Capturer `docs/captures/*.png` (accueil sombre, accueil clair, temporalité, engagement, conversion) pour le README et le rapport.
- [ ] **Étape 6 :** commit `feat: application Streamlit Audience Lab`.

### Tâche 8 : publication GitHub et déploiement (point de synchronisation avec l'étudiant)

**Fichiers :** aucun nouveau, sauf corrections éventuelles.

- [ ] **Étape 1 :** demander à l'étudiant de créer le dépôt public vide `audience-lab` sur github.com (compte `Abdazz`) et d'autoriser le push.
- [ ] **Étape 2 :** `git remote add origin https://github.com/Abdazz/audience-lab.git && git push -u origin main` (identifiants de l'étudiant si demandés).
- [ ] **Étape 3 :** guider l'étudiant sur share.streamlit.io : « Create app », dépôt `Abdazz/audience-lab`, branche `main`, fichier `app.py`, version Python 3.12, URL souhaitée `audience-lab`.
- [ ] **Étape 4 : vérifier l'application en ligne** dans le navigateur : chargement sans erreur, les deux thèmes, un filtre, l'export. Noter l'URL exacte.

### Tâche 9 : README

**Fichiers :** Créer `README.md`

- [ ] **Étape 1 :** README en français : titre, badge / lien vers l'application en ligne, capture principale, contexte du projet (module, enseignant, établissement, auteur), données (source, licence, période, volumes), fonctionnalités (correspondance explicite avec chaque exigence du cahier des charges sous forme de tableau « Exigence / Où la trouver »), arborescence, exécution locale (`pip install -r requirements-dev.txt`, `streamlit run app.py`, régénération via le notebook, `pytest`), liens rapport PDF et support de soutenance.
- [ ] **Étape 2 :** `.venv/bin/pytest -q` : PASS. Commit `docs: README` et push.

### Tâche 10 : rapport d'analyse PDF

**Fichiers :** Créer `rapport/rapport_analyse.html`, `rapport/style_rapport.css`, `rapport/rapport_analyse.pdf`, `scripts/generer_pdf.sh`

**Interfaces :**
- Consomme : `rapport/figures/*.png` (tâche 2), `docs/captures/*.png` (tâche 7), chiffres du notebook et de l'application (mêmes valeurs).
- `scripts/generer_pdf.sh <entrée.html> <sortie.pdf>` : `chromium --headless --no-pdf-header-footer --print-to-pdf=<sortie> <entrée>`.

- [ ] **Étape 1 : rédiger le rapport** (A4, CSS `@page`, numéros de page, police Inter, couleurs du thème clair) : page de garde (titre, sous-titre, auteur, Master 1 IA, Université Aube-Nouvelle, enseignant, date, liens dépôt et application) ; table des matières ; 1. Contexte et objectifs ; 2. Jeu de données (source, licence, variables, critères du sujet satisfaits) ; 3. Démarche de nettoyage (chiffres avant / après pour chaque étape) ; 4. Indicateurs clés ; 5. Analyse visuelle (chaque graphique imposé, figure + interprétation chiffrée) ; 6. Le tableau de bord (captures, fonctionnalités, choix de conception) ; 7. Conclusions business ; 8. Conclusions techniques et limites (fuseau horaire, échantillon obfusqué, sessions à durée nulle) ; Annexes (exécution, arborescence).
- [ ] **Étape 2 :** générer le PDF ; contrôler `pdftotext rapport/rapport_analyse.pdf - | grep -c $'\u2014'` = 0 ; vérifier visuellement 3 pages (garde, une page d'analyse, conclusion) avec l'outil Read sur le PDF.
- [ ] **Étape 3 :** pytest PASS ; commit `docs: rapport d'analyse PDF` ; push.

### Tâche 11 : support de soutenance

**Fichiers :** Créer `soutenance/presentation.html`, `soutenance/presentation.pdf`, `soutenance/deroule_demo.md`

- [ ] **Étape 1 :** 8 à 10 diapositives HTML 16:9 (une `section.slide` par page, `@page { size: 1280px 720px }`), style du thème sombre : titre, problématique, données, démarche de nettoyage, indicateurs, 3 constats majeurs, démonstration (lien et QR facultatif), conclusion et perspectives, merci / questions.
- [ ] **Étape 2 :** `deroule_demo.md` : déroulé minute par minute de la démonstration (ordre des onglets, filtres à manipuler, bascule de thème, export CSV, phrases clés).
- [ ] **Étape 3 :** PDF via `scripts/generer_pdf.sh`, contrôle anti-cadratin, vérification visuelle ; commit `docs: support de soutenance` ; push.

### Tâche 12 : vérification finale

- [ ] **Étape 1 :** ré-exécuter le notebook de bout en bout (nbconvert) ; vérifier que les parquet n'ont pas changé de forme.
- [ ] **Étape 2 :** `.venv/bin/pytest -q` : tout PASS.
- [ ] **Étape 3 :** scan cadratin complet, PDF compris : `grep -rl $'\u2014' --exclude-dir={.venv,.git,.superpowers} .` vide, et `pdftotext` des deux PDF sans cadratin.
- [ ] **Étape 4 :** vérifier la cohérence des chiffres clés (sessions totales, CA, taux de conversion) entre notebook, application et rapport.
- [ ] **Étape 5 :** application en ligne : dernier contrôle après le push final.
- [ ] **Étape 6 :** commit et push final ; remettre à l'étudiant la liste des liens (dépôt, application, rapport PDF, support).
