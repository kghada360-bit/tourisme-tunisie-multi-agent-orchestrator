# ============================================
# Fichier: run_manager_backup.py
# ============================================
# Version plus basique du gestionnaire de runs (sans structlog).
# Conservée comme backup. Les mêmes principes :
# - run_id unique, log en mémoire, sauvegarde JSON.
# ============================================

import json
import uuid
from datetime import datetime
from typing import Dict, List
import os

class RunManager:
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        self.current_run_id = None
        self.current_journal = []
        # Crée le dossier logs s'il n'existe pas
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

    def start_new_run(self, task_name: str = None) -> str:
        """Génère un nouvel ID et initialise le journal."""
        self.current_run_id = str(uuid.uuid4())[:8]
        self.current_journal = []
        self.log_event({
            'event_type': 'run_start',
            'run_id': self.current_run_id,
            'task_name': task_name,              # optionnel
            'timestamp': datetime.now().isoformat()
        })
        return self.current_run_id

    def end_run(self, status: str = 'success', error: str = None) -> None:
        """Marque la fin du run et sauvegarde le journal."""
        self.log_event({
            'event_type': 'run_end',
            'run_id': self.current_run_id,
            'status': status,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        self._save_journal_to_file()
        # Réinitialise l'état (plus aucun run actif)
        self.current_run_id = None
        self.current_journal = []

    def log_event(self, event: Dict) -> None:
        """Ajoute un événement au journal courant."""
        if self.current_run_id is not None:
            event['run_id'] = self.current_run_id
            event['timestamp'] = datetime.now().isoformat()
            self.current_journal.append(event)

    def log_step(self, phase: str, action: str, status: str, details: Dict = None) -> None:
        """Méthode pratique pour logger une étape (Plan, Act, Critique)."""
        self.log_event({
            'event_type': 'step',
            'phase': phase,
            'action': action,
            'status': status,
            'details': details or {}
        })

    def _save_journal_to_file(self) -> None:
        """Enregistre le journal dans un fichier JSON."""
        if not self.current_journal:
            return
        filename = f"{self.logs_dir}/run_{self.current_run_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.current_journal, f, indent=2, ensure_ascii=False)

    def get_journal(self, run_id: str = None) -> List[Dict]:
        """
        Récupère le journal d'un run.
        - Si run_id est None : journal du run actif (en mémoire)
        - Sinon : lit le fichier correspondant sur disque.
        """
        if run_id is None:
            return self.current_journal
        filename = f"{self.logs_dir}/run_{run_id}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_all_run_ids(self) -> List[str]:
        """Liste tous les run_ids existants dans le dossier logs/."""
        if not os.path.exists(self.logs_dir):
            return []
        run_ids = []
        for filename in os.listdir(self.logs_dir):
            if filename.startswith('run_') and filename.endswith('.json'):
                # extrait la partie entre "run_" et ".json"
                run_id = filename[4:-5]
                run_ids.append(run_id)
        return run_ids