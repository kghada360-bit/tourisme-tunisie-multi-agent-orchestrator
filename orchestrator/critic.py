# ============================================
# Fichier: orchestrator/critic.py
# ============================================
# Agent Critic : évalue si l'objectif de la tâche est atteint
# et si on doit continuer l'orchestration.
# ============================================

from typing import Dict

class CriticAgent:
    """
    Agent chargé de la validation.
    Il compare l'état courant (données acquises, KPIs calculés)
    avec l'objectif demandé. Il détermine aussi si l'on peut continuer
    (pas de dépassement du nombre d'étapes autorisées).
    """

    def __init__(self, run_manager=None):
        """
        Constructeur.
        :param run_manager: gestionnaire de logs (optionnel) pour tracer les étapes.
        """
        self.run_manager = run_manager

        # Règles de sécurité (allow-lists, limites) – utilisées pour le reporting
        self.safety_rules = {
            'allowed_paths': ['hotels_tunisie.csv', 'arrivees_mensuelles.csv', 'indicateurs_saisonniers.csv'],
            'allowed_endpoints': ['/api/occupancy', '/api/arrivals', '/api/revenue'],
            'max_steps': 10          # nombre maximal d'étapes dans un run
        }

    def evaluate(self, objective: Dict, state: Dict, last_result: Dict = None) -> Dict:
        """
        Évalue l'état courant par rapport à l'objectif.

        :param objective:  dictionnaire avec 'required_data' et 'kpis'
        :param state:       état courant (acquired_data, computed_kpis, completed_actions)
        :param last_result: dernier résultat d'outil (non utilisé ici, mais gardé pour cohérence)
        :return:            dictionnaire contenant goal_achieved, should_continue, issues, steps_count
        """
        # Log du début de l'évaluation (si run_manager fourni)
        if self.run_manager:
            self.run_manager.log_step(phase='critique', action='Evaluating state', status='started')

        # Extraire les données requises et déjà acquises
        required_data = set(objective.get('required_data', []))
        acquired_data = set(state.get('acquired_data', []))

        # Extraire les KPIs requis et déjà calculés
        kpi_required = set(objective.get('kpis', []))
        kpi_computed = set(state.get('computed_kpis', []))

        # L'objectif est atteint si toutes les données requises sont acquises
        # et tous les KPIs requis sont calculés.
        goal_achieved = required_data.issubset(acquired_data) and kpi_required.issubset(kpi_computed)

        # Nombre d'actions déjà effectuées
        steps_count = len(state.get('completed_actions', []))

        # On continue tant que l'objectif n'est pas atteint et qu'on n'a pas dépassé max_steps
        should_continue = not goal_achieved and steps_count < self.safety_rules['max_steps']

        # Préparer le résultat
        result = {
            'goal_achieved': goal_achieved,
            'should_continue': should_continue,
            'issues': [],                         # liste vide (peut être étendue)
            'steps_count': steps_count
        }

        # Log de fin d'évaluation
        if self.run_manager:
            self.run_manager.log_step(phase='critique', action='Evaluation complete', status='success', details=result)

        return result

    def get_safety_report(self) -> Dict:
        """
        Retourne un rapport de sécurité (allow-lists et limites).
        Utilisé par les tests et pour l'affichage GUI.
        """
        return {
            'allow_list': {
                'files': self.safety_rules['allowed_paths'],
                'endpoints': self.safety_rules['allowed_endpoints']
            },
            'limits': {
                'max_steps': self.safety_rules['max_steps']
            }
        }