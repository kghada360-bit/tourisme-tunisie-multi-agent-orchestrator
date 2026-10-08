# ============================================
# tourism_dashboard_backup.py - Interface Streamlit (version de base)
# ============================================
# Ce fichier est une version de sauvegarde de l'interface.
# Il affiche les résultats des scénarios 1 et 2 sans les traces des agents.
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from tourism_tools import ReadTourismDataTool, MockTourismAPITool
from tourism_planner import BacktrackingPlanner, DPPlanner
import time
import json

st.set_page_config(page_title="Tourisme Tunisien", layout="wide")

# Style minimal
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .main-title { text-align: center; padding: 1rem; background: #003366; color: white; border-radius: 10px; margin-bottom: 1rem; }
    .section-title { font-size: 1rem; font-weight: bold; color: #003366; border-left: 4px solid #e8a800; padding-left: 0.8rem; margin: 1rem 0 0.5rem 0; }
    .footer { text-align: center; margin-top: 2rem; padding: 1rem; color: #6c757d; border-top: 1px solid #e0e0e0; font-size: 0.7rem; }
    [data-testid="stSidebar"] { background: #f8f9fa; }
    .stButton > button { background: #003366; color: white; border-radius: 20px; }
    .stMetric { background: white; padding: 0.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title"><h1>Observatoire du Tourisme Tunisien</h1><p>Orchestration Multi-Agents</p></div>', unsafe_allow_html=True)

# Session
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("---")
    st.markdown("**Services**")
    scenario = st.radio("", ["Analyse des KPIs Hoteliers", "Indicateurs Nationaux (API)"], label_visibility="collapsed")
    st.markdown("---")
    test_panne = st.checkbox("Mode Test (Injection de panne)")
    use_dp = st.checkbox("Utiliser Dynamic Programming (DP)", value=True)
    st.markdown("---")
    if st.button("Executer l'analyse", use_container_width=True):
        st.session_state.run_data = {
            'id': f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'scenario': scenario,
            'panne': test_panne,
            'dp': use_dp,
            'debut': datetime.now()
        }
        st.session_state.lancer = True
    st.markdown("---")
    st.info("Selectionnez un service et lancez l'analyse")
    st.markdown("---")
    st.markdown("**Contact**")
    st.caption("Ministere du Tourisme")
    st.caption("1, Avenue Mohamed V")
    st.caption("1001 Tunis, Tunisie")
    st.caption("Email: contact@tourisme.tn")

# Page d'accueil
if not st.session_state.get('lancer', False):
    
    if st.session_state.history:
        st.markdown('<div class="section-title">Historique des executions</div>', unsafe_allow_html=True)
        hist = []
        for h in st.session_state.history[-5:]:
            duree = (h['fin'] - h['debut']).total_seconds() if 'fin' in h else 0
            hist.append({"ID": h['id'], "Scenario": h['scenario'], "Statut": "Succes", "Duree": f"{duree:.1f}s"})
        st.dataframe(pd.DataFrame(hist), use_container_width=True)
    
    st.markdown('<div class="section-title">Base de donnees nationale</div>', unsafe_allow_html=True)
    try:
        df = pd.read_csv('hotels_tunisie.csv')
        st.dataframe(df.head(8), use_container_width=True)
    except:
        st.error("Base de donnees non disponible")

# Execution
else:
    run = st.session_state.run_data
    chrono = []
    
    with st.spinner("Analyse en cours..."):
        chrono.append({"Phase": "Plan", "Action": "Generation du plan", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
        
        # ========== SCENARIO 1 ==========
        if "KPIs" in run['scenario']:
            tool = ReadTourismDataTool()
            
            if run['panne']:
                chrono.append({"Phase": "Act", "Action": "Lecture CSV", "Statut": "ECHEC", "Heure": datetime.now().strftime("%H:%M:%S")})
                st.error("Fichier non trouve")
                result = tool.execute({'filepath': 'fichier_inexistant.csv'})
                st.json(result)
                st.stop()
            
            chrono.append({"Phase": "Act", "Action": "Lecture CSV", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
            result = tool.execute({'filepath': 'hotels_tunisie.csv'})
            
            if result['status'] == 'success':
                data = pd.DataFrame(result['data'])
                occ_moyen = data['taux_occupation_2024'].mean()
                rev_moyen = data['revenu_chambre_journalier'].mean()
                
                chrono.append({"Phase": "Observe", "Action": "Calcul KPIs", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                chrono.append({"Phase": "Critique", "Action": "Validation", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                
                st.success(f"Analyse terminee avec succes ({result['row_count']} etablissements)")
                
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Taux d'occupation", f"{occ_moyen:.1f}%")
                with col2: st.metric("RevPAR", f"{rev_moyen:.1f} TND")
                with col3: st.metric("Etablissements", result['row_count'])
                
                st.markdown('<div class="section-title">Base de donnees</div>', unsafe_allow_html=True)
                st.dataframe(data, use_container_width=True)
                
                top3 = data.nlargest(3, 'taux_occupation_2024')[['gouvernorat', 'taux_occupation_2024']]
                fig = px.bar(top3, x='gouvernorat', y='taux_occupation_2024', title="Top 3 regions", color='gouvernorat')
                st.plotly_chart(fig, use_container_width=True)
        
        # ========== SCENARIO 2 ==========
        elif "API" in run['scenario']:
            tool = MockTourismAPITool()
            chrono.append({"Phase": "Act", "Action": "Appel API", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
            
            result = tool.execute({'endpoint': '/api/occupancy', 'simulate_failure': run['panne']})
            
            if result['status'] == 'success':
                chrono.append({"Phase": "Observe", "Action": "Analyse donnees", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                chrono.append({"Phase": "Critique", "Action": "Validation", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                
                st.success("Indicateurs nationaux charges")
                
                col1, col2 = st.columns(2)
                with col1: st.metric("Taux d'occupation national", f"{result['data']['national_avg_occupancy']}%")
                with col2: st.metric("Periode", "2024")
                
                df_api = pd.DataFrame(result['data']['by_region'].items(), columns=['Region', 'Taux (%)'])
                st.dataframe(df_api, use_container_width=True)
                fig = px.bar(df_api, x='Region', y='Taux (%)', title="Taux par region", color='Region')
                st.plotly_chart(fig, use_container_width=True)
            else:
                chrono[-1]["Statut"] = "ECHEC"
                st.error(f"Erreur: {result.get('error')}")
        
        # Benchmark
        obj = {'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen']}
        
        bt = BacktrackingPlanner({}, max_steps=5)
        s1 = time.perf_counter()
        bt.plan(obj)
        t_bt = (time.perf_counter() - s1) * 1000
        stats_bt = bt.get_stats()
        
        if run['dp']:
            dp = DPPlanner({}, max_steps=5)
            s2 = time.perf_counter()
            dp.plan(obj)
            t_dp = (time.perf_counter() - s2) * 1000
            stats_dp = dp.get_stats()
    
    # ========== AFFICHAGE METRIQUES ==========
    st.markdown("---")
    st.markdown("### Branches élaguées")
    st.metric("", stats_bt.get('pruned_branches', 0))
    
    st.markdown("### Temps de planification (ms)")
    st.metric("", f"{t_bt:.2f}")
    
    # ========== JOURNAUX D'EXECUTION ==========
    st.markdown('<div class="section-title">Journaux d\'execution (JSONL)</div>', unsafe_allow_html=True)
    
    logs_data = []
    for i, log in enumerate(chrono):
        logs_data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
            "step": i,
            "phase": log.get('Phase', '').lower(),
            "type": "info",
            "data": json.dumps(log, default=str)
        })
    
    logs_df = pd.DataFrame(logs_data)
    st.dataframe(logs_df, use_container_width=True)
    
    # ========== BOUTON TELECHARGEMENT ==========
    log_json = json.dumps(chrono, indent=2, default=str, ensure_ascii=False)
    st.download_button(
        label="Télécharger les logs",
        data=log_json,
        file_name=f"execution_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
    
    st.markdown("---")
    
    # ========== BENCHMARK ==========
    st.markdown('<div class="section-title">Performance des algorithmes</div>', unsafe_allow_html=True)
    
    if run['dp']:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Backtracking**\nTemps: {t_bt:.1f} ms\nBranches: {stats_bt.get('branches_explored', 0)}")
        with col2:
            st.success(f"**Dynamic Programming**\nTemps: {t_dp:.1f} ms\nCache hit: {stats_dp.get('cache_hit_ratio', 0)*100:.1f}%")
        if t_dp > 0:
            gain = round(t_bt / t_dp, 1)
            st.caption(f"Amelioration DP vs BT: {gain}x plus rapide")
    else:
        st.info(f"**Backtracking**\nTemps: {t_bt:.1f} ms\nBranches: {stats_bt.get('branches_explored', 0)}")
    
    # Sauvegarde
    run['fin'] = datetime.now()
    st.session_state.history.append(run)
    
    if st.button("Nouvelle analyse", use_container_width=True):
        st.session_state.lancer = False
        st.rerun()

st.markdown("""
<div class="footer">
    <p>Ministere du Tourisme Tunisien | Observatoire National</p>
    <p>© 2025 - Tous droits reserves | Donnees officielles</p>
</div>
""", unsafe_allow_html=True)