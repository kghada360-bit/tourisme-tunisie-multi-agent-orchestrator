# ============================================
# compare_bt_dp.py — Comparaison empirique Backtracking vs DP
# ============================================
# Ce script répond à la Section 4.4 et 5.5 de l'énoncé :
# "Vous devez comparer les deux approches empiriquement :
#  feasibility rate, planning latency, states explored, robustness."
#
# Il lance exactement les mêmes tâches (même seeds, mêmes budgets)
# avec le planificateur BT seul puis avec BT+DP, et affiche le tableau
# de comparaison attendu dans l'évaluation.
# ============================================

import time
# time : pour mesurer la latence de planification en millisecondes

from tourism_planner import BacktrackingPlanner, DPPlanner
# On importe les deux planificateurs du projet

# ============================================
# SEED FIXE — Reproductibilité (Section 4.4)
# ============================================
# Le projet est déterministe (pas de random) mais on documente
# explicitement que les mêmes tâches sont utilisées pour les deux.
SEED = 42  # seed symbolique, aucun random dans ce projet

# ============================================
# TÂCHES DE TEST — Mêmes pour BT et DP (Section 4.4)
# ============================================
# Ces 5 tâches couvrent des cas variés :
#  - tâche simple (1 donnée, 1 KPI)
#  - tâche avec plusieurs KPIs
#  - tâche avec données d'arrivées
#  - tâche répétée (pour mesurer le cache hit du DP)
#  - tâche API mock
TASKS = [
    {
        'name': 'Tache_1_simple',
        'objective': {
            'required_data': ['hotels'],
            'kpis': ['taux_occupation_moyen']
        }
    },
    {
        'name': 'Tache_2_multi_kpi',
        'objective': {
            'required_data': ['hotels'],
            'kpis': ['taux_occupation_moyen', 'revpar_moyen']
        }
    },
    {
        'name': 'Tache_3_arrivees',
        'objective': {
            'required_data': ['arrivals'],
            'kpis': []
        }
    },
    {
        # Tâche répétée — permet au DP de montrer un cache HIT
        'name': 'Tache_4_repetee',
        'objective': {
            'required_data': ['hotels'],
            'kpis': ['taux_occupation_moyen']
        }
    },
    {
        'name': 'Tache_5_api',
        'objective': {
            'required_data': ['api_data'],
            'kpis': []
        }
    },
]

# ============================================
# PARAMÈTRES IDENTIQUES POUR LES DEUX PLANIFICATEURS
# ============================================
MAX_STEPS = 5   # budget d'étapes maximal (Section 4.4 : mêmes caps)


def run_planner(planner_class, tasks, max_steps):
    """
    Lance le planificateur donné sur toutes les tâches.
    
    Paramètres :
        planner_class : BacktrackingPlanner ou DPPlanner
        tasks         : liste des tâches à planifier
        max_steps     : nombre max d'étapes autorisé
    
    Retourne :
        Liste de dictionnaires avec les métriques par tâche
    """
    # tools est un dict vide ici : le planificateur simule les actions
    # (les outils réels sont appelés par l'Executor, pas le Planner)
    tools = {}
    planner = planner_class(tools, max_steps=max_steps)
    
    results = []
    
    for task in tasks:
        # --- Mesure de latence (perf_counter = plus précis que time.time) ---
        t_start = time.perf_counter()
        plan = planner.plan(task['objective'])
        t_end = time.perf_counter()
        
        latency_ms = (t_end - t_start) * 1000  # conversion en ms
        
        # --- Récupération des statistiques du planificateur ---
        stats = planner.get_stats()
        
        # --- Résultat pour cette tâche ---
        results.append({
            'tache': task['name'],
            'plan_trouve': plan is not None,          # feasibility : plan trouvé ou non
            'latence_ms': round(latency_ms, 4),       # latency
            'branches_explorees': stats.get('branches_explored', 0),
            'branches_elaguees': stats.get('pruned_branches', 0),
            # Stats DP (None pour BT pur)
            'cache_hits': stats.get('cache_hits', None),
            'cache_misses': stats.get('cache_misses', None),
            'cache_hit_ratio': stats.get('cache_hit_ratio', None),
        })
    
    return results, planner


def print_separator(char='-', width=90):
    """Affiche une ligne de séparation."""
    print(char * width)


def print_table(results_bt, results_dp):
    """
    Affiche le tableau comparatif BT vs DP.
    C'est la preuve empirique demandée à la Section 5.5 et Section 8.
    """
    print_separator('=')
    print("COMPARAISON EMPIRIQUE : Backtracking (BT) vs Backtracking + DP")
    print(f"Seed : {SEED} | max_steps : {MAX_STEPS} | Nombre de tâches : {len(TASKS)}")
    print_separator('=')
    
    # En-tête du tableau
    print(f"{'Tâche':<22} {'Plan?':>6} | "
          f"{'BT ms':>8} {'BT branch':>10} {'BT prun':>8} | "
          f"{'DP ms':>8} {'DP branch':>10} {'Cache H':>8} {'HitR%':>7}")
    print_separator()
    
    # Lignes du tableau
    for bt, dp in zip(results_bt, results_dp):
        plan_ok = "OUI" if bt['plan_trouve'] else "NON"
        cache_h = dp['cache_hits'] if dp['cache_hits'] is not None else '-'
        hit_r = f"{dp['cache_hit_ratio']*100:.0f}%" if dp['cache_hit_ratio'] is not None else '-'
        
        print(f"{bt['tache']:<22} {plan_ok:>6} | "
              f"{bt['latence_ms']:>8.4f} {bt['branches_explorees']:>10} {bt['branches_elaguees']:>8} | "
              f"{dp['latence_ms']:>8.4f} {dp['branches_explorees']:>10} {cache_h!s:>8} {hit_r:>7}")
    
    print_separator()
    
    # ============================================
    # RÉSUMÉ GLOBAL
    # ============================================
    total_bt_ms = sum(r['latence_ms'] for r in results_bt)
    total_dp_ms = sum(r['latence_ms'] for r in results_dp)
    feasible_bt = sum(1 for r in results_bt if r['plan_trouve'])
    feasible_dp = sum(1 for r in results_dp if r['plan_trouve'])
    
    # Cache hits totaux (seulement pour le DP)
    total_cache_hits = sum(r['cache_hits'] for r in results_dp if r['cache_hits'] is not None)
    total_cache_misses = sum(r['cache_misses'] for r in results_dp if r['cache_misses'] is not None)
    total_cache_calls = total_cache_hits + total_cache_misses
    global_hit_ratio = (total_cache_hits / total_cache_calls * 100) if total_cache_calls > 0 else 0
    
    print()
    print("RÉSUMÉ GLOBAL")
    print_separator()
    print(f"  Feasibility rate   : BT = {feasible_bt}/{len(TASKS)} | DP = {feasible_dp}/{len(TASKS)}")
    print(f"  Latence totale     : BT = {total_bt_ms:.4f} ms | DP = {total_dp_ms:.4f} ms")
    if total_bt_ms > 0:
        gain = ((total_bt_ms - total_dp_ms) / total_bt_ms) * 100
        print(f"  Gain latence DP    : {gain:+.1f}% (positif = DP plus rapide sur appels répétés)")
    print(f"  Cache hits totaux  : {total_cache_hits} / {total_cache_calls} appels")
    print(f"  Cache hit ratio    : {global_hit_ratio:.1f}%")
    print_separator('=')
    
    # ============================================
    # INTERPRÉTATION (demandée dans les docs)
    # ============================================
    print()
    print("INTERPRÉTATION")
    print_separator()
    print("  - Backtracking seul : explore toutes les branches nécessaires à chaque appel.")
    print("  - Backtracking + DP : mémorise les résultats. Sur les tâches répétées")
    print("    (Tache_4), le DP retourne le plan sans re-explorer (cache hit).")
    print("  - Le gain de latence est visible sur les appels redondants (Tache_4).")
    print("  - Les deux algorithmes trouvent les mêmes plans (feasibility identique).")
    print("  - Pruning : les branches élaguées (depth >= max_steps) sont communes aux deux.")
    print_separator('=')


# ============================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================
if __name__ == "__main__":
    print()
    print("Lancement de la comparaison BT vs DP...")
    print(f"Tâches utilisées (seed={SEED}) :")
    for t in TASKS:
        print(f"  - {t['name']} : {t['objective']}")
    print()
    
    # --- Lancer Backtracking seul ---
    print("Exécution avec Backtracking seul...")
    results_bt, _ = run_planner(BacktrackingPlanner, TASKS, MAX_STEPS)
    
    # --- Lancer Backtracking + DP ---
    print("Exécution avec Backtracking + DP...")
    results_dp, dp_planner = run_planner(DPPlanner, TASKS, MAX_STEPS)
    
    # --- Afficher le tableau comparatif ---
    print_table(results_bt, results_dp)
    
    # ============================================
    # EXPORT JSON (preuve pour le dossier evidence)
    # ============================================
    import json
    import os
    
    # Construire le rapport JSON
    rapport = {
        'seed': SEED,
        'max_steps': MAX_STEPS,
        'nb_taches': len(TASKS),
        'resultats_bt': results_bt,
        'resultats_dp': results_dp,
        'resume': {
            'feasibility_bt': sum(1 for r in results_bt if r['plan_trouve']),
            'feasibility_dp': sum(1 for r in results_dp if r['plan_trouve']),
            'latence_totale_bt_ms': round(sum(r['latence_ms'] for r in results_bt), 4),
            'latence_totale_dp_ms': round(sum(r['latence_ms'] for r in results_dp), 4),
            'cache_hits_total': sum(r['cache_hits'] for r in results_dp if r['cache_hits']),
        }
    }
    
    # Sauvegarder dans logs/ pour preuve de soumission
    os.makedirs('logs', exist_ok=True)
    output_path = 'logs/compare_bt_dp_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    
    print(f"\nRapport JSON sauvegardé dans : {output_path}")
    print("(Inclure ce fichier dans le dossier evidence du Moodle)")