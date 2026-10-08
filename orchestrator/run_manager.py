# ============================================
# orchestrator/run_manager.py — Gestionnaire de runs
# ============================================
# Ce fichier gère les runs d'orchestration :
#  - Crée un identifiant unique (UUID) pour chaque run
#  - Journalise chaque événement (phase, action, statut, timestamp)
#  - Persiste les journaux sur disque (format JSON)
#
# AMÉLIORATION : utilisation de structlog (Section 12.3 de l'énoncé)
# structlog produit des logs JSON structurés lisibles par les outils d'audit.
# ============================================

import json
import uuid
from datetime import datetime
from typing import Dict, List
import os

# ============================================
# IMPORT STRUCTLOG (Section 12.3)
# ============================================
# L'énoncé demande "structlog ou loguru pour des logs JSON structurés".
# On essaie structlog ; si absent (pip install structlog), fallback logging standard.
try:
    import structlog # type: ignore
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),   # timestamp ISO 8601
            structlog.processors.add_log_level,            # niveau info/error
            structlog.processors.JSONRenderer()            # sortie JSON pur
        ],
        logger_factory=structlog.PrintLoggerFactory()
    )
    _logger = structlog.get_logger()
    _USE_STRUCTLOG = True
except ImportError:
    # Fallback si structlog n'est pas installé
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    _logger = logging.getLogger(__name__)
    _USE_STRUCTLOG = False


def _log(level: str, message: str, **kwargs):
    """
    Journalise via structlog (ou logging en fallback).
    
    Paramètres :
        level   : 'info' ou 'error'
        message : message principal du log
        **kwargs: données structurées supplémentaires (run_id, phase, etc.)
    """
    if _USE_STRUCTLOG:
        if level == 'error':
            _logger.error(message, **kwargs)
        else:
            _logger.info(message, **kwargs)
    else:
        log_line = json.dumps({'message': message, **kwargs})
        if level == 'error':
            _logger.error(log_line)
        else:
            _logger.info(log_line)


class RunManager:
    """
    Gestionnaire de runs d'orchestration.
    
    Rôle :
        - Crée un run_id unique (UUID) à chaque nouveau run
        - Journalise chaque événement dans un journal en mémoire
        - Persiste le journal en JSON sur disque à la fin du run
        - Expose les journaux pour la GUI et les tests
    """

    def __init__(self, logs_dir: str = "logs"):
        """
        Constructeur.
        
        Paramètre :
            logs_dir : dossier où les journaux JSON seront sauvegardés
        """
        self.logs_dir = logs_dir
        self.current_run_id = None    # UUID du run en cours (None = aucun run actif)
        self.current_journal = []     # Journal en mémoire : liste d'événements
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

    def start_new_run(self, task_name: str = None) -> str:
        """
        Démarre un nouveau run.
        Chaque run a son propre journal → isolation garantie (Section 5.4).
        
        Paramètre :
            task_name : nom optionnel de la tâche (pour la GUI et les logs)
        
        Retourne :
            run_id : identifiant unique du run (8 caractères hex)
        """
        self.current_run_id = str(uuid.uuid4())[:8]
        self.current_journal = []
        
        # Log structuré du démarrage (traçable dans les logs du serveur)
        _log('info', 'run_start',
             run_id=self.current_run_id,
             task_name=task_name or 'unnamed')
        
        self.log_event({
            'event_type': 'run_start',
            'run_id': self.current_run_id,
            'task_name': task_name,
            'timestamp': datetime.now().isoformat()
        })
        return self.current_run_id

    def end_run(self, status: str = 'success', error: str = None) -> None:
        """
        Termine le run actif, journalise la fin et sauvegarde sur disque.
        
        Paramètres :
            status : 'success' ou 'failed'
            error  : message d'erreur si status='failed'
        """
        # Log structuré : level error si échec, info si succès
        _log('info' if status == 'success' else 'error', 'run_end',
             run_id=self.current_run_id or 'unknown',
             status=status,
             error=error or '')
        
        self.log_event({
            'event_type': 'run_end',
            'run_id': self.current_run_id,
            'status': status,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        self._save_journal_to_file()
        # Réinitialiser l'état (aucun run actif)
        self.current_run_id = None
        self.current_journal = []

    def log_event(self, event: Dict) -> None:
        """Ajoute un événement brut dans le journal en mémoire du run actif."""
        if self.current_run_id is not None:
            event['run_id'] = self.current_run_id
            event['timestamp'] = datetime.now().isoformat()
            self.current_journal.append(event)

    def log_step(self, phase: str, action: str, status: str, details: Dict = None) -> None:
        """
        Journalise une étape de la boucle Plan→Act→Observe→Critique.
        
        Paramètres :
            phase   : 'plan', 'act', 'observe' ou 'critique'
            action  : description courte de l'action
            status  : 'started', 'success' ou 'failed'
            details : données supplémentaires (optionnel)
        """
        # Log structuré via structlog (chaque étape est traçable par run_id)
        _log('info' if status != 'failed' else 'error', 'step',
             run_id=self.current_run_id or 'unknown',
             phase=phase,
             action=action,
             status=status)
        
        self.log_event({
            'event_type': 'step',
            'phase': phase,
            'action': action,
            'status': status,
            'details': details or {}
        })

    def _save_journal_to_file(self) -> None:
        """
        Persiste le journal du run actif dans un fichier JSON.
        Chaque run a son propre fichier : run_<run_id>.json
        """
        if not self.current_journal:
            return
        filename = f"{self.logs_dir}/run_{self.current_run_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.current_journal, f, indent=2, ensure_ascii=False)
        
        # Log structuré de la sauvegarde (pour audit)
        _log('info', 'journal_saved',
             run_id=self.current_run_id,
             filename=filename,
             events_count=len(self.current_journal))

    def get_journal(self, run_id: str = None) -> List[Dict]:
        """
        Retourne le journal d'un run.
        
        Paramètre :
            run_id : si None, retourne le journal du run actif ;
                     sinon, lit le fichier correspondant sur disque.
        """
        if run_id is None:
            return self.current_journal
        filename = f"{self.logs_dir}/run_{run_id}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_all_run_ids(self) -> List[str]:
        """
        Liste tous les run_ids disponibles dans le dossier logs/.
        Utilisé par la GUI pour afficher l'historique des runs.
        """
        if not os.path.exists(self.logs_dir):
            return []
        run_ids = []
        for filename in os.listdir(self.logs_dir):
            if filename.startswith('run_') and filename.endswith('.json'):
                run_ids.append(filename[4:-5])  # extraire entre "run_" et ".json"
        return run_ids