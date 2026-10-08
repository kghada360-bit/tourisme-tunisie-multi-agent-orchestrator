# ============================================
# Fichier: orchestrator/executor.py
# ============================================
# Agent Executor : exécute les actions planifiées (lecture CSV, calcul KPIs, appel API).
# ============================================

import time
from typing import Dict
import pandas as pd
from tourism_tools import ReadTourismDataTool, MockTourismAPITool

class ExecutorAgent:
    """
    Agent chargé de l'exécution réelle des outils.
    Il valide et exécute les actions produites par le Planner.
    Il conserve un cache interne (_data_store) des données lues pour les réutiliser
    lors des calculs de KPIs.
    """

    def __init__(self, run_manager=None):
        """
        :param run_manager: gestionnaire de logs (optionnel)
        """
        self.run_manager = run_manager
        # Stockage des données lues (par exemple, après read_hotels)
        self._data_store = {}

    def execute(self, action: Dict) -> Dict:
        """
        Exécute une action.
        :param action: dictionnaire contenant 'tool', 'type', 'params'...
        :return:       résultat de l'exécution (status, data, etc.)
        """
        tool_name = action.get('tool')
        tool_type = action.get('type')
        params = action.get('params', {})

        # Log de début d'exécution
        if self.run_manager:
            self.run_manager.log_step(phase='act', action=f"Executing {tool_name}", status='started')

        try:
            # --- Lecture (read) ---
            if tool_type == 'read':
                # Utilisation de l'outil de lecture CSV
                tool = ReadTourismDataTool()
                result = tool.execute(params)
                # Si la lecture a réussi, on stocke les données dans le cache
                if result.get('status') == 'success':
                    target = action.get('target', tool_name)
                    self._data_store[target] = result.get('data', [])

            # --- Calcul de KPIs (compute) ---
            elif tool_type == 'compute':
                # Si les données ne sont pas fournies en paramètre,
                # on les cherche dans _data_store (en priorité 'hotels')
                if 'data' not in params or not params['data']:
                    for key in ['hotels', 'arrivals']:
                        if key in self._data_store:
                            params = dict(params)          # copie pour ne pas modifier l'original
                            params['data'] = self._data_store[key]
                            break
                result = self._execute_compute(params)

            # --- Appel API (api) ---
            elif tool_type == 'api':
                tool = MockTourismAPITool()
                result = tool.execute(params)

            else:
                result = {'status': 'failed', 'error': f'Type inconnu: {tool_type}'}

            # Log de fin d'exécution (succès ou échec)
            if self.run_manager:
                self.run_manager.log_step(
                    phase='act',
                    action=f"Executed {tool_name}",
                    status='success' if result.get('status') == 'success' else 'failed'
                )
            return result

        except Exception as e:
            # Log d'erreur en cas d'exception
            if self.run_manager:
                self.run_manager.log_step(phase='act', action=f"Executed {tool_name}", status='failed')
            return {'status': 'failed', 'error': str(e)}

    def _execute_compute(self, params: Dict) -> Dict:
        """
        Sous‑méthode qui effectue le calcul des KPIs à partir d'un DataFrame.
        :param params: dictionnaire contenant 'data' (liste d'enregistrements) et 'kpi_requested'
        :return:       succès ou échec avec les KPIs calculés
        """
        data = params.get('data', [])
        kpi_requested = params.get('kpi_requested', [])

        # Vérifications de base
        if not data:
            return {'status': 'failed', 'error': 'Donnees manquantes pour le calcul'}
        if not kpi_requested:
            return {'status': 'failed', 'error': 'KPIs requis non specifies'}

        # Convertir la liste de dictionnaires en DataFrame pandas
        df = pd.DataFrame(data)
        results = {}

        # KPI : taux d'occupation moyen (colonne 'taux_occupation_2024')
        if 'taux_occupation_moyen' in kpi_requested and 'taux_occupation_2024' in df.columns:
            results['taux_occupation_moyen'] = round(float(df['taux_occupation_2024'].mean()), 1)

        # KPI : RevPAR moyen (colonne 'revenu_chambre_journalier')
        if 'revpar_moyen' in kpi_requested and 'revenu_chambre_journalier' in df.columns:
            results['revpar_moyen'] = round(float(df['revenu_chambre_journalier'].mean()), 1)

        # KPI : top 3 régions (par taux d'occupation)
        if 'top_regions' in kpi_requested and 'gouvernorat' in df.columns:
            top3 = df.nlargest(3, 'taux_occupation_2024')[['gouvernorat', 'taux_occupation_2024']]
            results['top_regions'] = top3.to_dict(orient='records')

        # Retour succès avec les KPIs
        return {'status': 'success', 'kpis': results}