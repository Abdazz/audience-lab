# Déroulé de la démonstration : Audience Lab

Démonstration en direct d'environ 6 minutes sur l'application en ligne, entre la diapositive 8 (« Démonstration ») et la diapositive 9 (« Conclusion et perspectives ») du [support](presentation.pdf).

- Application : https://audience-lab.streamlit.app
- Thème au démarrage : **clair** (thème par défaut) ; le thème sombre s'active avec la bascule de thème de l'en-tête.
- Tous les chiffres cités ci-dessous ont été vérifiés sur les données traitées (`data/processed/`) ; ils sont identiques dans le notebook, l'application et le rapport.

## Avant la soutenance (10 minutes avant)

1. **Réveiller l'application** : ouvrir https://audience-lab.streamlit.app. Streamlit Community Cloud met l'application en veille après une période d'inactivité ; le premier chargement peut prendre quelques secondes.
2. **Préparer le plan B** dans un second onglet : `streamlit run app.py` en local (http://localhost:8501), après `source .venv/bin/activate`.
3. Navigateur en plein écran, zoom à 90 ou 100 %, notifications coupées, onglet du support PDF ouvert à la diapositive 8.
4. Vérifier que les filtres sont à leur état initial (bouton « Réinitialiser les filtres ») et que l'onglet Synthèse est affiché.

## Déroulé minute par minute

| Temps | Où | Action | Ce que l'on montre |
|---|---|---|---|
| 0:00 | Accueil, onglet **Synthèse** | Aucune action : présenter l'écran | En-tête, puces de contexte (18 101 sessions, période, aucun filtre actif), bandeau des six `st.metric`, constats rédigés automatiquement |
| 0:45 | Onglet **Temporalité** | Survoler le pic de début décembre ; passer la granularité sur **Semaine** puis revenir sur **Jour** ; activer **Détail par appareil** | Record du 8 décembre 2020 (527 sessions), repères Black Friday, Cyber Monday, Noël ; trois courbes de même forme |
| 1:45 | Onglet **Temporalité**, plus bas | Faire défiler jusqu'à la heatmap | Lignes du week-end plus claires ; case maximale : mardi à 13 h (159 sessions) |
| 2:15 | Barre latérale, **Période** | Choisir du **01/01/2021 au 31/01/2021** | Le bandeau compare janvier à **décembre**, vraie période précédente de même durée (note sous le bandeau) |
| 3:00 | Barre latérale | **Réinitialiser les filtres** ; puis onglet **Audience** ; mesure des catégories sur **Chiffre d'affaires** | Anneau des appareils (desktop 57,9 %, mobile 39,9 %, tablet 2,1 %) ; Apparel en tête ; carte des pays et top 10 |
| 3:45 | Barre latérale, **Pays** | Taper « India » et choisir **IN · India** ; puis retirer le filtre | 1 667 sessions, conversion 24,9 % : l'Inde convertit comme les États-Unis |
| 4:15 | Onglet **Engagement** | Montrer les boîtes ; changer la métrique (**Actions par session**, puis **Valeur du panier**) ; basculer l'échelle logarithmique | Les trois appareils ont des distributions presque superposées |
| 4:45 | Onglet **Conversion** ; barre latérale, **Appareils** = **mobile** | Lire l'entonnoir, puis filtrer sur mobile | 35,0 % des sessions avec add_to_cart atteignent begin_checkout, 47,1 % des begin_checkout vont jusqu'à purchase ; en mobile seul, conversion 25,2 % (7 231 sessions) |
| 5:30 | Onglet **Données** | Montrer l'aperçu, cliquer sur **Exporter en CSV** | Fichier `audience_lab_sessions_filtrees.csv` : les sessions filtrées (ici mobile), toutes colonnes, lisible par Excel |
| 6:00 | En-tête | Activer la **bascule de thème** pour passer en sombre, puis **Réinitialiser les filtres** | Le CSS et chaque graphique suivent le thème ; retour au support, diapositive 9 |

## Phrases clés

**0:00, accueil.** « Voici Audience Lab : à gauche les filtres, en haut six indicateurs toujours visibles. Sans filtre : 18 101 sessions, 14 701 utilisateurs, un panier moyen de 65,09 USD et 24,6 % de sessions avec achat. L'onglet Synthèse rédige les constats à partir des données filtrées : ils changent avec chaque filtre. »

**0:00, sur les variations.** « Sur la période complète, la période précédente n'existe pas dans les données : l'application compare donc la seconde moitié à la première et l'écrit en toutes lettres sous le bandeau. Je ne voulais pas afficher une variation trompeuse. »

**0:45, Temporalité.** « Le trafic culmine le 8 décembre avec 527 sessions, 2,7 fois la moyenne journalière. Le pic n'est pas le Black Friday : ce sont les commandes de Noël, avant les dates limites de livraison. Le détail par appareil montre trois courbes de même forme. »

**1:45, heatmap.** « Le jour compte plus que l'heure : le mardi attire 1,9 fois plus de sessions que le dimanche, et le créneau le plus actif est le mardi à 13 h. L'heure varie peu, et le fuseau des données n'est pas documenté : je recommande donc d'agir sur le jour. »

**2:15, janvier.** « Si je sélectionne janvier 2021, la période précédente, décembre, est couverte : les variations deviennent de vraies comparaisons. Janvier perd 46,7 % des sessions et la conversion recule de 4,8 points, à 16,9 %. C'est le creux d'après les fêtes. »

**3:00, Audience.** « En volume d'intérêt comme en chiffre d'affaires, Apparel domine : 54,3 % des ventes. Les États-Unis pèsent 44,2 % des sessions. »

**3:45, pays.** « Avec l'Inde seule, le bandeau se recalcule : 1 667 sessions et 24,9 % de conversion, le même niveau qu'aux États-Unis. C'est un relais de croissance. »

**4:15, Engagement.** « Durée, nombre d'actions, valeur du panier : desktop, mobile et tablet ont presque la même distribution. L'échelle logarithmique déplie la longue traîne sans supprimer de session. »

**4:45, Conversion.** « Voici le constat le plus utile : 65,0 % des sessions avec ajout au panier s'arrêtent avant le paiement, alors que près d'un paiement commencé sur deux aboutit. Et le mobile n'est pas un problème : 25,2 % de conversion, au moins autant que le desktop. »

**5:30, export.** « Le bouton d'export télécharge exactement la sélection courante, ici les sessions mobile, au format CSV. »

**6:00, thème.** « Enfin, l'application propose un thème clair par défaut et un thème sombre, adapté à la projection ; tous les graphiques suivent. Je reviens au support pour conclure. »

## Plan B si le réseau ou l'hébergement fait défaut

1. Basculer sur l'onglet local déjà lancé : `streamlit run app.py` (http://localhost:8501). Les données sont dans le dépôt : aucun téléchargement au démarrage.
2. Si l'environnement local pose aussi problème : dérouler la même histoire avec les captures du support (diapositives 6 à 8) et du rapport (section 6, figures 8 à 12), en citant les mêmes chiffres.
3. Si l'application est lente au premier chargement : commencer à commenter la diapositive 8 pendant le réveil, sans attendre en silence.

## Cinq questions probables du jury

**1. Pourquoi avoir conservé les valeurs aberrantes ?**
La règle IQR signale 3 000 sessions (16,6 %), mais elles forment une queue continue, pas des erreurs : ce sont de grosses commandes ou des onglets restés ouverts. Elles convertissent à 47,1 % et portent 42,4 % du chiffre d'affaires ; les supprimer fausserait tous les indicateurs. Elles sont donc signalées par deux colonnes booléennes et les graphiques passent en échelle logarithmique.

**2. Un taux de conversion de 24,6 %, n'est-ce pas très élevé ?**
Une session est ici une visite avec au moins un événement e-commerce : les simples visiteurs qui regardent sans ajouter au panier n'existent pas dans ce jeu. De plus, avant le 16 novembre, seuls les achats sont enregistrés, et begin_checkout n'apparaît que le 23 novembre. En partant du 23 novembre, la conversion descend à 20,9 %, mais les taux de l'entonnoir restent stables (36,3 % puis 47,1 %) : la conclusion ne change pas.

**3. Pourquoi des taux conditionnels plutôt qu'un entonnoir classique ?**
Les étapes ne sont pas imbriquées : 1 993 sessions commencent un paiement sans add_to_cart et 1 006 achètent sans begin_checkout. Diviser les effectifs d'une étape par la précédente ne donnerait pas une probabilité de passage ; on calcule donc la part des sessions d'une étape qui atteignent la suivante (35,0 %, puis 47,1 %).

**4. Pourquoi les heures sont-elles si peu marquées ?**
Le profil horaire est plat (681 à 789 sessions selon l'heure), ce qui est surprenant pour une audience à 44 % américaine. Le fuseau des horodatages n'est pas documenté et Google obfusque ce jeu public. Je lis donc l'heure comme une tendance relative et je fonde les recommandations sur le jour de la semaine.

**5. Comment garantir que les chiffres sont les mêmes partout ?**
Une seule source : le notebook produit les fichiers Parquet de `data/processed/`, que lisent l'application et les calculs du rapport. Le notebook contrôle la cohérence entre sessions et événements, et 95 tests pytest vérifient les données traitées, les indicateurs, les constats, les graphiques (filtres vides, suivi du thème) et l'application elle-même.
