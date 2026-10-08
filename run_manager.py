# ============================================
# run_manager.py - Gestion des journaux d'exécution (JSONL)
# ============================================
# Ce fichier gère les runs d'orchestration.
# Il crée un run_id unique, journalise les événements (plan, act, critique),
# et persiste les journaux en JSONL (une ligne par événement).
# ============================================

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class RunManager:
    """Gère la persistance des journaux d'exécution (run_id, steps, métriques)."""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)   # crée le dossier logs/ s'il n'existe pas
    
    def start_run(self, task_id: str, scenario: str, objective: Dict) -> str:
        """Crée un nouveau run et retourne son run_id (8 premiers caractères d'un UUID)."""
        run_id = str(uuid.uuid4())[:8]
        run_file = os.path.join(self.logs_dir, f"{run_id}.jsonl")
        # Métadonnées du run : première ligne du fichier
        metadata = {
            "run_id": run_id,
            "task_id": task_id,
            "scenario": scenario,
            "objective": objective,
            "start_time": datetime.now().isoformat(),
            "status": "running"
        }
        with open(run_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        return run_id
    
    def log_event(self, run_id: str, step: int, phase: str, event_type: str, data: Dict[str, Any]):
        """Ajoute un événement au journal du run (une ligne JSONL)."""
        run_file = os.path.join(self.logs_dir, f"{run_id}.jsonl")
        if not os.path.exists(run_file):
            return
        event = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "phase": phase,       # "plan", "act", "observe", "critique"
            "type": event_type,   # "plan_proposal", "tool_call", "tool_result", "critic_verdict"
            "data": data
        }
        with open(run_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    def end_run(self, run_id: str, status: str, summary: Dict = None):
        """Marque le run comme terminé (success, failed, stopped) et met à jour la première ligne."""
        run_file = os.path.join(self.logs_dir, f"{run_id}.jsonl")
        if not os.path.exists(run_file):
            return
        # Lire le fichier, modifier la première ligne (metadata)
        with open(run_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return
        metadata = json.loads(lines[0])
        metadata["status"] = status
        metadata["end_time"] = datetime.now().isoformat()
        if summary:
            metadata["summary"] = summary
        lines[0] = json.dumps(metadata, ensure_ascii=False) + "\n"
        with open(run_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
    
    def get_run_logs(self, run_id: str) -> list:
        """Retourne toutes les lignes du journal (sauf la ligne de métadonnées)."""
        run_file = os.path.join(self.logs_dir, f"{run_id}.jsonl")
        if not os.path.exists(run_file):
            return []
        with open(run_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Ignorer la première ligne (metadata)
        return [json.loads(line) for line in lines[1:]]