# ============================================
# LIGNES 1-3: IMPORT DES BIBLIOTHEQUES
# ============================================

import pytest
# pytest: framework de test pour Python
# Permet d'écrire des tests simples avec des fonctions commençant par "test_"
# Les résultats s'affichent avec des couleurs (vert = succès, rouge = échec)

import pandas as pd
# pandas: bibliothèque pour manipuler les données
# Utilisé dans les tests pour vérifier les calculs de moyennes et top régions

from tourism_tools import ReadTourismDataTool, MockTourismAPITool
# On importe les classes à tester depuis tourism_tools.py
# ReadTourismDataTool: outil de lecture de fichiers CSV
# MockTourismAPITool: outil de simulation d'API

# ============================================
# TEST 1: LECTURE DU FICHIER CSV
# ============================================

def test_read_hotels_file():
    """
    Test: lecture du fichier hotels_tunisie.csv
    
    Objectif: Vérifier que l'outil de lecture peut lire correctement
    le fichier CSV des hôtels et retourner les données.
    
    Ce test vérifie le bon fonctionnement de base de l'application.
    """
    
    # LIGNE 21: CRÉATION DE L'OUTIL
    tool = ReadTourismDataTool()
    # On crée une instance de l'outil de lecture
    
    # LIGNE 22: APPEL DE L'OUTIL
    result = tool.execute({
        'filepath': 'hotels_tunisie.csv',   # Chemin du fichier à lire
        'indicator_type': 'hotels'          # Type d'indicateur (hôtels)
    })
    # result contient le dictionnaire retourné par l'outil
    
    # LIGNE 27: VÉRIFICATION 1 - Le statut doit être "success"
    assert result['status'] == 'success'
    # assert est une vérification
    # Si result['status'] n'est pas égal à 'success', le test échoue
    
    # LIGNE 28: VÉRIFICATION 2 - Le nombre de lignes doit être > 0
    assert result['row_count'] > 0
    # Vérifie que le fichier n'est pas vide (au moins une ligne de données)


# ============================================
# TEST 2: FICHIER MANQUANT (INJECTION DE PANNE)
# ============================================

def test_missing_file():
    """
    Test: fichier manquant - injection de panne
    
    Objectif: Vérifier que l'outil de lecture retourne une erreur
    quand on lui demande de lire un fichier qui n'existe pas.
    
    C'est une forme d'injection de panne (failure injection)
    pour tester la résilience du système.
    """
    
    # LIGNE 46: CRÉATION DE L'OUTIL
    tool = ReadTourismDataTool()
    
    # LIGNE 47: APPEL AVEC UN FICHIER QUI N'EXISTE PAS
    result = tool.execute({
        'filepath': 'fichier_inexistant.csv',  # Ce fichier n'existe PAS
        'indicator_type': 'hotels'
    })
    
    # LIGNE 53: VÉRIFICATION 1 - Le statut doit être "failed"
    assert result['status'] == 'failed'
    # Une erreur a eu lieu → status = 'failed'
    
    # LIGNE 55-57: VÉRIFICATION 2 - Message d'erreur approprié
    # On accepte plusieurs messages d'erreur possibles
    # car selon l'ordre des vérifications, le message peut varier
    assert ("non trouve" in result['error'] or 
            "existe pas" in result['error'] or
            "non autorise" in result['error'])
    # in vérifie si une chaîne est contenue dans une autre
    # On accepte soit :
    # - "non trouve" (fichier non trouvé)
    # - "existe pas" (fichier n'existe pas)
    # - "non autorise" (fichier non autorisé par la liste blanche)


# ============================================
# TEST 3: API OCCUPANCY (SUCCÈS)
# ============================================

def test_api_occupancy():
    """
    Test: appel API occupancy
    
    Objectif: Vérifier que l'API mock retourne les données
    correctes pour l'endpoint /api/occupancy.
    
    Ce test vérifie le Scénario 2 du projet.
    """
    
    # LIGNE 71: CRÉATION DE L'OUTIL API
    tool = MockTourismAPITool()
    
    # LIGNE 72: APPEL DE L'API (sans panne)
    result = tool.execute({
        'endpoint': '/api/occupancy',      # Endpoint demandé
        'simulate_failure': False          # Pas de panne simulée
    })
    
    # LIGNE 76: VÉRIFICATION 1 - Le statut doit être "success"
    assert result['status'] == 'success'
    # L'appel API a réussi
    
    # LIGNE 77: VÉRIFICATION 2 - La valeur doit être 74.3%
    assert result['data']['national_avg_occupancy'] == 74.3
    # Vérifie que les données retournées sont correctes
    # La valeur attendue est 74.3% (d'après la documentation)


# ============================================
# TEST 4: API RATE LIMIT (INJECTION DE PANNE)
# ============================================

def test_api_rate_limit():
    """
    Test: API rate limit (HTTP 429) - injection de panne
    
    Objectif: Vérifier que l'API mock retourne une erreur
    HTTP 429 (Too Many Requests) quand on simule une panne.
    
    C'est une injection de panne pour tester la résilience/récupération.
    """
    
    # LIGNE 95: CRÉATION DE L'OUTIL API
    tool = MockTourismAPITool()
    
    # LIGNE 96: APPEL DE L'API AVEC SIMULATION DE PANNE
    result = tool.execute({
        'endpoint': '/api/occupancy',     # Endpoint demandé
        'simulate_failure': True          # Simuler une panne (HTTP 429)
    })
    
    # LIGNE 101: VÉRIFICATION 1 - Le statut doit être "rate_limited"
    assert result['status'] == 'rate_limited'
    # Le serveur a limité le nombre de requêtes
    
    # LIGNE 102: VÉRIFICATION 2 - Le message d'erreur contient "429"
    assert "429" in result['error']
    # HTTP 429 = Too Many Requests (trop de requêtes)


# ============================================
# TEST 5: CALCUL DU TAUX D'OCCUPATION MOYEN
# ============================================

def test_taux_occupation_moyen():
    """
    Test: calcul du taux d'occupation moyen
    
    Objectif: Vérifier que le calcul de la moyenne du taux d'occupation
    est correct et que le résultat est plausible (entre 50% et 100%).
    
    Ce test valide l'exactitude des KPIs calculés.
    """
    
    # LIGNE 119: LECTURE DU FICHIER CSV
    df = pd.read_csv('hotels_tunisie.csv')
    # pandas lit le fichier et crée un DataFrame
    
    # LIGNE 120: CALCUL DE LA MOYENNE
    avg = df['taux_occupation_2024'].mean()
    # .mean() calcule la moyenne arithmétique de la colonne
    
    # LIGNE 121: VÉRIFICATION - La moyenne doit être entre 50% et 100%
    assert 50 < avg < 100
    # Un taux d'occupation ne peut pas être en dessous de 50% ou au-dessus de 100%
    # Donc si la moyenne est en dehors, il y a une erreur


# ============================================
# TEST 6: TOP 3 RÉGIONS
# ============================================

def test_top_regions():
    """
    Test: top 3 regions
    
    Objectif: Vérifier que la fonction nlargest() retourne
    exactement 3 régions (pas plus, pas moins).
    
    Ce test valide l'identification des meilleures performances.
    """
    
    # LIGNE 138: LECTURE DU FICHIER CSV
    df = pd.read_csv('hotels_tunisie.csv')
    
    # LIGNE 139: EXTRACTION DES TOP 3 RÉGIONS
    top3 = df.nlargest(3, 'taux_occupation_2024')['gouvernorat'].tolist()
    # nlargest(3, 'colonne'): prend les 3 plus grandes valeurs
    # ['gouvernorat']: on ne garde que la colonne des gouvernorats
    # .tolist(): convertit en liste Python
    
    # LIGNE 140: VÉRIFICATION - Il doit y avoir exactement 3 régions
    assert len(top3) == 3
    # len() retourne la longueur de la liste
    # Si la liste n'a pas 3 éléments (ex: 2 ou 4), le test échoue