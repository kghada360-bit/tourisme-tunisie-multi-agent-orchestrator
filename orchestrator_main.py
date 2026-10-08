# ============================================
# FICHIER: orchestrator/orchestrator.py
# ============================================
# Orchestrateur Principal
# Responsable de:
# - Coordonner les 3 agents (Planner, Executor, Critic)
# - Gérer la boucle principale
# - Assurer la boucle Plan → Act → Observe → Critique

from typing import Dict, List, Optional
from orchestrator.run_manager import RunManager
from orchestrator.executor import ExecutorAgent
from orchestrator.critic import CriticAgent
from tourism_planner import BacktrackingPlanner, DPPlanner

class Orchestrator:
    """
    Orchestrateur principal.
    Il coordonne les 3 agents dans la boucle:
    Plan → Act → Observe → Critique
    """
    
    def __init__(self, use_dp: bool = True, max_steps: int = 10):
        """
        Constructeur.
        
        Paramètres:
            use_dp: Utiliser le Dynamic Programming (True) ou Backtracking simple (False)
            max_steps: Nombre maximum d'étapes
        """
        self.run_manager = RunManager()
        self.executor = ExecutorAgent(self.run_manager)
        self.critic = CriticAgent(self.run_manager)
        self.use_dp = use_dp
        self.max_steps = max_steps
        
        # Initialiser le planificateur
        tools = {
            'read_hotels': self.executor,
            'read_arrivals': self.executor,
            'compute_kpis': self.executor
        }
        
        if use_dp:
            self.planner = DPPlanner(tools, max_steps)
        else:
            self.planner = BacktrackingPlanner(tools, max_steps)
    
    def run(self, objective: Dict, task_name: str = None) -> Dict:
        """
        Exécute l'orchestration complète.
        
        Paramètres:
            objective: Objectif à atteindre
            task_name: Nom de la tâche (optionnel)
        
        Retourne:
            Dictionnaire avec les résultats
        """
        # ============================================
        # 1. Démarrer le run
        # ============================================
        run_id = self.run_manager.start_new_run(task_name)
        
        self.run_manager.log_step(
            phase='plan',
            action='Starting orchestration',
            status='started',
            details={'objective': objective}
        )
        
        # ============================================
        # 2. Phase de planification (Plan)
        # ============================================
        self.run_manager.log_step(
            phase='plan',
            action='Generating plan',
            status='started'
        )
        
        plan = self.planner.plan(objective)
        
        if plan is None:
            self.run_manager.log_step(
                phase='plan',
                action='Generating plan',
                status='failed',
                details={'error': 'No plan found'}
            )
            self.run_manager.end_run(status='failed', error='Aucun plan trouvé')
            return {'success': False, 'error': 'Aucun plan trouvé', 'run_id': run_id}
        
        self.run_manager.log_step(
            phase='plan',
            action='Generating plan',
            status='success',
            details={'plan_length': len(plan)}
        )
        
        # ============================================
        # 3. Phase d'exécution (Act)
        # ============================================
        state = {
            'acquired_data': [],
            'completed_actions': [],
            'computed_kpis': []
        }
        
        all_results = []
        planner_stats = self.planner.get_stats()
        
        for i, action in enumerate(plan):
            self.run_manager.log_step(
                phase='act',
                action=f"Executing step {i+1}/{len(plan)}",
                status='started',
                details={'action': action}
            )
            
            # Exécuter l'action
            result = self._execute_action(action, state)
            all_results.append(result)
            
            # Mettre à jour l'état
            if result.get('status') == 'success':
                self._update_state(state, action, result)
            
            self.run_manager.log_step(
                phase='act',
                action=f"Executing step {i+1}/{len(plan)}",
                status='success' if result.get('status') == 'success' else 'failed',
                details={'result_status': result.get('status')}
            )
            
            if result.get('status') != 'success':
                break
        
        # ============================================
        # 4. Phase d'observation et critique (Observe & Critique)
        # ============================================
        self.run_manager.log_step(
            phase='critique',
            action='Final evaluation',
            status='started'
        )
        
        evaluation = self.critic.evaluate(objective, state, all_results[-1] if all_results else None)
        
        self.run_manager.log_step(
            phase='critique',
            action='Final evaluation',
            status='success',
            details=evaluation
        )
        
        # ============================================
        # 5. Finaliser le run
        # ============================================
        success = evaluation['goal_achieved']
        
        self.run_manager.end_run(
            status='success' if success else 'failed',
            error=None if success else "Objectif non atteint"
        )
        
        # ============================================
        # 6. Retourner les résultats
        # ============================================
        return {
            'success': success,
            'run_id': run_id,
            'plan': plan,
            'results': all_results,
            'state': state,
            'evaluation': evaluation,
            'planner_stats': planner_stats,
            'steps_count': len(plan)
        }
    
    def _execute_action(self, action: Dict, state: Dict) -> Dict:
        """
        Exécute une action via l'Executor.
        
        Paramètres:
            action: Action à exécuter
            state: État courant
        
        Retourne:
            Résultat de l'exécution
        """
        tool_name = action.get('tool')
        action_type = action.get('type')
        params = action.get('params', {})
        
        # Ajouter les données de l'état si nécessaire
        if action_type == 'compute' and 'data' not in params:
            # Récupérer les données de l'état
            if 'read_hotels' in [a.get('tool') for a in state.get('completed_actions', [])]:
                # Simuler la récupération des données
                import pandas as pd
                import os as _os
                _base = _os.path.dirname(_os.path.abspath(__file__))
                df = pd.read_csv(_os.path.join(_base, 'hotels_tunisie.csv'))
                params['data'] = df.to_dict(orient='records')
        
        return self.executor.execute(action)
    
    def _update_state(self, state: Dict, action: Dict, result: Dict) -> None:
        """
        Met à jour l'état après une action.
        
        Paramètres:
            state: État à mettre à jour
            action: Action exécutée
            result: Résultat de l'action
        """
        action_type = action.get('type')
        target = action.get('target')
        
        if action_type == 'read':
            if target not in state['acquired_data']:
                state['acquired_data'].append(target)
        
        elif action_type == 'compute':
            if target not in state['computed_kpis']:
                state['computed_kpis'].append(target)
        
        state['completed_actions'].append(action)
    
    def get_journal(self, run_id: str = None) -> List[Dict]:
        """
        Récupère le journal d'exécution.
        
        Paramètres:
            run_id: ID du run (optionnel)
        
        Retourne:
            Liste des événements
        """
        return self.run_manager.get_journal(run_id)
    
    def get_all_run_ids(self) -> List[str]:
        """
        Récupère tous les IDs des runs.
        
        Retourne:
            Liste des IDs
        """
        return self.run_manager.get_all_run_ids()