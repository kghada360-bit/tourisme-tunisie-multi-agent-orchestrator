# ============================================
# test_security.py - Tests de sécurité (allow-list, règles, CriticAgent)
# ============================================
# Ces tests vérifient que les mécanismes de sécurité (allow-list, max_steps)
# sont correctement configurés et que le CriticAgent évalue correctement l'objectif.
# ============================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.critic import CriticAgent

def test_allow_list():
    """Vérifie que la liste blanche des fichiers contient bien 'hotels_tunisie.csv'."""
    critic = CriticAgent()
    report = critic.get_safety_report()
    assert 'hotels_tunisie.csv' in report['allow_list']['files']
    print("Test allow-list: OK")

def test_safety_rules():
    """Vérifie que la règle max_steps est bien à 10 (valeur par défaut)."""
    critic = CriticAgent()
    rules = critic.safety_rules
    assert rules['max_steps'] == 10
    print("Test safety rules: OK")

def test_critic_evaluate():
    """Teste que le CriticAgent détecte correctement qu'un objectif est atteint."""
    critic = CriticAgent()
    objective = {'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen']}
    state = {'acquired_data': ['hotels'], 'computed_kpis': ['taux_occupation_moyen'], 'completed_actions': []}
    result = critic.evaluate(objective, state)
    assert result['goal_achieved'] is True
    print("Test critic evaluate: OK")

if __name__ == "__main__":
    test_allow_list()
    test_safety_rules()
    test_critic_evaluate()
    print("Tous les tests passes!")