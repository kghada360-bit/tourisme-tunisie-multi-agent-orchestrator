# Orchestration multi-agents sécurisée pour le tourisme tunisien

Système multi-agents (Planner, Executor, Critic) qui orchestre des outils pour des
workflows liés au **tourisme en Tunisie**, avec planification par backtracking et
programmation dynamique, injection de pannes, tests de concurrence et interface graphique.

Projet réalisé en groupe de 4 étudiants — Problem Solving, ISG Tunis (2BIS), 2025-2026.

## Secteur : tourisme
[À COMPLÉTER : ex. taux d'occupation hôtelier par gouvernorat, arrivées de visiteurs,
saisonnalité, tout ce que tes données synthétiques contiennent vraiment]

## Architecture
- **Planner** : propose la prochaine action et choisit l'outil
- **Executor** : exécute les outils, valide les entrées et sorties (schémas stricts)
- **Critic** : vérifie la correction et le respect des règles de sécurité
- Boucle : Plan → Act → Observe → Critique, avec nombre d'étapes et de tentatives bornés

## Scénarios
1. **Tableau de bord opérationnel** à partir d'un fichier local synthétique
   (lecture, calcul des KPI, rapport JSON) + variante avec panne injectée
2. **Indicateurs touristiques** via API autorisée ou serveur simulé
   (GET, validation de schéma, transformation) + variante HTTP 429 / timeout

## Algorithmes
- **Backtracking** : état = [À COMPLÉTER], règles d'élagage = [À COMPLÉTER]
- **Programmation dynamique / mémoïsation** : clé de cache = [À COMPLÉTER]
- Comparaison des deux approches (même simulateur, mêmes graines et budgets)

## Sécurité et fiabilité
- Liste blanche de ressources et d'hôtes, validation stricte des schémas
- Masquage des secrets dans les logs et l'interface
- Réessais bornés, arrêt sûr en cas d'échec, journaux d'exécution par run
- Isolation entre exécutions parallèles (pas d'état partagé modifiable)

## Résultats
[À COMPLÉTER avec tes vrais chiffres]
| Métrique | Valeur |
|----------|--------|
| Taux de réussite des tâches | |
| Score de grounding des outils | |
| Récupération sur pannes injectées | |
| Gain du cache DP (taux de succès du cache / latence) | |
| Test de concurrence | |

## Interface graphique
[À COMPLÉTER : Streamlit / Gradio / FastAPI / autre]
Vues : lanceur de tâches, liste des runs, chronologie, inspecteur d'appels d'outils,
panneau de sécurité, métriques.

![Trace](screenshots/trace.png)
![Métriques](screenshots/metrics.png)

## Installation et lancement
```bash
git clone https://github.com/kghada360-bit/NOM-DU-DEPOT.git
cd NOM-DU-DEPOT
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pytest                        # lancer les tests
[COMMANDE POUR LANCER LA GUI]  # URL et port : [À COMPLÉTER]
```

## Structure
```
orchestrator/   agents et gestionnaire de runs
tools/          définitions d'outils + validation de schémas
workflows/      scénarios du tourisme
security/       listes blanches, validation, masquage
gui/            interface graphique
tests/          tests unitaires, pannes injectées, concurrence
docs/           conception, décisions, limites
data_synthetic/ données synthétiques
```

## Limites
[À COMPLÉTER : ce qui ne marche pas encore ou les simplifications faites]

## Auteure
Ghada Kaabi — ISG Tunis
Ma contribution : [À COMPLÉTER : ta part du travail dans le groupe de 4]
