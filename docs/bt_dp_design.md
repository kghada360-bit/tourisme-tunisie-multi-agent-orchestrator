# Backtracking et Dynamic Programming — Design

## 1. État de la planification (Section 4.1)

L'état de l'orchestration est un dictionnaire contenant :

```python
state = {
    'acquired_data':    [],  # données déjà lues (ex: 'hotels', 'arrivals')
    'computed_kpis':    [],  # KPIs déjà calculés (ex: 'taux_occupation_moyen')
    'completed_actions': [] # liste des actions déjà exécutées (historique)
}
```

Deux états sont **identiques** si et seulement si `acquired_data` (trié)
et `computed_kpis` (trié) sont identiques — peu importe l'ordre des actions.

## 2. BacktrackingPlanner — Exploration par branches (Section 4.2)

### Principe

Le planificateur explore les actions possibles de façon récursive.
Si une branche mène à une impasse (dépassement de budget ou objectif impossible),
il revient au nœud précédent et essaie une autre action.

### Vecteur d'état (ce qui distingue deux branches)

```
(acquired_data_sorted, computed_kpis_sorted, depth)
```

### Décision à chaque nœud

1. Si des données manquent → ajouter une action `read`
2. Sinon si des KPIs manquent → ajouter une action `compute`
3. Sinon → objectif atteint, retourner le plan

### Règles de pruning (élagage)

| Règle | Condition | Effet |
|-------|-----------|-------|
| Limite de profondeur | `depth >= max_steps` | Couper la branche |
| Objectif déjà atteint | `required ⊆ acquired AND kpis ⊆ computed` | Retourner le plan |

L'élagage garantit la terminaison en temps fini (Section 7 : boucles infinies).

### Complexité

- **Pire cas** : O(b^d) où b = facteur de branchement, d = profondeur max
- **Cas typique** (scénarios 1 et 2) : O(d) car le plan est linéaire

## 3. DPPlanner — Mémorisation (Section 4.3)

### Principe

Avant d'explorer, on vérifie si le même état a déjà été résolu.
Si oui, on retourne directement la solution mémorisée (cache hit).

### Clé de cache (soundness)

```python
key = {
    'acquired': sorted(state['acquired_data']),    # trié pour stabilité
    'computed': sorted(state['computed_kpis']),    # trié pour stabilité
    'required': sorted(objective['required_data']),
    'kpis':     sorted(objective['kpis'])
}
cache_key = hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()
```

**Pourquoi cette clé est valide :**
Deux appels mappés sur la même clé ont le même `acquired_data`, les mêmes
`computed_kpis` et les mêmes objectifs → ils mèneront exactement au même plan.
Le tri garantit que l'ordre d'insertion ne change pas la clé.

### Validité de la mémorisation

- Les outils sont **déterministes** (pas d'aléatoire, pas de side effects)
- Les données synthétiques sont **stables** (mêmes CSV entre les runs)
- → Deux appels avec la même clé produisent **toujours** le même plan

### Approximations et limitations

- Le cache est **en mémoire** et réinitialisé à chaque instance de DPPlanner
- Il n'y a pas de persistance du cache entre les runs (isolation garantie)
- Pour un espace d'état riche, un cache borné (`cachetools.LRUCache`) pourrait être utilisé

## 4. Comparaison empirique (Section 4.4)

Exécuter `python compare_bt_dp.py` pour obtenir le tableau comparatif complet.

| Métrique | BT seul | BT + DP |
|----------|---------|---------|
| Feasibility rate | identique | identique |
| Latence (1er appel) | base | ≈ identique (surcoût hachage) |
| Latence (appel répété) | identique au 1er | **très rapide** (cache hit) |
| Branches explorées | toutes | idem (1er appel), 0 (cache hit) |
| Cache hit ratio | N/A | > 0% dès le 2ème appel identique |

**Interprétation :** Le gain du DP est visible sur les appels **répétés**
(même objectif, même état). En production avec plusieurs utilisateurs
demandant les mêmes analyses, le DP réduit significativement la latence.

## 5. Idempotence et side effects (Section 4.5)

Tous les outils de ce projet sont **read-only** :
- `ReadTourismDataTool` : lit un CSV, ne le modifie pas
- `MockTourismAPITool` : retourne des données simulées, aucun appel réseau
- `ComputeKPIsTool` : calcule en mémoire, ne persiste rien

→ Pas de risque de double application sur retry (idempotence triviale).
