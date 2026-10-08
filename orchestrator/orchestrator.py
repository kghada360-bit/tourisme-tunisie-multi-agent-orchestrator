# ============================================
# Fichier: orchestrator/orchestrator.py
# ============================================
# Orchestrateur principal.
# Il coordonne les trois agents (Planner, Executor, Critic)
# selon la boucle Plan → Act → Observe → Critique.
# ============================================

from typing import Dict, List
from orchestrator.run_manager import RunManager
from orchestrator.executor import ExecutorAgent
from orchestrator.critic import CriticAgent
from tourism_planner import BacktrackingPlanner, DPPlanner

class Orchestrator:
    """
    Orchestrateur multi-agents.
    - Utilise un planificateur (Backtracking ou DP) pour générer un plan.
    - Exécute chaque action du plan via l'Executor.
    - À la fin, demande au Critic d'évaluer si l'objectif est atteint.
    - Journalise tout via RunManager.
    """

    def __init__(self, use_dp: bool = True, max_steps: int = 10):
        """
        :param use_dp:   si True, utilise DPPlanner (avec cache) ; sinon BacktrackingPlanner
        :param max_steps: nombre maximum d'étapes autorisées pour le planificateur
        """
        self.run_manager = RunManager()
        self.executor = ExecutorAgent(self.run_manager)
        self.critic = CriticAgent(self.run_manager)
        self.use_dp = use_dp
        self.max_steps = max_steps

        # Les outils (simplement passés aux planificateurs, qui ne les utilisent que pour la simulation)
        tools = {'read': self.executor, 'compute': self.executor}
        # Instanciation du planificateur choisi
        self.planner = DPPlanner(tools, max_steps) if use_dp else BacktrackingPlanner(tools, max_steps)

    def run(self, objective: Dict, task_name: str = None) -> Dict:
        """
        Lance l'orchestration complète.
        :param objective:  objectif à atteindre (ex: {'required_data':['hotels'], 'kpis':[...]})
        :param task_name:   nom optionnel de la tâche (pour les logs)
        :return:            dictionnaire contenant success, run_id, plan, state, evaluation
        """
        # 1. Démarrage d'un nouveau run (génère un run_id unique)
        run_id = self.run_manager.start_new_run(task_name)

        # 2. Phase de planification (Plan)
        self.run_manager.log_step(phase='plan', action='Generating plan', status='started')
        plan = self.planner.plan(objective)
        if plan is None:
            self.run_manager.end_run(status='failed', error='Aucun plan trouve')
            return {'success': False, 'error': 'Aucun plan trouve', 'run_id': run_id}

        # 3. Phase d'exécution (Act)
        state = {'acquired_data': [], 'completed_actions': [], 'computed_kpis': []}
        for action in plan:
            result = self.executor.execute(action)
            if result.get('status') == 'success':
                self._update_state(state, action, result)

        # 4. Phase critique (Critique)
        evaluation = self.critic.evaluate(objective, state)

        # 5. Fin du run
        success = evaluation['goal_achieved']
        self.run_manager.end_run(status='success' if success else 'failed')

        return {
            'success': success,
            'run_id': run_id,
            'plan': plan,
            'state': state,
            'evaluation': evaluation
        }

    def _update_state(self, state: Dict, action: Dict, result: Dict) -> None:
        """
        Met à jour l'état courant après une action réussie.
        :param state:  état à modifier (en place)
        :param action: action exécutée
        :param result: résultat de l'action (non utilisé directement ici)
        """
        action_type = action.get('type')
        target = action.get('target')
        if action_type == 'read' and target not in state['acquired_data']:
            state['acquired_data'].append(target)
        elif action_type == 'compute' and target not in state['computed_kpis']:
            state['computed_kpis'].append(target)
        state['completed_actions'].append(action)

    def get_journal(self, run_id: str = None) -> List[Dict]:
        """Retourne le journal (liste d'événements) pour un run donné."""
        return self.run_manager.get_journal(run_id)