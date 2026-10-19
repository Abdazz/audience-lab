# Document de conception : Audience Lab, tableau de bord d'audience de la Google Merchandise Store

Date : 19 octobre 2026
Auteur : Abdoul-Aziz ZOROM (seul), Master 1 IA, Université Aube-Nouvelle
Enseignant : Dr. Zakaria Sawadogo
Module : Visualisation de Données avec Python
Échéance : ce soir (19 octobre 2026)

## 1. Intention

Projet de fin de module : « Plateforme d'Analyse et de Visualisation d'Audience Média » (sujet dans `projet.pdf`).
L'objectif déclaré de l'étudiant est la note maximale (20/20). Tout ce qui suit est arbitré à l'aune de cet objectif : couvrir **chaque exigence du cahier des charges de façon visible et vérifiable**, puis aller au-delà par la qualité de l'analyse et la finition de l'interface.

L'idée directrice : traiter le trafic d'une boutique en ligne réelle comme l'audience d'un média, et raconter une histoire en quatre questions :

1. **Quand** les visiteurs viennent-ils ? (saisonnalité Black Friday / Noël / creux de janvier, heures de pointe)
2. **D'où et sur quel appareil** ? (desktop / mobile / tablet, pays)
3. **À quel point s'engagent-ils** ? (durée de session, actions par session, valeur du panier)
4. **Où les perd-on** ? (entonnoir add_to_cart, begin_checkout, purchase)

## 2. Contraintes impératives

- **Aucun caractère cadratin (U+2014) dans aucun fichier ni aucune interface** : code, notebook, rapport, diapositives, README, ce document, sorties affichées. Vérification automatique obligatoire avant livraison (`grep -rP '\x{2014}'` ou équivalent Python sur tout le dépôt, y compris les sorties du notebook et le PDF extrait en texte). Utiliser à la place deux-points, virgules, parenthèses ou le tiret simple « - ».
- **Données sources conservées dans leur langue d'origine** (anglais) : les valeurs `desktop`, `mobile`, `add_to_cart`, `Apparel`, codes pays `US`, etc. ne sont **pas** traduites. Seuls les titres, libellés, textes d'interface et documents sont en français.
- Respect du cours : Pandas pour le nettoyage, Seaborn / Matplotlib dans le notebook, Plotly Express dans l'application, Streamlit pour le tableau de bord. Les API utilisées doivent rester reconnaissables par rapport au cours (`px.line`, `px.bar`, `px.pie`, `px.box`, `px.histogram`, `px.density_heatmap` ou `px.imshow`, `sns.boxplot`, `sns.histplot(kde=True)`, `sns.heatmap(annot=True, cmap=...)`, `st.sidebar`, `st.metric`, `st.plotly_chart`, `st.download_button`).
- Livraison : dépôt GitHub public, application en ligne (Streamlit Community Cloud), rapport PDF. Tout doit être prêt ce soir.

## 3. Données

### Source
Google Merchandise Store, sous-ensemble curé des données Google Analytics 4 (BigQuery public dataset `ga4_obfuscated_sample_ecommerce`), publié sur Kaggle (`mexwell/google-merchandise-sales-data`) et Observable (`@observablehq/google-merchandise-sales-data`). Période : 2020-11-01 au 2021-01-31.

Les trois CSV sont téléchargeables sans authentification depuis `static.observableusercontent.com` (fichiers gzip). Liens identifiés :
- events : `https://static.observableusercontent.com/files/845a898c568ec809581cc9b237a87804da7d499860cf1a7ef55e55f52f22d59d20c4a32eee620cd970c9bf33d31cf6bf30e4424c4614e3459496931d36cf4f61`
- items : `https://static.observableusercontent.com/files/d435b958c46cabed96246426f0bb4d41c3346ea595ff216ff979918e0f94cb44e738caa3a76a023d90ff959ec62f42a2755e1fc7a7299af6f7d7b4e56982566e`
- users : `https://static.observableusercontent.com/files/7526de4ae1295798cf559eba1644fb8ae72da71faad134a5ea249d88f93c6d609542460cf192751d3866b5b10ff0f1152b11dc4a9cd88e2ea769fae1db91fcde`

Les fichiers bruts sont versionnés dans le dépôt (`data/raw/`), la source est citée dans le README et le rapport.

### Profil constaté (exploration préalable)
- `events.csv` : 758 884 lignes, colonnes `user_id, ga_session_id, country, device, type, item_id, date`.
  - `device` : desktop 441 521, mobile 300 628, tablet 16 735.
  - `type` : add_to_cart 667 282, begin_checkout 76 047, purchase 15 555.
  - `country` : 109 pays, **4 555 valeurs manquantes**.
  - 18 101 sessions (clé `user_id` + `ga_session_id`), 14 701 utilisateurs, un seul appareil par session.
  - Lignes dupliquées visibles (même session, même article, même horodatage).
  - Durée de session (dernier événement moins premier) : médiane 66 s, 33 % de sessions à 0 s (un seul horodatage), queue lourde jusqu'à 16 196 s.
  - Événements par session : médiane 21, max 979.
- `items.csv` : 1 381 articles, `id, name, brand, variant, category, price_in_usd` (prix 1 à 313 USD, 21 catégories). Toutes les `item_id` des événements ont une correspondance.
- `users.csv` : 270 154 utilisateurs, `id, ltv, date` (ltv > 0 pour 4 445 utilisateurs).

Ce jeu satisfait les critères du sujet : variable temporelle (horodatage à la seconde), variables numériques (prix, durée, nombre d'événements, valeur du panier, chiffre d'affaires, ltv), variables catégorielles (device, type, country, category, brand).

## 4. Livrables

### 4.1 Notebook de pré-traitement (`notebooks/01_preparation_donnees.ipynb`)
Exécuté de bout en bout, sorties conservées, cellules Markdown en français qui expliquent chaque décision. Il produit les fichiers propres consommés par l'application.

Étape 1 (cahier des charges 2.1) :
1. Inspection : `shape`, `dtypes`, `info()`, `describe()`, `head()`, cardinalités, valeurs manquantes par colonne, doublons.
2. Valeurs manquantes : `country` manquant traité de façon explicite et justifiée (ex. modalité `(not set)` conforme à la convention GA, plutôt que suppression), décision documentée.
3. Doublons : détection et suppression des doublons exacts, avec chiffrage avant / après.
4. Valeurs aberrantes : détection par méthode IQR (et visualisation boxplot) sur la durée de session et le nombre d'événements par session ; décision documentée (ex. plafonnement ou indicateur `is_outlier` plutôt que suppression aveugle).
5. Conversion des dates en `datetime`, indexation temporelle (`set_index` / `resample`) illustrée.
6. Jointure avec `items` (prix, catégorie, marque).
7. Variables dérivées : heure, jour de la semaine (nom en français pour l'affichage, ordre lundi à dimanche), date, semaine, mois ; au niveau session : début, fin, durée, nombre d'événements, nombre d'articles distincts, valeur ajoutée au panier, chiffre d'affaires (somme des prix des événements `purchase`), indicateurs atteint begin_checkout / purchase.
8. Étape 2 (KPI) calculée et affichée dans le notebook : volume total de sessions / événements / utilisateurs, durée moyenne et valeur moyenne par session, répartition par appareil et par catégorie.
9. Visualisations Seaborn / Matplotlib (exigées par l'étape 3 « Seaborn et Plotly Express ») : évolution temporelle, barres par catégorie, boxplot et KDE de l'engagement par appareil, heatmap heure x jour annotée, matrice de corrélation des variables numériques de session.
10. Export : `data/processed/events_clean.parquet` (ou CSV compressé) et `data/processed/sessions.parquet`, légers pour le déploiement.

Le fuseau horaire des horodatages n'est pas documenté par la source : le signaler comme limite (probablement l'heure de la propriété GA, USA) dans le notebook et le rapport.

### 4.2 Application Streamlit (`app.py`)
Un seul fichier `app.py` propre et commenté (des modules utilitaires dans un dossier `src/` sont permis si cela améliore la lisibilité, mais `app.py` reste le point d'entrée). Chargement des données avec `st.cache_data`. Interface intégralement en français, valeurs de données en anglais.

**Thèmes** : deux thèmes validés par l'étudiant à partir des maquettes :
- Sombre « Nuit analytique » : fond `#0B1020`, surfaces `#141B35`, bordures `#232D55`, texte `#E6E9F5`, accents en dégradé violet `#8B5CF6` vers cyan `#22D3EE`, positif `#34D399`, négatif `#F87171`.
- Clair « professionnel » : fond `#F5F7FB`, cartes blanches à ombre douce, texte `#0F172A`, accent indigo `#4F46E5`, secondaire `#0EA5E9`, positif `#059669`, négatif `#DC2626`.
Une bascule visible (dans l'en-tête ou la barre latérale) passe de l'un à l'autre ; le CSS personnalisé ET les graphiques Plotly (template, couleurs, fond) suivent le thème. Le mécanisme exact (bascule maison avec `st.session_state` + CSS injecté + template Plotly, ou thèmes natifs Streamlit `[theme.light]` / `[theme.dark]`) est laissé au constructeur, à condition que le rendu des deux thèmes soit soigné et cohérent.

**Structure** (option « une page, des onglets » validée) :
- En-tête : nom de l'application (« Audience Lab » proposé), phrase de contexte (boutique, période), bascule de thème.
- Barre latérale (`st.sidebar`) : filtres période (plage de dates), appareil, pays, catégorie de produit ; bouton de réinitialisation ; bouton d'export CSV des données filtrées (`st.download_button`).
- Bandeau KPI toujours visible au-dessus des onglets (`st.metric`, 4 à 6 cartes stylées) : sessions, utilisateurs, durée moyenne de session, panier moyen / valeur moyenne par session, taux de conversion, part mobile. Chaque carte montre une variation (`delta`) par rapport à la période précédente de même durée (choix du concepteur).
- Onglets :
  1. **Synthèse** : 3 ou 4 constats clés rédigés en phrases, recalculés selon les filtres.
  2. **Temporalité** : courbe d'évolution du trafic (granularité jour / semaine au choix, annotations Black Friday / Noël) ; heatmap heure x jour de la semaine.
  3. **Audience** : parts par appareil (donut ou barres), pays (carte choroplèthe + top pays), catégories.
  4. **Engagement** : boxplot et densité de la durée / valeur de session selon l'appareil.
  5. **Conversion** : entonnoir add_to_cart, begin_checkout, purchase, comparé par appareil.
  6. **Données** : aperçu du tableau filtré, export CSV.
- Les quatre visualisations imposées par le sujet (évolution temporelle avec filtres, comparaison catégorielle barres / camembert, distribution boxplot / densité par appareil, heatmap heure x jour) doivent être immédiatement identifiables.
- États vides : si les filtres ne laissent aucune donnée, message clair au lieu d'une erreur.
- Mise en page agréable à l'écran d'un ordinateur portable et en projection.

### 4.3 Rapport d'analyse PDF (`rapport/rapport_analyse.pdf`)
Document synthétique en français, mise en page soignée : page de garde (titre, auteur, Master 1 IA, Université Aube-Nouvelle, enseignant Dr. Zakaria Sawadogo, date), table des matières, puis :
présentation du jeu de données et justification du choix ; démarche de nettoyage chiffrée ; KPI ; interprétation de chaque graphique ; conclusions business et techniques ; limites ; annexes (lien dépôt, lien application, instructions d'exécution). Graphiques exportés en haute qualité. Production suggérée : HTML/CSS imprimé en PDF avec Chromium headless (disponible sur la machine), méthode laissée au constructeur. Source du rapport versionnée.

### 4.4 Support de soutenance (`soutenance/`)
Court support (environ 8 à 10 diapositives) pour la présentation orale : problématique, données, démarche, démonstration (déroulé conseillé), constats, conclusion. Format au choix du constructeur (HTML exportable PDF recommandé, cohérent avec le thème de l'application). Inclure un déroulé de démonstration (quels filtres manipuler, dans quel ordre).

### 4.5 Dépôt GitHub et déploiement
- Arborescence claire : `app.py`, `requirements.txt` (versions épinglées), `.streamlit/config.toml`, `data/raw/`, `data/processed/`, `notebooks/`, `rapport/`, `soutenance/`, `README.md` (présentation, captures d'écran, lien de l'application, exécution locale), `.gitignore`.
- Déploiement sur Streamlit Community Cloud depuis le dépôt. La CLI `gh` n'est pas installée : la création du dépôt distant, le premier push et la connexion à Streamlit Cloud nécessitent une action de l'étudiant (compte GitHub et Streamlit). Toute action publique (création de dépôt, push, déploiement) se fait avec l'accord explicite de l'étudiant.
- Compte GitHub : `Abdazz`. Nom de dépôt proposé : `audience-lab` (URL attendue `https://github.com/Abdazz/audience-lab`).
- Point de synchronisation **au milieu du travail** (dès que notebook + application fonctionnent en local) : l'étudiant crée le dépôt, le constructeur pousse, l'étudiant connecte Streamlit Cloud. Le rapport, le README et les diapositives sont ensuite finalisés avec les vrais liens et vérifiés contre l'application en ligne.
- Données brutes publiées dans le dépôt avec citation de la source (choix du concepteur : jeu de démonstration diffusé publiquement par Google).

### 4.6 Priorités
L'étudiant confirme disposer du temps nécessaire : **aucun livrable n'est sacrifié**. Tous les éléments ci-dessus (y compris les deux thèmes, la carte, les diapositives) sont dans le périmètre.

## 5. Non-objectifs
- Pas de modèle prédictif ni de machine learning.
- Pas de traduction des valeurs de données.
- Pas d'authentification, de base de données, ni de données en temps réel.
- Pas de multi-pages Streamlit.

## 6. Anti-objectifs (échec même si « ça marche »)
- Un caractère cadratin présent quelque part.
- Une exigence explicite du cahier des charges absente ou difficile à repérer.
- Une interface « Streamlit par défaut », terne ou incohérente entre les deux thèmes (graphiques restés en thème clair sur fond sombre, par exemple).
- Une application en ligne qui plante, est lente au chargement ou dépend d'un téléchargement externe au démarrage.
- Des graphiques sans interprétation ; des chiffres incohérents entre notebook, application et rapport.

## 7. Laissé au constructeur
Choix précis des polices, icônes, micro-animations, libellés exacts, forme des graphiques bonus, format des fichiers intermédiaires, découpage interne du code, technique de génération du PDF et des diapositives, tant que les contraintes ci-dessus sont respectées.

## 8. Environnement constaté
Python 3.12.3, `pip` et `venv` disponibles, pandas / plotly / streamlit / seaborn **non installés** (créer un environnement virtuel `.venv`, non versionné). Git configuré (`Abdoul-Aziz ZOROM`). Chromium et Google Chrome disponibles. Pas de `gh`.
