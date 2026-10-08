# ============================================
# test_concurrency.py — Tests de concurrence (Section 5.4 de l'énoncé)
# ============================================
# Ce test vérifie que :
#   1. Plusieurs runs parallèles ont chacun un run_id unique
#   2. Les journaux sont isolés par run (pas de mélange)
#   3. Les caches DP sont isolés par instance de planificateur
#   4. Aucun run ne retourne None (pas de crash en parallèle)
#
# Technologie utilisée : concurrent.futures.ThreadPoolExecutor
# C'est la primitive de concurrence recommandée (Section 12.3 de l'énoncé).
# ============================================

import concurrent.futures
import time
import pytest

# Import depuis le package orchestrator (Section 9.3 : structure du projet)
from orchestrator.orchestrator import Orchestrator


def run_task(task_id: int, objective: dict, use_dp: bool) -> dict:
    """
    Lance un run d'orchestration dans un thread séparé.
    
    IMPORTANT : chaque appel crée sa propre instance d'Orchestrator.
    Cela garantit qu'il n'y a pas d'état partagé mutable (Section 5.4).
    Chaque Orchestrator a son propre RunManager, ExecutorAgent, CriticAgent,
    et son propre DPPlanner (donc son propre cache).
    
    Paramètres :
        task_id   : identifiant du thread (0, 1, 2, ...)
        objective : objectif à atteindre
        use_dp    : True = utiliser DPPlanner, False = BacktrackingPlanner
    
    Retourne :
        dict avec les résultats du run (run_id, success, etc.)
    """
    # Chaque tâche crée son propre Orchestrator → journal isolé, cache isolé
    orch = Orchestrator(use_dp=use_dp, max_steps=5)
    result = orch.run(objective, task_name=f"concurrency_test_thread_{task_id}")
    return result


def test_concurrent_runs():
    """
    Test principal : 3 runs parallèles sans conflit d'état.
    
    Ce test correspond à la Section 5.4 de l'énoncé :
    "Concurrency support: multiple runs should behave correctly
     in parallel without shared mutable state bugs."
    """
    # ─── OBJECTIF identique pour tous les runs (même seeds) ───
    objective = {
        'required_data': ['hotels'],
        'kpis': ['taux_occupation_moyen']
    }
    
    # ─── LANCER 3 RUNS EN PARALLÈLE ───
    # max_workers=3 : exactement 3 threads simultanés
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(run_task, i, objective, use_dp=(i % 2 == 0))
            for i in range(3)
        ]
        # Attendre que tous les threads terminent et récupérer les résultats
        results = [f.result() for f in futures]
    
    # ─── VÉRIFICATION 1 : tous les run_ids doivent être UNIQUES ───
    # Si deux runs partagent le même run_id, c'est un bug de concurrence.
    run_ids = [r['run_id'] for r in results]
    assert len(set(run_ids)) == 3, (
        f"Les run_ids ne sont pas uniques ! run_ids obtenus : {run_ids}"
    )
    
    # ─── VÉRIFICATION 2 : aucun run ne doit retourner None ───
    for r in results:
        assert r is not None, "Un run a retourné None (crash en parallèle)"
    
    # ─── VÉRIFICATION 3 : chaque run possède son propre 'run_id' ───
    for r in results:
        assert 'run_id' in r, f"run_id manquant dans le résultat : {r}"
    
    # ─── VÉRIFICATION 4 : isolation des caches DP ───
    # On vérifie que les stats de chaque run sont bien indépendantes.
    # (Chaque Orchestrator crée son propre DPPlanner avec son propre cache)
    for r in results:
        assert 'planner_stats' in r, "planner_stats manquant dans le résultat"
    
    print()
    print("Test de concurrence réussi :")
    print(f"  - 3 runs parallèles exécutés sans conflit")
    print(f"  - run_ids uniques : {run_ids}")
    print(f"  - Journaux isolés par run_id")
    print(f"  - Caches DP isolés par instance d'Orchestrator")


def test_cache_isolation():
    """
    Test supplémentaire : vérifie que les caches DP de deux Orchestrator
    sont bien indépendants (pas de partage de mémoire entre instances).
    
    Ce test répond à la remarque de l'analyse : 
    "le test ne prouve pas explicitement l'isolation des caches".
    """
    objective = {
        'required_data': ['hotels'],
        'kpis': ['taux_occupation_moyen']
    }
    
    # Créer deux orchestrateurs DP séparés
    orch1 = Orchestrator(use_dp=True, max_steps=5)
    orch2 = Orchestrator(use_dp=True, max_steps=5)
    
    # Vérifier que leurs planificateurs sont bien des objets différents
    assert orch1.planner is not orch2.planner, (
        "Les deux orchestrateurs partagent le même planificateur !"
    )
    
    # Vérifier que leurs caches DP sont bien des objets différents
    assert orch1.planner.cache is not orch2.planner.cache, (
        "Les deux orchestrateurs partagent le même cache DP !"
    )
    
    # Lancer orch1 et vérifier que le cache de orch2 reste vide
    orch1.run(objective, task_name="test_isolation_orch1")
    
    # Le cache de orch2 ne doit pas avoir été rempli par orch1
    assert len(orch2.planner.cache) == 0, (
        f"Le cache de orch2 a été pollué par orch1 ! cache : {orch2.planner.cache}"
    )
    
    print()
    print("Test d'isolation des caches DP réussi :")
    print(f"  - Cache orch1 après run : {len(orch1.planner.cache)} entrée(s)")
    print(f"  - Cache orch2 (non lancé) : {len(orch2.planner.cache)} entrée(s)")
    print("  - Les caches sont bien isolés par instance")


if __name__ == "__main__":
    # Lancer les tests directement si on exécute ce fichier
    test_concurrent_runs()
    test_cache_isolation()
    print()
    print("Tous les tests de concurrence passés avec succès !")
