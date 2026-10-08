# Projet DS2 — Orchestrateur Multi-Agents | Tourisme Tunisien

## Description

Ce projet implémente un système d'orchestration multi-agents pour analyser
les indicateurs du secteur touristique tunisien (taux d'occupation, RevPAR,
arrivées par gouvernorat, indicateurs saisonniers).

### Ce que le projet implémente

- **3 agents distincts** : Planner, ExecutorAgent, CriticAgent
- **Boucle d'orchestration** : Plan → Act → Observe → Critique avec journal persisté par run
- **Backtracking** avec élagage (depth ≥ max_steps)
- **Dynamic Programming** avec cache MD5 et comparaison empirique BT vs DP
- **Injection de pannes** : fichier manquant, HTTP 429 avec retry borné (tenacity)
- **Concurrence** : runs parallèles avec journaux et caches isolés par run_id
- **Logs structurés** via structlog (JSON par événement)
- **GUI Streamlit** : lanceur, timeline, métriques BT vs DP, injection de pannes

---

## Installation

```bash
# 1. Se placer dans le dossier du projet
cd Groupe_X_Projet_DS2

# 2. (Recommandé) Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## Lancement de la GUI

```bash
streamlit run tourism_dashboard.py
```

La GUI s'ouvre sur **http://localhost:8501**

---

## Exécution des tests

```bash
# Tests unitaires + injection de pannes (Scénarios 1 et 2)
pytest test_tourism_failures.py -v

# Tests de sécurité (allow-list, CriticAgent)
pytest test_security.py -v

# Tests de concurrence (3 runs parallèles, isolation des caches DP)
pytest test_concurrency.py -v

# Tous les tests en une seule commande
pytest test_tourism_failures.py test_security.py test_concurrency.py -v
```

---

## Comparaison empirique BT vs DP

```bash
# Lance la comparaison sur 5 tâches avec seeds fixes
# Affiche le tableau latence / branches / cache hits
# Sauvegarde le rapport dans logs/compare_bt_dp_report.json
python compare_bt_dp.py
```

---

## Replay d'un scénario démo (ligne de commande)

```bash
# Scénario 1 : KPIs hôteliers depuis CSV (avec DP)
python orchestrator_main.py

# Ou directement via Python
python - <<'EOF'
from orchestrator.orchestrator import Orchestrator

orch = Orchestrator(use_dp=True, max_steps=10)
result = orch.run(
    objective={'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen', 'revpar_moyen']},
    task_name="demo_scenario1"
)
print("Succès :", result['success'])
print("Run ID :", result['run_id'])
print("Plan   :", [a['tool'] for a in result['plan']])
EOF
```

---

## Structure du projet

```
Groupe_X_Projet_DS2/
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py       # Boucle Plan→Act→Observe→Critique
│   ├── executor.py           # Validation schéma + exécution outils
│   ├── critic.py             # Évaluation objectifs + sécurité
│   └── run_manager.py        # run_id UUID, journal JSON, structlog
├── tourism_tools.py           # ReadTourismDataTool, MockTourismAPITool (tenacity), ComputeKPIsTool
├── tourism_planner.py         # BacktrackingPlanner + DPPlanner (cache MD5)
├── tourism_dashboard.py       # GUI Streamlit principale
├── schemas.py                 # Schémas JSON pour validation I/O
├── compare_bt_dp.py           # Comparaison empirique BT vs DP (Section 4.4)
├── test_tourism_failures.py   # Tests unitaires + injection de pannes
├── test_security.py           # Tests sécurité (allow-list, Critic)
├── test_concurrency.py        # Tests concurrence + isolation caches DP
├── orchestrator_main.py       # Script démo ligne de commande
├── hotels_tunisie.csv         # Données synthétiques hôtels (10 établissements)
├── arrivees_mensuelles.csv    # Données arrivées touristiques par mois
├── indicateurs_saisonniers.csv# Indicateurs saisonniers
├── docs/
│   ├── architecture.md        # Diagramme ASCII + rôles agents
│   ├── bt_dp_design.md        # État BT, pruning, clé DP, comparaison
│   └── threat_model.md        # Risques et contrôles de sécurité
├── logs/                      # Journaux JSON par run (run_<id>.json)
├── requirements.txt
└── README.md                  # Ce fichier
```

---

## Paramètres de reproductibilité

| Paramètre | Valeur |
|-----------|--------|
| `max_steps` (tests) | 5 |
| `max_steps` (orchestrateur) | 10 |
| Clé de cache DP | MD5 sur `(acquired_sorted, computed_sorted, required_sorted, kpis_sorted)` |
| Composante aléatoire | Aucune (entièrement déterministe) |
| Données | Synthétiques, incluses dans le dépôt |
| API | Mock locale (pas de clé externe, pas d'appel réseau) |
| Python | 3.11+ |

---

## Limitations connues

- L'API est un mock local ; aucun appel réseau réel n'est effectué.
- La GUI utilise `st.rerun` (polling) pour les mises à jour ; pas de WebSocket.
- Le cache DP est en mémoire et réinitialisé à chaque instance de DPPlanner.
- Les logs sont en JSON (un fichier par run) ; une base SQLite améliorerait les requêtes.
- Le Scénario 3 (retrieval sur corpus réglementaire) n'est pas implémenté (optionnel).
