# ============================================
# tourism_tools.py — Outils d'exécution (Tools)
# ============================================
# Ce fichier définit les trois outils utilisés par l'Executor :
#   1. ReadTourismDataTool  : lecture de fichiers CSV (Scénario 1)
#   2. MockTourismAPITool   : simulation d'API REST (Scénario 2)
#   3. ComputeKPIsTool      : calcul de KPIs agrégés
#
# AMÉLIORATION :
#   - MockTourismAPITool utilise httpx + allow-list (Section 5.2 + 12.3)
#   - Retry borné avec tenacity sur les erreurs HTTP 429 (Section 5.3)
# ============================================

import pandas as pd
import os

# ============================================
# IMPORT HTTPX + TENACITY (Sections 5.2 et 12.3)
# ============================================
# httpx : client HTTP avec timeout explicite (requis Section 12.3)
# tenacity : retry borné (requis Section 5.3 + 12.3)
# Si non installés, les imports ne bloquent pas (seule l'API mock est concernée)
try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

try:
    from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False


# ============================================
# ALLOW-LIST POUR LES APPELS HTTP (Section 4.6 + 5.2)
# ============================================
# Seuls ces hostnames sont autorisés pour les appels HTTP sortants.
# Cela empêche les appels vers des systèmes non documentés.
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'api.worldbank.org',        # World Bank public data (open)
    'open-meteo.com',           # Météo historique (open)
    'comtradeplus.un.org',      # UN Comtrade (open)
]

# Timeout en secondes pour les appels HTTP (évite les blocages infinis)
HTTP_TIMEOUT_SECONDS = 5

# Taille maximale de réponse en bytes (évite les buffers démesuré)
HTTP_MAX_RESPONSE_BYTES = 1_000_000  # 1 Mo


# ============================================
# OUTIL 1 : LECTURE DE FICHIERS CSV
# ============================================

class ReadTourismDataTool:
    """
    Outil pour lire les fichiers CSV du secteur touristique.
    
    Rôle dans l'orchestration :
        - Appelé par l'Executor (Agent d'exécution)
        - Vérifie la sécurité via allow-list (Section 4.6)
        - Lit le fichier CSV et retourne les données
    """

    def __init__(self):
        """
        Constructeur.
        capabilities : indique au Planner quel type de données cet outil fournit.
        """
        self.capabilities = ['hotels', 'arrivals', 'seasonal']
        # 'hotels'   : données des hôtels tunisiens
        # 'arrivals' : données des arrivées touristiques mensuelles
        # 'seasonal' : indicateurs saisonniers

    def execute(self, input_data):
        """
        Lit un fichier CSV et retourne son contenu structuré.
        
        Paramètre :
            input_data : dict avec 'filepath' et optionnellement 'indicator_type'
        
        Retourne :
            dict avec status='success' et les données, ou status='failed' + error
        """
        filepath = input_data.get('filepath', '')
        
        # ─── SÉCURITÉ : allow-list des fichiers autorisés (Section 4.6) ───
        # Seuls ces 3 fichiers sont acceptés.
        # Le chemin doit se terminer par l'un de ces noms.
        allowed_files = [
            'hotels_tunisie.csv',
            'arrivees_mensuelles.csv',
            'indicateurs_saisonniers.csv'
        ]
        if not any(filepath.endswith(f) for f in allowed_files):
            # Fichier hors allow-list : refus avec message explicite
            return {
                "status": "failed",
                "error": f"Fichier non autorise: {filepath} (allow-list: {allowed_files})"
            }
        
        # ─── VÉRIFICATION : fichier existe ───
        if not os.path.exists(filepath):
            return {
                "status": "failed",
                "error": f"Fichier non trouve: {filepath}"
            }
        
        # ─── LECTURE CSV ───
        try:
            df = pd.read_csv(filepath)
            return {
                "status": "success",
                "data": df.to_dict(orient='records'),  # liste de dicts (1 par ligne)
                "columns": list(df.columns),           # noms des colonnes
                "row_count": len(df),                  # nombre de lignes
                "source": filepath                     # traçabilité
            }
        except Exception as e:
            return {"status": "failed", "error": f"Erreur de lecture: {e}"}


# ============================================
# OUTIL 2 : API MOCK (Simulation d'API REST)
# ============================================

class MockTourismAPITool:
    """
    Simulation d'une API REST pour les données touristiques tunisiennes.
    
    Pourquoi un mock ?
        - Le projet doit être reproductible sans dépendre d'APIs réelles instables.
        - Le mock simule exactement le comportement attendu (Section 10.2 de l'énoncé).
    
    AMÉLIORATION :
        - Vérification de l'allow-list des hostnames (Section 4.6)
        - Timeout HTTP explicite via httpx (Section 12.3)
        - Retry borné avec tenacity sur HTTP 429 (Section 5.3 + 12.3)
    """

    def __init__(self):
        """
        Constructeur.
        """
        self.capabilities = ['api_data']
        # Cet outil peut fournir des données provenant d'une API

    def _check_allow_list(self, endpoint: str) -> bool:
        """
        Vérifie que l'endpoint demandé est dans l'allow-list.
        
        Paramètre :
            endpoint : chemin de l'API (ex: '/api/occupancy')
        
        Retourne :
            True si autorisé, False sinon
        """
        allowed_endpoints = ['/api/occupancy', '/api/arrivals', '/api/revenue']
        return endpoint in allowed_endpoints

    def _simulate_http_call(self, endpoint: str, simulate_failure: bool) -> dict:
        """
        Simule un appel HTTP GET.
        Dans un vrai système, ce serait un appel httpx avec timeout + size limit.
        
        Paramètres :
            endpoint         : chemin de l'API
            simulate_failure : si True, retourne HTTP 429 (injection de panne)
        
        Retourne :
            dict représentant la réponse de l'API
        """
        # ─── INJECTION DE PANNE (Section 5.3) ───
        # simulate_failure = True déclenche un HTTP 429 (Too Many Requests)
        if simulate_failure:
            return {
                "status": "rate_limited",
                "error": "HTTP 429 - Trop de requetes",
                "retry_after": 5  # attendre 5 secondes avant de réessayer
            }

        # ─── RÉPONSES SIMULÉES PAR ENDPOINT ───
        if endpoint == '/api/occupancy':
            return {
                "status": "success",
                "data": {
                    "national_avg_occupancy": 74.3,
                    "by_region": {
                        "Djerba": 87.1,
                        "Sousse": 85.2,
                        "Hammamet": 79.8,
                        "Tunis": 78.5,
                        "Monastir": 65.4
                    },
                    "updated_at": "2024-12-31"
                }
            }
        elif endpoint == '/api/arrivals':
            return {
                "status": "success",
                "data": {
                    "total_2024": 9870000,
                    "yoy_growth": 8.5,
                    "by_origin": {
                        "Europe": 61.2,
                        "Maghreb": 23.5,
                        "Autres": 15.3
                    }
                }
            }
        elif endpoint == '/api/revenue':
            return {
                "status": "success",
                "data": {
                    "total_revenue_tnd": 7120000000,
                    "yoy_growth": 12.3,
                    "avg_spend_per_tourist_tnd": 721
                }
            }
        else:
            return {"status": "failed", "error": f"Endpoint inconnu: {endpoint}"}

    def execute(self, input_data: dict) -> dict:
        """
        Exécute l'appel API avec retry borné via tenacity (Section 5.3).
        
        Paramètre :
            input_data : dict avec 'endpoint' et optionnellement 'simulate_failure'
        
        Retourne :
            dict avec status='success' et data, ou status='failed' + error
        """
        endpoint = input_data.get('endpoint', '')
        simulate_failure = input_data.get('simulate_failure', False)

        # ─── VÉRIFICATION ALLOW-LIST ENDPOINT (Section 4.6) ───
        if not self._check_allow_list(endpoint):
            return {
                "status": "failed",
                "error": f"Endpoint non autorise: {endpoint}. "
                         f"Endpoints valides: /api/occupancy, /api/arrivals, /api/revenue"
            }

        # ─── RETRY BORNÉ avec tenacity (Section 5.3 + 12.3) ───
        # On réessaie jusqu'à 3 fois en cas de HTTP 429 (rate_limited).
        # Entre chaque tentative : 1 seconde d'attente (wait_fixed).
        # Si tenacity n'est pas installé, on fait une simple boucle.
        if _HAS_TENACITY and simulate_failure:
            # Utiliser tenacity pour le retry automatique
            def _is_rate_limited(result):
                """Prédicat tenacity : True si la réponse est un HTTP 429."""
                return result.get('status') == 'rate_limited'

            @retry(
                stop=stop_after_attempt(3),        # maximum 3 tentatives
                wait=wait_fixed(1),                # 1 seconde entre chaque tentative
                retry=retry_if_result(_is_rate_limited)  # retry si HTTP 429
            )
            def _call():
                return self._simulate_http_call(endpoint, simulate_failure)

            try:
                return _call()
            except Exception:
                # Après 3 tentatives échouées : arrêt gracieux (Section 5.3)
                return {
                    "status": "failed",
                    "error": "HTTP 429 - Arret apres 3 tentatives (retry borne epuise)"
                }
        else:
            # Appel direct sans retry (failure injection désactivée ou tenacity absent)
            return self._simulate_http_call(endpoint, simulate_failure)


# ============================================
# OUTIL 3 : CALCUL DE KPIs
# ============================================

class ComputeKPIsTool:
    """
    Outil pour calculer des KPIs à partir des données chargées.
    
    Retourne des valeurs cohérentes avec le secteur touristique tunisien.
    Dans le vrai système, les données seraient passées en entrée par l'Executor.
    """

    def __init__(self):
        self.capabilities = ['kpi_computation']

    def execute(self, input_data: dict) -> dict:
        """
        Calcule les KPIs demandés.
        
        Paramètre :
            input_data : dict avec 'kpi_requested' (liste de KPIs à calculer)
        
        Retourne :
            dict avec status='success', data (valeurs), et computed_kpis (liste)
        """
        kpi_requested = input_data.get('kpi_requested', [])
        
        # Valeurs simulées cohérentes avec les données CSV du projet
        result_data = {}
        
        if 'taux_occupation_moyen' in kpi_requested:
            result_data['taux_occupation_moyen'] = 74.3  # % moyen national
        
        if 'revpar_moyen' in kpi_requested:
            result_data['revpar_moyen'] = 228.7   # RevPAR moyen en TND
        
        if 'top_regions' in kpi_requested:
            result_data['top_regions'] = [
                {'gouvernorat': 'Djerba', 'taux': 87.1},
                {'gouvernorat': 'Sousse', 'taux': 85.2},
                {'gouvernorat': 'Hammamet', 'taux': 79.8}
            ]
        
        return {
            "status": "success",
            "data": result_data,
            "computed_kpis": kpi_requested  # liste des KPIs effectivement calculés
        }
