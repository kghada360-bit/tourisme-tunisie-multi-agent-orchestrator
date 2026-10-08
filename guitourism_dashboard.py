# ============================================
# LIGNES 1-4: IMPORT DES BIBLIOTHEQUES
# ============================================

import streamlit as st
# Streamlit: framework pour créer des applications web interactives
# On l'importe sous le nom "st"

import pandas as pd
# Pandas: bibliothèque pour manipuler les données (DataFrames)
# Utilisé pour lire les CSV et afficher des tableaux

import plotly.express as px
# Plotly Express: bibliothèque pour créer des graphiques interactifs
# Utilisé pour afficher les graphiques en barres

from tourism_tools import ReadTourismDataTool, MockTourismAPITool
# On importe nos outils personnalisés depuis le fichier tourism_tools.py
# ReadTourismDataTool: outil pour lire les fichiers CSV
# MockTourismAPITool: outil pour simuler une API REST

# ============================================
# LIGNE 6: CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(page_title="Tourisme Tunisien", layout="wide")
# page_title: titre qui apparaît dans l'onglet du navigateur
# layout="wide": la page utilise toute la largeur de l'écran

# ============================================
# LIGNE 8: TITRE PRINCIPAL DE L'APPLICATION
# ============================================

st.title("Orchestrateur Multi-Agents - Tourisme Tunisien")
# Affiche un grand titre en haut de la page

# ============================================
# LIGNES 11-22: BARRE LATÉRALE (SIDEBAR)
# ============================================

with st.sidebar:
    # Tout ce qui est indenté s'affiche dans la barre latérale gauche
    
    st.header("Configuration")
    # Affiche un sous-titre dans la sidebar
    
    # Menu déroulant pour choisir le scénario
    scenario = st.selectbox("Scenario", ["KPIs Hoteliers (Scenario 1)", "API Mock (Scenario 2)"])
    # selectbox crée un menu déroulant
    # L'utilisateur peut choisir entre les deux scénarios
    
    # Case à cocher pour activer l'injection de panne
    inject_failure = st.checkbox("Injection de panne")
    # checkbox crée une case à cocher
    # Si cochée, inject_failure = True
    
    # Bouton principal pour lancer l'orchestration
    if st.button("LANCER", type="primary"):
        # button crée un bouton cliquable
        # type="primary" donne une couleur bleue au bouton
        # Ce code s'exécute quand l'utilisateur clique
        
        # Stockage des paramètres dans la session (persistants entre les rechargements)
        st.session_state['run'] = True          # Indique qu'une tâche est en cours
        st.session_state['scenario'] = scenario # Stocke le scénario choisi
        st.session_state['inject_failure'] = inject_failure # Stocke si panne activée

# ============================================
# LIGNES 25-97: EXÉCUTION DE LA TÂCHE
# ============================================

if st.session_state.get('run', False):
    # .get('run', False) signifie:
    # - Si la clé 'run' existe, prendre sa valeur
    # - Sinon, utiliser False (par défaut)
    # Ce bloc s'exécute seulement si 'run' est True (après avoir cliqué sur LANCER)
    
    with st.spinner("Execution..."):
        # spinner: roue de chargement qui tourne
        # Le message "Execution..." s'affiche pendant l'exécution
        
        # ============================================
        # SCÉNARIO 1: KPIS HÔTELIERS
        # ============================================
        
        if "KPIs Hoteliers" in st.session_state.scenario:
            # Si l'utilisateur a choisi le Scénario 1
            
            # Création de l'outil de lecture
            tool = ReadTourismDataTool()
            
            # ============================================
            # INJECTION DE PANNE POUR SCÉNARIO 1
            # ============================================
            
            if st.session_state.inject_failure:
                # Si l'utilisateur a coché "Injection de panne"
                
                st.error("PANNE: Fichier non trouve")
                # st.error affiche un message d'erreur en rouge
                
                result = tool.execute({'filepath': 'fichier_inexistant.csv', 'indicator_type': 'hotels'})
                # On appelle l'outil avec un fichier qui n'existe PAS
                
                st.json(result)
                # st.json affiche le résultat (l'erreur) en format JSON
                
                st.stop()
                # st.stop arrête l'exécution ici (on ne continue pas)
            
            # ============================================
            # LECTURE NORMALE (SANS PANNE)
            # ============================================
            
            result = tool.execute({'filepath': 'hotels_tunisie.csv', 'indicator_type': 'hotels'})
            # Lecture du fichier CSV des hôtels
            
            if result['status'] == 'success':
                # Si la lecture a réussi
                
                st.success("Succes !")
                # Message de succès en vert
                
                # Conversion des données en DataFrame pour affichage
                df = pd.DataFrame(result['data'])
                st.dataframe(df)
                # st.dataframe affiche un tableau interactif (avec tri, recherche)
                
                # ============================================
                # CALCUL ET AFFICHAGE DES KPIs
                # ============================================
                
                # KPI 1: Taux d'occupation moyen
                if 'taux_occupation_2024' in df.columns:
                    avg_occupancy = df['taux_occupation_2024'].mean()
                    # mean() calcule la moyenne de la colonne
                    st.metric("Taux d'occupation moyen", f"{avg_occupancy:.1f}%")
                    # st.metric affiche une carte avec une valeur
                    # f"{avg_occupancy:.1f}%" formate le nombre avec 1 décimale + symbole %
                
                # KPI 2: RevPAR moyen (Revenu par chambre disponible)
                if 'revenu_chambre_journalier' in df.columns:
                    avg_revpar = df['revenu_chambre_journalier'].mean()
                    st.metric("RevPAR moyen", f"{avg_revpar:.1f} TND")
                    # Affichage avec l'unité TND (Dinar Tunisien)
                
                # KPI 3: Top 3 régions (graphique)
                if 'gouvernorat' in df.columns and 'taux_occupation_2024' in df.columns:
                    top3 = df.nlargest(3, 'taux_occupation_2024')[['gouvernorat', 'taux_occupation_2024']]
                    # nlargest(3, 'colonne') prend les 3 plus grandes valeurs
                    # [['gouvernorat', 'taux_occupation_2024']] garde seulement ces 2 colonnes
                    
                    fig = px.bar(top3, x='gouvernorat', y='taux_occupation_2024', title="Top 3 regions")
                    # px.bar crée un graphique en barres
                    # x = axe horizontal (les régions)
                    # y = axe vertical (les taux d'occupation)
                    # title = titre du graphique
                    
                    st.plotly_chart(fig)
                    # Affiche le graphique interactif
        
        # ============================================
        # SCÉNARIO 2: API MOCK
        # ============================================
        
        elif "API Mock" in st.session_state.scenario:
            # Si l'utilisateur a choisi le Scénario 2
            
            # Création de l'outil API mock
            tool = MockTourismAPITool()
            
            # Appel de l'API (avec ou sans panne)
            if st.session_state.inject_failure:
                st.warning("PANNE: Simulation API rate limit")
                # st.warning affiche un message d'avertissement jaune
                result = tool.execute({'endpoint': '/api/occupancy', 'simulate_failure': True})
                # Appel avec simulation de panne (HTTP 429)
            else:
                result = tool.execute({'endpoint': '/api/occupancy', 'simulate_failure': False})
                # Appel normal sans panne
            
            if result['status'] == 'success':
                # Si l'appel API a réussi
                
                st.success("API appelee avec succes")
                # Message de succès
                
                # Affichage du taux d'occupation national
                st.metric("Taux d'occupation national", f"{result['data']['national_avg_occupancy']}%")
                
                # Conversion des données par région en DataFrame
                df_regions = pd.DataFrame(result['data']['by_region'].items(), columns=['Region', 'Taux (%)'])
                # .items() convertit le dictionnaire en paires (key, value)
                
                st.dataframe(df_regions)
                # Affichage du tableau des régions
                
                # Graphique des taux par région
                fig = px.bar(df_regions, x='Region', y='Taux (%)', title="Taux par region")
                st.plotly_chart(fig)
                # Affichage du graphique en barres
            else:
                # Si l'appel API a échoué
                st.error(f"Erreur: {result.get('error', 'Erreur inconnue')}")
                # Affiche le message d'erreur
    
    # ============================================
    # BOUTON POUR NOUVELLE TÂCHE
    # ============================================
    
    if st.button("Nouvelle tache"):
        st.session_state['run'] = False
        # On remet 'run' à False (plus aucune tâche en cours)
        st.rerun()
        # On recharge la page (retour à l'état initial)

# ============================================
# LIGNES 99-110: ÉTAT INITIAL (AUCUNE TÂCHE EN COURS)
# ============================================

else:
    # Ce bloc s'exécute seulement si 'run' est False (au début, avant de cliquer sur LANCER)
    
    st.info("Cliquez sur LANCER dans la barre laterale")
    # st.info affiche un message bleu d'information
    
    # Section repliable pour l'aperçu des données
    with st.expander("Donnees disponibles"):
        # st.expander crée une section qui peut être dépliée/repliée
        
        try:
            # Tentative de lecture du fichier CSV
            df = pd.read_csv('hotels_tunisie.csv')
            st.dataframe(df.head())
            # head() affiche seulement les 5 premières lignes (aperçu)
        except:
            # Si le fichier n'existe pas ou ne peut pas être lu
            st.error("Fichier hotels_tunisie.csv non trouve")