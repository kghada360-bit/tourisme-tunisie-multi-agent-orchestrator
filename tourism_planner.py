# ============================================
# LIGNES 1-7: IMPORT DES BIBLIOTHEQUES
# ============================================

from typing import Dict, List, Optional
# typing: pour les annotations de type
# Dict: dictionnaire, List: liste, Optional: valeur peut être None
# Cela aide à documenter quel type de données chaque fonction attend/retourne

import json
# json: pour convertir les données en format JSON
# Utilisé pour créer les clés de cache (convertir un dictionnaire en chaîne)

import hashlib
# hashlib: pour créer des empreintes numériques (hachage MD5)
# Utilisé pour générer des clés de cache uniques et de taille fixe

from datetime import datetime
# datetime: pour mesurer le temps d'exécution du planificateur
# Permet de comparer les performances entre Backtracking et DP

# ============================================
# CLASSE 1 : PLANIFICATEUR AVEC BACKTRACKING
# ============================================

class BacktrackingPlanner:
    """
    Planificateur qui explore les différentes possibilités (branches)
    et revient en arrière (backtrack) si une branche échoue.
    
    Principe: on essaie une action, si ça mène à une impasse, on revient
    en arrière et on essaie une autre action.
    
    Analogie: comme chercher son chemin dans un labyrinthe
    - On avance tout droit
    - Si c'est un cul-de-sac, on revient au dernier carrefour
    - On essaie une autre direction
    """
    
    # ============================================
    # LIGNE 33: CONSTRUCTEUR DE LA CLASSE
    # ============================================
    
    def __init__(self, tools: Dict, max_steps: int = 5):
        """
        Constructeur de la classe.
        
        Paramètres:
            tools: Dictionnaire contenant tous les outils disponibles
                   (lecture CSV, calcul KPIs, etc.)
            max_steps: Nombre maximum d'étapes autorisé (pour éviter les boucles infinies)
                      Par défaut = 5 étapes maximum
        """
        self.tools = tools
        # Stocke la liste des outils disponibles
        
        self.max_steps = max_steps
        # Limite de profondeur pour l'élagage (pruning)
        # Évite que le programme tourne indéfiniment
        
        self.branches_explored = 0
        # Compteur: nombre de branches explorées
        # Plus ce nombre est élevé, plus le planning a été complexe
        
        self.pruned_branches = 0
        # Compteur: nombre de branches coupées (élaguées)
        # L'élagage permet d'éviter d'explorer des branches inutiles
        
        self.start_time = None
        # Moment de début du planning (pour mesurer le temps)
        # None signifie que le planning n'a pas encore commencé
    
    # ============================================
    # LIGNE 56: MÉTHODE PRINCIPALE DE PLANIFICATION
    # ============================================
    
    def plan(self, objective: Dict, state: Optional[Dict] = None, depth: int = 0) -> Optional[List[Dict]]:
        """
        Méthode principale qui cherche un plan pour atteindre l'objectif.
        
        Paramètres:
            objective: Objectif à atteindre
                       Exemple: {'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen']}
            state: État courant (ce qu'on a déjà acquis comme données)
            depth: Profondeur actuelle (nombre d'actions déjà effectuées)
        
        Retourne:
            La liste des actions à exécuter, ou None si aucun plan n'est trouvé
        """
        
        # ============================================
        # LIGNE 71: ENREGISTREMENT DE L'HEURE DE DÉBUT
        # ============================================
        
        # Si c'est le premier appel, on enregistre l'heure de début
        if self.start_time is None:
            self.start_time = datetime.now()
            # datetime.now() retourne l'heure actuelle
        
        # ============================================
        # LIGNE 76: INITIALISATION DE L'ÉTAT
        # ============================================
        
        # Initialisation de l'état si c'est la première fois
        if state is None:
            state = {
                'acquired_data': [],      # Données déjà acquises (ex: 'hotels', 'arrivals')
                'completed_actions': [],  # Liste des actions déjà effectuées
                'computed_kpis': []       # KPIs déjà calculés
            }
        
        # ============================================
        # LIGNES 85-94: VÉRIFICATION SI L'OBJECTIF EST ATTEINT
        # ============================================
        
        # Extraire les données requises depuis l'objectif
        required = set(objective.get('required_data', []))
        # set() crée un ensemble (pas de doublons)
        # .get('required_data', []) retourne [] si la clé n'existe pas
        # Exemple: {'hotels', 'arrivals'}
        
        acquired = set(state['acquired_data'])
        # Ce qu'on a déjà comme données
        
        # Extraire les KPIs requis
        kpi_required = set(objective.get('kpis', []))
        # Exemple: {'taux_occupation_moyen', 'revpar_moyen'}
        
        kpi_computed = set(state['computed_kpis'])
        # Ce qu'on a déjà comme KPIs calculés
        
        # Si toutes les données sont acquises ET tous les KPIs sont calculés
        # Alors l'objectif est atteint !
        if required.issubset(acquired) and kpi_required.issubset(kpi_computed):
            # issubset() vérifie si un ensemble est contenu dans un autre
            return state['completed_actions']
            # Retourner le plan trouvé (liste des actions)
        
        # ============================================
        # LIGNES 97-103: ÉLAGAGE (PRUNING)
        # ============================================
        
        # Si on a dépassé le nombre maximum d'étapes, on coupe cette branche
        if depth >= self.max_steps:
            self.pruned_branches += 1
            # Incrémenter le compteur de branches élaguées
            return None
            # Cette branche est abandonnée (cul-de-sac)
        
        # Incrémenter le compteur de branches explorées
        self.branches_explored += 1
        
        # ============================================
        # LIGNES 106-120: CALCUL DE CE QUI MANQUE
        # ============================================
        
        # Calculer ce qui manque (données non encore acquises)
        missing_data = required - acquired
        # Opérateur - : différence entre deux ensembles
        # Exemple: si required={'hotels'}, acquired={} → missing={'hotels'}
        
        # Calculer les KPIs non encore calculés
        missing_kpis = kpi_required - kpi_computed
        
        actions = []
        # Liste vide qui va contenir les actions candidates
        
           # ============================================
        # PRIORITÉ 1 - LECTURE DES DONNÉES
        # ============================================
        
        if missing_data:
            for data_type in missing_data:
                if data_type == 'hotels':
                    actions.append({
                        'tool': 'read_hotels',
                        'type': 'read',
                        'target': data_type,
                        'params': {
                            'filepath': 'hotels_tunisie.csv',
                            'indicator_type': 'hotels'
                        }
                    })
                elif data_type == 'arrivals':
                    actions.append({
                        'tool': 'read_arrivals',
                        'type': 'read',
                        'target': data_type,
                        'params': {
                            'filepath': 'arrivees_mensuelles.csv',
                            'indicator_type': 'arrivals'
                        }
                    })
                elif data_type == 'api_data':
                    actions.append({
                        'tool': 'mock_api',
                        'type': 'read',
                        'target': data_type,
                        'params': {
                            'endpoint': '/api/occupancy',
                            'simulate_failure': False
                        }
                    })
        # ============================================
        # LIGNES 152-165: PRIORITÉ 2 - CALCUL DES KPIs
        # ============================================
        
        # On ne peut calculer les KPIs que si on a déjà les données des hôtels
        if missing_kpis and 'hotels' in acquired:
            for kpi in missing_kpis:
                actions.append({
                    'tool': 'compute_kpis',
                    # Nom de l'outil de calcul
                    'type': 'compute',
                    # Type d'action (calcul)
                    'target': kpi,
                    # KPI à calculer
                    'params': {
                        'kpi_requested': [kpi]
                        # Le KPI demandé (dans une liste)
                    }
                })
        
        # ============================================
        # LIGNES 168-180: BACKTRACKING (RETOUR SUR TRACE)
        # ============================================
        
        # Essayer chaque action candidate
        for action in actions:
            # Simuler l'effet de l'action sur l'état
            new_state = self._simulate_action(state, action)
            
            # Appel récursif pour continuer le planning
            # depth + 1 car on a fait une action de plus
            result = self.plan(objective, new_state, depth + 1)
            
            # Si on a trouvé un plan, retourner l'action actuelle + la suite
            if result is not None:
                return [action] + result
                # [action] + result concatène l'action courante avec le reste du plan
        
        # Aucune action n'a fonctionné → retourner None (échec)
        return None
    
    # ============================================
    # LIGNES 183-215: SIMULATION D'UNE ACTION
    # ============================================
    
    def _simulate_action(self, state: Dict, action: Dict) -> Dict:
        """
        Simule l'effet d'une action sur l'état.
        
        Paramètres:
            state: État avant l'action
            action: Action à simuler
        
        Retourne:
            Nouvel état après l'action
        """
        
        # Copier l'état actuel pour ne pas le modifier directement
        new_state = {
            'acquired_data': state['acquired_data'].copy(),
            # .copy() crée une copie indépendante (pas de référence)
            'completed_actions': state['completed_actions'].copy(),
            'computed_kpis': state['computed_kpis'].copy()
        }
        
        # ============================================
        # LIGNE 205: TRAITEMENT SELON LE TYPE D'ACTION
        # ============================================
        
        # Si l'action est une lecture de données
        if action['type'] == 'read':
            # Ajouter la donnée acquise si elle n'est pas déjà présente
            if action['target'] not in new_state['acquired_data']:
                new_state['acquired_data'].append(action['target'])
                # append() ajoute un élément à la fin de la liste
        
        # Si l'action est un calcul de KPI
        elif action['type'] == 'compute':
            # Ajouter le KPI calculé s'il n'est pas déjà présent
            if action['target'] not in new_state['computed_kpis']:
                new_state['computed_kpis'].append(action['target'])
        
        # Enregistrer l'action dans la liste des actions complétées
        new_state['completed_actions'].append(action)
        
        return new_state
    
    # ============================================
    # LIGNES 218-228: STATISTIQUES DU PLANIFICATEUR
    # ============================================
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques du planificateur.
        
        Utile pour comparer Backtracking vs Dynamic Programming.
        Ces statistiques sont demandées dans la Section 8 du sujet.
        """
        return {
            'branches_explored': self.branches_explored,
            # Nombre de branches explorées (plus c'est petit, mieux c'est)
            
            'pruned_branches': self.pruned_branches,
            # Nombre de branches élaguées (optimisation)
            
            'planning_time_ms': (datetime.now() - self.start_time).total_seconds() * 1000 if self.start_time else 0
            # Temps de planning en millisecondes
            # (datetime.now() - self.start_time) = différence de temps
            # .total_seconds() = conversion en secondes
            # * 1000 = conversion en millisecondes
        }


# ============================================
# CLASSE 2 : PLANIFICATEUR AVEC DYNAMIC PROGRAMMING
# ============================================

class DPPlanner(BacktrackingPlanner):
    """
    Planificateur avec mémorisation (Dynamic Programming).
    
    Héritage de BacktrackingPlanner: on reprend toutes ses méthodes,
    mais on ajoute un cache pour ne pas recalculer plusieurs fois le même état.
    
    Principe: Si on a déjà résolu le même sous-problème, on réutilise la solution.
    
    Analogie: comme apprendre par cœur les réponses d'un examen
    - La première fois, on calcule la réponse
    - Les fois suivantes, on la sort du cache (plus rapide)
    """
    
    # ============================================
    # LIGNE 245: CONSTRUCTEUR
    # ============================================
    
    def __init__(self, tools: Dict, max_steps: int = 5):
        """
        Constructeur: appelle d'abord le constructeur parent, puis ajoute le cache.
        """
        super().__init__(tools, max_steps)
        # super() appelle la classe parent (BacktrackingPlanner)
        # Cela exécute le constructeur de la classe mère
        
        self.cache = {}
        # Dictionnaire qui sert de cache (clé → résultat)
        # Exemple: {'abc123...': ['action1', 'action2']}
        
        self.cache_hits = 0
        # Nombre de fois où on a trouvé la solution dans le cache
        
        self.cache_misses = 0
        # Nombre de fois où on n'a pas trouvé dans le cache
    
    # ============================================
    # LIGNE 258: GÉNÉRATION DE LA CLÉ DE CACHE
    # ============================================
    
    def _get_cache_key(self, state: Dict, objective: Dict) -> str:
        """
        Génère une clé unique pour identifier un état.
        
        La clé est basée sur:
        - Les données déjà acquises
        - Les KPIs déjà calculés
        - Les données requises
        - Les KPIs requis
        
        On utilise MD5 pour avoir une clé de taille fixe.
        """
        
        # Construire un dictionnaire représentant l'état
        key = {
            'acquired': sorted(state['acquired_data']),
            # sorted() trie la liste pour avoir une représentation stable
            # ['Djerba', 'Sousse'] au lieu de ['Sousse', 'Djerba']
            
            'computed': sorted(state['computed_kpis']),
            # Tri des KPIs calculés
            
            'required': sorted(objective.get('required_data', [])),
            # Tri des données requises
            
            'kpis': sorted(objective.get('kpis', []))
            # Tri des KPIs requis
        }
        
        # Convertir en JSON (trié pour être stable), puis hasher avec MD5
        key_string = json.dumps(key, sort_keys=True)
        # json.dumps() convertit un dictionnaire en chaîne JSON
        # sort_keys=True garantit l'ordre des clés
        
        return hashlib.md5(key_string.encode()).hexdigest()
        # .encode() convertit la chaîne en bytes
        # hashlib.md5() crée l'empreinte MD5
        # .hexdigest() convertit en chaîne hexadécimale (ex: 'a1b2c3...')
    
    # ============================================
    # LIGNE 283: PLANIFICATION AVEC CACHE
    # ============================================
    
    def plan(self, objective: Dict, state: Optional[Dict] = None, depth: int = 0) -> Optional[List[Dict]]:
        """
        Version avec mémorisation de la méthode plan().
        
        Avant de calculer, on vérifie si le résultat est déjà dans le cache.
        C'est l'essence du Dynamic Programming.
        """
        
        # Initialiser l'état si nécessaire
        if state is None:
            state = {
                'acquired_data': [],
                'completed_actions': [],
                'computed_kpis': []
            }
        
        # Générer la clé de cache pour cet état
        cache_key = self._get_cache_key(state, objective)
        
        # ============================================
        # LIGNES 300-306: VÉRIFICATION DU CACHE
        # ============================================
        
        # Si la solution est déjà dans le cache, on la retourne directement
        if cache_key in self.cache:
            self.cache_hits += 1
            # Incrémenter le compteur de hits (succès du cache)
            return self.cache[cache_key]
            # Retourner la solution mise en cache (très rapide !)
        
        # Sinon, on doit calculer la solution
        self.cache_misses += 1
        # Incrémenter le compteur de misses (échec du cache)
        
        # ============================================
        # LIGNES 309-312: CALCUL ET STOCKAGE
        # ============================================
        
        # Appeler la méthode parent (BacktrackingPlanner) pour calculer la solution
        result = super().plan(objective, state, depth)
        
        # Stocker le résultat dans le cache pour une future utilisation
        self.cache[cache_key] = result
        # La prochaine fois qu'on aura le même état, on utilisera le cache
        
        return result
    
    # ============================================
    # LIGNES 315-332: STATISTIQUES AVEC CACHE
    # ============================================
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques du planificateur avec DP.
        
        Ajoute les statistiques du cache aux statistiques parentes.
        """
        # Récupérer les stats du parent (BacktrackingPlanner)
        stats = super().get_stats()
        
        # Ajouter les stats spécifiques au DP
        stats['cache_hits'] = self.cache_hits
        # Nombre de hits dans le cache (succès)
        
        stats['cache_misses'] = self.cache_misses
        # Nombre de misses dans le cache (échecs)
        
        # Calculer le taux de hits (pourcentage)
        total = self.cache_hits + self.cache_misses
        if total > 0:
            stats['cache_hit_ratio'] = self.cache_hits / total
            # Taux entre 0 et 1 (0 = aucun hit, 1 = tous les appels sont dans le cache)
        else:
            stats['cache_hit_ratio'] = 0
            # Pas de données
        
        return stats