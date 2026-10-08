# Architecture du Système Multi-Agents — Tourisme Tunisien

## Secteur déclaré

**Tourisme tunisien** — Indicateurs hôteliers par gouvernorat, arrivées mensuelles,
taux d'occupation, RevPAR, indicateurs saisonniers.

## Rôles des agents

| Agent | Fichier | Responsabilité |
|-------|---------|----------------|
| **Planner** | `tourism_planner.py` | Génère le plan (séquence d'actions). Deux variantes : `BacktrackingPlanner` (exploration pure) et `DPPlanner` (avec cache MD5). |
| **Executor** | `orchestrator/executor.py` | Valide les schémas JSON (entrée + sortie) et exécute les outils (`ReadTourismDataTool`, `MockTourismAPITool`, `ComputeKPIsTool`). |
| **Critic** | `orchestrator/critic.py` | Évalue si l'objectif est atteint et si les règles de sécurité ont été respectées. |
| **Orchestrator** | `orchestrator/orchestrator.py` | Coordonne les 3 agents dans la boucle Plan→Act→Observe→Critique. |
| **RunManager** | `orchestrator/run_manager.py` | Génère les run_ids (UUID), journalise chaque événement via structlog, persiste en JSON. |

## Diagramme de flux

```
Utilisateur / GUI
      │
      ▼
 Orchestrator.run(objective)
      │
      ├──[1. PLAN]──────────────────────────────────────────────────────────┐
      │   Planner.plan(objective)                                           │
      │   • BacktrackingPlanner : explore les branches, élagage si         │
      │     depth >= max_steps ou objectif impossible                       │
      │   • DPPlanner : vérifie le cache MD5 avant d'explorer              │
      │   → retourne une liste d'actions                                    │
      │                                                                     │
      ├──[2. ACT]───────────────────────────────────────────────────────────┤
      │   Pour chaque action du plan :                                      │
      │   ExecutorAgent.execute(action)                                     │
      │   • Validation schéma entrée (jsonschema)                          │
      │   • Exécution de l'outil (ReadTourismData / MockAPI / ComputeKPIs) │
      │   • Validation schéma sortie                                        │
      │   • Vérification allow-list (fichiers + endpoints)                 │
      │                                                                     │
      ├──[3. OBSERVE]───────────────────────────────────────────────────────┤
      │   Mise à jour de l'état :                                           │
      │   • state['acquired_data'] += target si type='read'               │
      │   • state['computed_kpis'] += target si type='compute'            │
      │                                                                     │
      └──[4. CRITIQUE]──────────────────────────────────────────────────────┘
          CriticAgent.evaluate(objective, state)
          • required_data ⊆ acquired_data ?
          • required_kpis ⊆ computed_kpis ?
          • steps_count < max_steps ?
          → goal_achieved = True/False
          → Journal persisté dans logs/run_<id>.json
```

## Outils (Tools)

| Outil | Type | Allow-list | Scénario |
|-------|------|-----------|---------|
| `ReadTourismDataTool` | read-only | `hotels_tunisie.csv`, `arrivees_mensuelles.csv`, `indicateurs_saisonniers.csv` | Scénario 1 |
| `MockTourismAPITool` | read-only | `/api/occupancy`, `/api/arrivals`, `/api/revenue` | Scénario 2 |
| `ComputeKPIsTool` | read-only | N/A (calcul interne) | Scénarios 1+2 |

Tous les outils sont **read-only** dans ce projet : aucun effet de bord (Section 4.5).

## Concurrence (Section 5.4)

Chaque `Orchestrator` crée ses propres instances de `RunManager`, `ExecutorAgent`,
`CriticAgent` et `Planner`. Il n'y a **aucun état partagé** entre les runs parallèles :
- Chaque run a son propre `run_id` et son propre journal en mémoire.
- Chaque `DPPlanner` a son propre cache (dictionnaire d'instance, non partagé).
- `test_concurrency.py` vérifie cela avec 3 threads simultanés.

## Journalisation (structlog)

Les événements sont journalisés en JSON structuré via `structlog` (Section 12.3) :
```json
{"event": "step", "run_id": "a1b2c3d4", "phase": "act", "action": "Lecture CSV",
 "status": "success", "timestamp": "2025-01-15T10:23:45.123456"}
```
