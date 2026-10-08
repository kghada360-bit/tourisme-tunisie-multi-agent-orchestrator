# ============================================
# Fichier: orchestrator/__init__.py
# ============================================
# Ce fichier fait du dossier "orchestrator" un package Python.
# Il expose les classes principales que d'autres modules (comme tourism_dashboard.py)
# peuvent importer directement depuis "orchestrator".

# Import des classes depuis les modules internes
from orchestrator.run_manager import RunManager      # Gestionnaire de runs et de logs
from orchestrator.executor import ExecutorAgent      # Agent d'exécution des outils
from orchestrator.critic import CriticAgent           # Agent de validation (Critic)
from orchestrator.orchestrator import Orchestrator    # Orchestrateur principal

# __all__ indique quelles sont les classes rendues publiques
# (import * depuis orchestrator ne ramènera que ces noms)
__all__ = ['RunManager', 'ExecutorAgent', 'CriticAgent', 'Orchestrator']