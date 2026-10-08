# Limitations connues du projet

Ce document liste les compromis, contraintes et améliorations possibles du système d’orchestration multi-agents.  
Ces limites sont assumées dans le cadre du projet pédagogique et n’empêchent pas le bon fonctionnement des scénarios obligatoires.

---

## 1. Infrastructure technique

### a) Isolation des runs et cache DP
- Chaque run d’orchestration crée **sa propre instance** d’`Orchestrator`, donc son propre cache DP (mémoire).
- Le cache n’est **pas partagé** entre différents utilisateurs ou différentes requêtes.  
  → **Conséquence** : deux appels identiques à la même tâche mais dans des runs séparés ne bénéficient pas du cache DP.  
  → **Piste d’amélioration** : utiliser un cache partagé (Redis, memcached) avec clé de hachage incluant l’objectif et l’état.

### b) Persistance des journaux
- Les journaux sont stockés au format **JSONL** (un fichier par run). La recherche historique ou l’analyse croisée nécessite de parcourir plusieurs fichiers.
- Aucun index ni base de données n’est utilisé.  
  → **Piste d’amélioration** : remplacer par SQLite ou une base de données temps réel (InfluxDB) pour des requêtes plus rapides.

### c) Simultanéité et concurrence
- Le système supporte des runs parallèles car chaque `Orchestrator` est indépendant.  
- Cependant, **les outils `ReadTourismDataTool` et `MockTourismAPITool` ne sont pas thread‑safe** : ils lisent des fichiers CSV partagés et n’utilisent pas de verrou.  
  → En pratique, avec les petits jeux de données et le faible nombre de runs, aucun conflit n’a été observé.  
  → **Piste d’amélioration** : utiliser un mécanisme de verrouillage de fichiers ou un pool de connexions.

---

## 2. Planification et algorithmes

### a) Backtracking sans coût
- L’algorithme explore les plans jusqu’à trouver **un plan réalisable**, pas nécessairement le plan optimal en temps ou en ressources.  
  → Si plusieurs séquences d’outils mènent au même objectif, la première trouvée est retournée (ordre de priorité codé en dur).
- **Piste d’amélioration** : ajouter une fonction de coût (temps d’exécution, latence API) et une recherche A* ou branch‑and‑bound.

### b) Élagage (pruning) limité
- Seul le `max_steps` est utilisé pour couper les branches trop profondes.  
  Aucun élagage par **dominance** (si un état est déjà atteint avec plus de ressources) ou **impossibilité détectée** n’est implémenté.  
  → La complexité exponentielle peut apparaître sur des objectifs avec beaucoup de données requises.

### c) Cache DP – clé limitée
- La clé de cache se base sur les `acquired_data`, `computed_kpis`, `required_data` et `kpis` triés.  
  **Les budgets (temps, nombre de retries, etc.) ne font pas partie de la clé**.  
  → Deux runs avec des budgets différents mais le même objectif partageraient le même cache, ce qui pourrait être incorrect en théorie.  
  → Dans notre contexte (budget fixe et petit), cet effet est négligeable.

---

## 3. Outils et données

### a) Mock API
- L’API est entièrement simulée : les endpoints retournent des valeurs fixes (ex: taux national 74,3%).  
  Aucun appel réseau réel n’est effectué, même si `httpx` et `tenacity` sont configurés.  
  → Le comportement de délai (`timeout`) et de retry est simulé en mémoire.  
  → **Piste d’amélioration** : basculer vers une vraie API publique (World Bank, Open-Meteo) avec mécanisme de cache pour la reproductibilité.

### b) Données CSV figées
- Les fichiers `hotels_tunisie.csv`, `arrivees_mensuelles.csv`, etc. sont fournis statiquement.  
  Aucune mécanique de mise à jour (sourcing automatique) n’est implémentée.  
  → Le scénario 1 reproduit toujours les mêmes KPIs.

### c) Injection de panne partielle
- Les pannes injectables sont limitées à :
  - Fichier CSV manquant (`FileNotFoundError`)
  - HTTP 429 sur l’API mock
- D’autres pannes (timeout, erreur JSON, taux de change nul, division par zéro) ne sont pas testées.

---

## 4. Interface utilisateur (GUI)

### a) Mise à jour en temps réel
- La GUI utilise `st.rerun()` (polling) et non des WebSockets.  
  Pour des runs longs, l’interface peut sembler bloquée (mais le spinner tourne).

### b) Pas de pagination ni recherche avancée
- Les tableaux (journaux, historique) deviennent longs après plusieurs runs ; aucune recherche ou filtre n’est proposée.

### c) Accessibilité
- Couleurs utilisées (vert, orange, bleu) pour distinguer les agents : aucune adaptation pour daltoniens n’est incluse.

---

## 5. Documentation et reproductibilité

- Les dépendances exactes (`requirements.txt`) ne figent que les versions minimales. Une reconstruction complète peut nécessiter des ajustements (ex: `structlog` optionnel).
- Les seeds sont documentés mais le système est déterministe ; aucun générateur aléatoire n’est utilisé.

---

## Conclusion

Le projet remplit les exigences minimales de l’énoncé (scénarios, agents, backtracking+DP, tests, GUI).  
Les limitations listées ci‑dessus représentent des axes d’amélioration naturels pour le faire évoluer vers une application industrielle.  
Toutes ces limites sont **connues et assumées** dans le cadre de ce travail universitaire.