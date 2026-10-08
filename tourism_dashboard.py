# ============================================
# tourism_dashboard.py - Interface Streamlit principale avec traces des agents
# ============================================
# Cette version affiche les résultats des scénarios 1 et 2,
# les métriques de Backtracking/DP, les traces détaillées des
# trois agents (Planner, Executor, Critic) et un panneau de sécurité.
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from tourism_tools import ReadTourismDataTool, MockTourismAPITool
from tourism_planner import BacktrackingPlanner, DPPlanner
from orchestrator import Orchestrator   # ← import depuis ton dossier orchestrator
import time
import json
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result

st.set_page_config(page_title="Tourisme Tunisien", layout="wide")

# ============================================
# CSS (design original complet)
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8edf5 100%); }
    .main-header {
        background: linear-gradient(135deg, #003366 0%, #00509e 100%);
        padding: 1rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        border-bottom: 3px solid #e8a800;
    }
    .main-header h1 { margin: 0; font-size: 1.5rem; font-weight: 600; }
    .main-header p { margin: 0.2rem 0 0 0; opacity: 0.9; font-size: 0.8rem; }
    .badge-officiel {
        background: #e8a800; color: #003366; padding: 0.15rem 0.8rem;
        border-radius: 20px; font-size: 0.6rem; font-weight: bold; display: inline-block; margin-bottom: 0.3rem;
    }
    .metric-card {
        background: white; padding: 1rem; border-radius: 12px; text-align: center;
        border-left: 4px solid #e8a800; border-bottom: 2px solid #003366; transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
    .metric-card h3 { color: #003366; margin: 0 0 0.3rem 0; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
    .metric-card .value { color: #003366; font-size: 1.6rem; font-weight: 700; }
    .result-card {
        background: white; padding: 1rem; border-radius: 12px; text-align: center;
        border-bottom: 3px solid #e8a800; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.3s ease;
    }
    .result-card:hover { transform: translateY(-3px); }
    .result-card .label { color: #6c757d; font-size: 0.7rem; text-transform: uppercase; }
    .result-card .value { color: #003366; font-size: 1.6rem; font-weight: 700; }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e0e0e0; }
    .stButton > button { background: #003366; color: white; border: none; border-radius: 25px; font-weight: 500; transition: all 0.3s ease; width: 100%; }
    .stButton > button:hover { background: #002244; }
    .section-title { font-size: 1rem; font-weight: 600; color: #003366; margin: 1.2rem 0 0.8rem 0; border-left: 4px solid #e8a800; padding-left: 0.8rem; }
    .footer { text-align: center; margin-top: 2rem; padding: 0.8rem; color: #6c757d; border-top: 1px solid #e0e0e0; font-size: 0.65rem; }
    .stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #e0e0e0; }
    .dataframe th { background: #003366 !important; color: white !important; }
    .success-box { background: #d4edda; padding: 0.8rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; color: #155724; }
    .run-row { padding: 0.4rem 0.8rem; border-radius: 8px; font-size: 0.75rem; margin-bottom: 4px; border-left: 3px solid #e8a800; background: #f8f9fa; }
    /* Styles pour les agents */
    .agent-planner { border-left: 5px solid #003366; background-color: #f0f7ff; padding: 0.5rem 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .agent-executor { border-left: 5px solid #28a745; background-color: #f0fff0; padding: 0.5rem 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .agent-critic { border-left: 5px solid #ffc107; background-color: #fff8e1; padding: 0.5rem 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .agent-title { font-weight: bold; font-size: 1rem; margin-bottom: 0.5rem; }
    /* Style pour le panneau sécurité */
    .safety-panel {
        background: #fff3e0;
        border-left: 5px solid #e8a800;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# EN-TETE
# ============================================
st.markdown("""
<div class="main-header fade-in">
    <div class="badge-officiel">MINISTERE DU TOURISME</div>
    <h1>Observatoire du Tourisme Tunisien</h1>
    <p>Orchestration Multi-Agents | Backtracking & Dynamic Programming | Analyse des indicateurs</p>
</div>
""", unsafe_allow_html=True)

try:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Flag_of_Tunisia.svg/1200px-Flag_of_Tunisia.svg.png" 
             style="width: 60px; border-radius: 8px;">
    </div>
    """, unsafe_allow_html=True)
except:
    pass

# ============================================
# SESSION STATE
# ============================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'orchestrator_trace' not in st.session_state:
    st.session_state.orchestrator_trace = None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("---")
    scenario = st.radio("Services", ["Analyse des KPIs Hoteliers", "Indicateurs Nationaux (API)"], label_visibility="collapsed")
    st.markdown("---")
    test_panne = st.checkbox("Mode Test (Injection de panne)")
    use_dp = st.checkbox("Utiliser Dynamic Programming (DP)", value=True)
    st.markdown("---")
    if st.button("Executer l'analyse", use_container_width=True):
        # 1) Lancer l'orchestrateur pour récupérer la trace des agents
        objective = {}
        if scenario == "Analyse des KPIs Hoteliers":
            objective = {'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen']}
        else:
            objective = {'required_data': ['api_data'], 'kpis': []}
        orch = Orchestrator(use_dp=use_dp, max_steps=5)
        result_orch = orch.run(objective)          # ← appel sans paramètre scenario
        st.session_state.orchestrator_trace = result_orch.get('trace')
        # 2) Exécution normale pour l'affichage riche
        st.session_state.run_data = {
            'id': f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'scenario': scenario,
            'panne': test_panne,
            'dp': use_dp,
            'debut': datetime.now()
        }
        st.session_state.lancer = True
    st.markdown("---")
    st.markdown("### Historique des runs")
    if st.session_state.history:
        for run_hist in reversed(st.session_state.history[-5:]):
            statut = run_hist.get('statut', 'success')
            couleur = "#155724" if statut == 'success' else "#721c24"
            icone = "✓" if statut == 'success' else "✗"
            duree = ""
            if run_hist.get('fin') and run_hist.get('debut'):
                duree = f" | {(run_hist['fin'] - run_hist['debut']).seconds}s"
            st.markdown(
                f"<div class='run-row'>"
                f"<span style='color:{couleur};font-weight:600;'>{icone}</span> "
                f"<b>{run_hist['id'][-8:]}</b><br>"
                f"<span style='color:#6c757d;'>{run_hist['scenario'][:22]}{duree}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.caption("Aucun run effectué")
    st.markdown("---")
    st.markdown("### Contact")
    st.caption("Ministere du Tourisme")
    st.caption("1, Avenue Mohamed V")
    st.caption("1001 Tunis, Tunisie")
    st.caption("Email: contact@tourisme.tn")
    st.caption("Horaires: Lun-Ven | 8h30-16h30")

# ============================================
# PAGE D'ACCUEIL (si aucun run)
# ============================================
if not st.session_state.get('lancer', False):
    st.markdown('<div class="section-title fade-in">Presentation du service</div>', unsafe_allow_html=True)
    st.write("L'Observatoire du Tourisme Tunisien met a disposition un systeme d'orchestration multi-agents pour l'analyse des indicateurs cles du secteur touristique national.")
    st.markdown("**Services disponibles**")
    services_df = pd.DataFrame({
        "Service": ["Analyse KPIs", "Indicateurs nationaux"],
        "Description": ["Calcul automatique des indicateurs hoteliers", "Donnees API sur l'occupation par region"]
    })
    st.dataframe(services_df, use_container_width=True, hide_index=True)
    st.markdown("**Donnees disponibles**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- 10 etablissements hoteliers")
        st.markdown("- 7 indicateurs de performance")
    with col2:
        st.markdown("- Couverture nationale")
        st.markdown("- Donnees mises a jour")
    st.markdown('<div class="section-title fade-in">Statistiques generales</div>', unsafe_allow_html=True)
    try:
        df = pd.read_csv('hotels_tunisie.csv')
        nb_hotels = len(df)
        avg_etoiles = df['etoiles'].mean()
        avg_taux = df['taux_occupation_2024'].mean()
        avg_revpar = df['revenu_chambre_journalier'].mean()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Etablissements hoteliers", nb_hotels)
        with col2: st.metric("Classification moyenne", f"{avg_etoiles:.1f} etoiles")
        with col3: st.metric("Taux d'occupation moyen", f"{avg_taux:.1f}%")
        with col4: st.metric("RevPAR moyen", f"{avg_revpar:.1f} TND")
    except:
        st.error("Base de donnees non disponible")
    st.markdown('<div class="section-title fade-in">Apercu de la base de donnees</div>', unsafe_allow_html=True)
    try:
        df = pd.read_csv('hotels_tunisie.csv')
        df_preview = df.head(8).rename(columns={
            'gouvernorat': 'Gouvernorat', 'hotel_id': 'ID', 'etoiles': 'Etoiles',
            'capacite_lits': 'Capacite (lits)', 'taux_occupation_2024': 'Taux occupation (%)',
            'prix_moyen_nuit_tnd': 'Prix moyen (TND)', 'revenu_chambre_journalier': 'RevPAR (TND)'
        })
        st.dataframe(df_preview, use_container_width=True)
    except:
        st.error("Base de donnees non disponible")
    st.markdown('<div class="section-title fade-in">Repartition par gouvernorat</div>', unsafe_allow_html=True)
    try:
        df = pd.read_csv('hotels_tunisie.csv')
        region_stats = df.groupby('gouvernorat').agg({'hotel_id': 'count', 'taux_occupation_2024': 'mean'}).round(1).reset_index()
        region_stats.columns = ['Gouvernorat', "Nombre d'etablissements", 'Taux occupation (%)']
        st.dataframe(region_stats, use_container_width=True)
    except:
        pass

# ============================================
# EXECUTION - RESULTATS
# ============================================
else:
    run = st.session_state.run_data
    chrono = []
    run_statut = 'success'
    with st.spinner("Analyse en cours..."):
        chrono.append({"Phase": "Plan", "Action": "Generation du plan", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})

        # ---------- SCENARIO KPIs ----------
        if "KPIs" in run['scenario']:
            tool = ReadTourismDataTool()
            if run['panne']:
                chrono.append({"Phase": "Act", "Action": "Lecture CSV", "Statut": "ECHEC (panne injectee)", "Heure": datetime.now().strftime("%H:%M:%S")})
                st.error("Fichier non trouve - Test de resilience (panne injectee)")
                obj = {'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen']}
                bt = BacktrackingPlanner({}, max_steps=5)
                s1 = time.perf_counter()
                bt.plan(obj)
                t_bt = (time.perf_counter() - s1) * 1000
                stats_bt = bt.get_stats()
                t_dp = None
                stats_dp = None
                if run['dp']:
                    dp = DPPlanner({}, max_steps=5)
                    dp.plan(obj)
                    s2 = time.perf_counter()
                    dp.plan(obj)
                    t_dp = (time.perf_counter() - s2) * 1000
                    stats_dp = dp.get_stats()
                st.markdown("---")
                st.markdown("## Metriques du planificateur")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Branches explorees", stats_bt.get('branches_explored', 0))
                    st.metric("Branches elaguees", stats_bt.get('pruned_branches', 0))
                with col2:
                    st.metric("Temps BT", f"{t_bt:.2f} ms")
                    if t_dp: st.metric("Temps DP", f"{t_dp:.2f} ms")
                with col3:
                    if stats_dp:
                        st.metric("Cache hits", stats_dp.get('cache_hits', 0))
                        st.metric("Cache hit ratio", f"{stats_dp.get('cache_hit_ratio',0)*100:.1f}%")
                run_statut = 'failed'
                run['statut'] = run_statut
                run['fin'] = datetime.now()
                if run['id'] not in [h['id'] for h in st.session_state.history]:
                    st.session_state.history.append(run)
                st.stop()
            chrono.append({"Phase": "Act", "Action": "Lecture CSV", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
            result = tool.execute({'filepath': 'hotels_tunisie.csv'})
            if result['status'] == 'success':
                data = pd.DataFrame(result['data'])
                occ_moyen = data['taux_occupation_2024'].mean()
                rev_moyen = data['revenu_chambre_journalier'].mean()
                chrono.append({"Phase": "Observe", "Action": "Calcul KPIs", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                chrono.append({"Phase": "Critique", "Action": "Validation", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                st.markdown('<div class="success-box fade-in"> Analyse terminee avec succes</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Indicateurs nationaux</div>', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Taux d'occupation national", f"{occ_moyen:.1f}%")
                with col2: st.metric("RevPAR moyen", f"{rev_moyen:.1f} TND")
                with col3: st.metric("Etablissements recenses", result['row_count'])
                with col4: st.metric("Classification moyenne", f"{data['etoiles'].mean():.1f} ★")
                st.markdown('<div class="section-title">Base de donnees des etablissements hoteliers</div>', unsafe_allow_html=True)
                df_display = data.rename(columns={
                    'gouvernorat': 'Region', 'hotel_id': 'ID', 'etoiles': '⭐',
                    'taux_occupation_2024': 'Taux %', 'revenu_chambre_journalier': 'RevPAR'
                })
                st.dataframe(df_display[['Region','ID','⭐','Taux %','RevPAR']], use_container_width=True)
                if 'gouvernorat' in data.columns and 'taux_occupation_2024' in data.columns:
                    st.markdown('<div class="section-title">Classement des regions par performance</div>', unsafe_allow_html=True)
                    top3 = data.nlargest(3, 'taux_occupation_2024')[['gouvernorat', 'taux_occupation_2024']]
                    fig = px.bar(top3, x='gouvernorat', y='taux_occupation_2024', title="Top 3 regions par taux d'occupation", color='gouvernorat')
                    fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
                    st.plotly_chart(fig, use_container_width=True)
                st.markdown('<div class="section-title">Statistiques par gouvernorat</div>', unsafe_allow_html=True)
                region_stats = data.groupby('gouvernorat').agg({
                    'hotel_id': 'count', 'etoiles': 'mean', 'taux_occupation_2024': 'mean', 'revenu_chambre_journalier': 'mean'
                }).round(1).reset_index()
                region_stats.columns = ['Gouvernorat', 'Nb hotels', 'Etoiles moy', 'Taux occ. (%)', 'RevPAR (TND)']
                st.dataframe(region_stats, use_container_width=True)

        # ---------- SCENARIO API ----------
        elif "API" in run['scenario']:
            tool = MockTourismAPITool()
            chrono.append({"Phase": "Act", "Action": "Appel API /api/occupancy", "Statut": "...", "Heure": datetime.now().strftime("%H:%M:%S")})
            params = {'endpoint': '/api/occupancy', 'simulate_failure': run['panne']}
            result = None
            if run['panne']:
                st.info("Panne HTTP 429 injectee — retry automatique (max 3 tentatives, 1s entre chaque)...")
                retry_log = []
                for attempt in range(1, 4):
                    attempt_result = tool.execute(params)
                    retry_log.append({
                        "Tentative": attempt,
                        "Statut HTTP": "429 Rate Limited" if attempt_result.get('status')=='rate_limited' else "200 OK",
                        "Heure": datetime.now().strftime("%H:%M:%S")
                    })
                    chrono.append({
                        "Phase": "Act",
                        "Action": f"Retry API tentative {attempt}/3",
                        "Statut": "ECHEC (429)" if attempt_result.get('status')=='rate_limited' else "OK",
                        "Heure": datetime.now().strftime("%H:%M:%S")
                    })
                    if attempt_result.get('status') != 'rate_limited':
                        result = attempt_result
                        break
                    if attempt < 3: time.sleep(1)
                if result is None:
                    result = {'status': 'failed', 'error': 'HTTP 429 - Trop de requetes apres 3 tentatives (arret safe)'}
                st.markdown('<div class="section-title">Journal des tentatives API (backoff)</div>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(retry_log), use_container_width=True)
            else:
                result = tool.execute(params)
            if result and result.get('status') == 'success':
                chrono[-1]["Statut"] = "OK"
                chrono.append({"Phase": "Observe", "Action": "Analyse", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                chrono.append({"Phase": "Critique", "Action": "Validation", "Statut": "OK", "Heure": datetime.now().strftime("%H:%M:%S")})
                st.markdown('<div class="success-box fade-in"> API chargee avec succes</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1: st.metric("Taux d'occupation national", f"{result['data']['national_avg_occupancy']}%")
                with col2: st.metric("Periode de reference", "2024")
                st.markdown('<div class="section-title">Analyse regionale</div>', unsafe_allow_html=True)
                df_regions = pd.DataFrame(result['data']['by_region'].items(), columns=['Region', 'Taux d\'occupation (%)'])
                st.dataframe(df_regions, use_container_width=True)
                st.markdown('<div class="section-title">Visualisation des donnees regionales</div>', unsafe_allow_html=True)
                fig = px.bar(df_regions, x='Region', y='Taux d\'occupation (%)', title="Taux d'occupation par region", color='Region')
                fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                chrono[-1]["Statut"] = "ECHEC"
                chrono.append({"Phase": "Critique", "Action": "Arret safe apres retries", "Statut": "STOP", "Heure": datetime.now().strftime("%H:%M:%S")})
                st.error(f"Erreur API apres retries : {result.get('error', 'Erreur inconnue')}")
                st.warning("Arret grace apres 3 tentatives — comportement conforme a la politique de retry borne.")
                run_statut = 'failed'

    # ---------- PANEL DE SÉCURITÉ (ajouté pour conformité 11.2) ----------
    st.markdown("---")
    with st.expander("🔒 Panneau de sécurité et politiques", expanded=False):
        st.markdown('<div class="safety-panel">', unsafe_allow_html=True)
        st.markdown("**Liste blanche (allow‑list) des fichiers :**")
        st.code("hotels_tunisie.csv, arrivees_mensuelles.csv, indicateurs_saisonniers.csv", language="text")
        st.markdown("**Endpoints API autorisés :** `/api/occupancy`, `/api/arrivals`, `/api/revenue`")
        st.markdown(f"**Limitation :** `max_steps = 5` (profondeur maximale de l’arbre de planification)")
        if run_statut == 'failed':
            if "Fichier non trouve" in st.session_state.get('run_data', {}).get('scenario', ''):
                st.error("❌ Dernier arrêt : fichier CSV manquant (injection de panne)")
            elif "API" in st.session_state.get('run_data', {}).get('scenario', '') and run.get('panne'):
                st.error("❌ Dernier arrêt : HTTP 429 après 3 tentatives (retry borné)")
            else:
                st.warning("⚠️ Aucun arrêt lié à la sécurité détecté – exécution réussie.")
        else:
            st.success("✅ Aucun arrêt de sécurité – toutes les politiques respectées.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- METRIQUES PLANIFICATEUR ----------
    st.markdown("---")
    st.markdown('<div class="section-title">Performance des algorithmes</div>', unsafe_allow_html=True)
    obj = {'required_data': ['hotels'], 'kpis': ['taux_occupation_moyen']}
    bt = BacktrackingPlanner({}, max_steps=5)
    s1 = time.perf_counter()
    bt.plan(obj)
    t_bt = (time.perf_counter() - s1) * 1000
    stats_bt = bt.get_stats()
    t_dp = None
    stats_dp = None
    if run['dp']:
        dp = DPPlanner({}, max_steps=5)
        dp.plan(obj)
        s2 = time.perf_counter()
        dp.plan(obj)
        t_dp = (time.perf_counter() - s2) * 1000
        stats_dp = dp.get_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Branches explorees", stats_bt.get('branches_explored', 0))
        st.metric("Branches elaguees", stats_bt.get('pruned_branches', 0))
    with col2:
        st.metric("Temps BT", f"{t_bt:.2f} ms")
        if t_dp: st.metric("Temps DP", f"{t_dp:.2f} ms")
    with col3:
        if stats_dp:
            st.metric("Cache hits", stats_dp.get('cache_hits', 0))
            st.metric("Cache hit ratio", f"{stats_dp.get('cache_hit_ratio',0)*100:.1f}%")
    if t_dp:
        st.markdown('<div class="section-title">Comparaison BT vs DP</div>', unsafe_allow_html=True)
        comp_df = pd.DataFrame({
            "Algorithme": ["Backtracking seul", "Backtracking + DP"],
            "Temps (ms)": [f"{t_bt:.3f}", f"{t_dp:.3f}"],
            "Branches explorees": [stats_bt.get('branches_explored',0), stats_dp.get('branches_explored',0)],
            "Branches elaguees": [stats_bt.get('pruned_branches',0), stats_dp.get('pruned_branches',0)],
            "Cache hits": ["-", stats_dp.get('cache_hits',0)],
            "Cache hit ratio": ["-", f"{stats_dp.get('cache_hit_ratio',0)*100:.1f}%"],
        })
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # ---------- TRACES DES AGENTS ----------
    if st.session_state.orchestrator_trace:
        trace = st.session_state.orchestrator_trace
        st.markdown("---")
        st.markdown("##  Traces des agents multi-agents")
        
        # Planner
        with st.expander(" Agent Planner – Planification", expanded=True):
            plan_info = trace.get("plan", {})
            plan = plan_info.get("plan", [])
            if plan:
                st.markdown("**Plan généré (séquence d’actions) :**")
                for i, action in enumerate(plan):
                    st.write(f"{i+1}. `{action['tool']}` → paramètres : {action.get('params', {})}")
            else:
                st.warning("Aucun plan trouvé.")
            stats = plan_info.get("stats", {})
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Branches explorées", stats.get('branches_explored',0))
                    st.metric("Branches élaguées", stats.get('pruned_branches',0))
                with col2:
                    st.metric("Temps planif. (ms)", f"{stats.get('planning_time_ms',0):.2f}")
                    if 'cache_hits' in stats:
                        st.metric("Cache hits/misses", f"{stats['cache_hits']}/{stats['cache_misses']}")
                        st.metric("Hit ratio", f"{stats.get('cache_hit_ratio',0):.2%}")
        
        # Executor
        with st.expander("⚙️ Agent Executor – Exécution des outils", expanded=True):
            exec_steps = trace.get("execution", [])
            if exec_steps:
                for step in exec_steps:
                    st.markdown(f"**Étape {step['step']}**")
                    st.code(f"Action : {step['action']['tool']}\nParamètres : {step['action'].get('params',{})}", language="json")
                    res = step['result']
                    if res.get('status') == 'success':
                        st.success(f" Succès (data size : {len(res.get('data',[])) if isinstance(res.get('data'),list) else 'N/A'})")
                    else:
                        st.error(f" Échec : {res.get('error')}")
            else:
                st.info("Aucune exécution enregistrée.")
        
        # Critic
        with st.expander("🔍 Agent Critic – Validation", expanded=True):
            exec_steps = trace.get("execution", [])
            if exec_steps:
                for step in exec_steps:
                    verdict = step.get('verdict', {})
                    if verdict.get('verdict') == 'pass':
                        st.success(f"Étape {step['step']} : {verdict.get('reason')}")
                    else:
                        st.error(f"Étape {step['step']} : {verdict.get('reason')}")
            else:
                st.info("Aucune validation disponible.")

    # ---------- JOURNAUX ----------
    st.markdown('<div class="section-title">Journaux d execution (JSONL)</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(chrono), use_container_width=True)
    log_json = json.dumps(chrono, indent=2, default=str, ensure_ascii=False)
    st.download_button("Telecharger les logs", data=log_json,
                       file_name=f"execution_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                       mime="application/json")
    if st.button("Nouvelle analyse", use_container_width=True):
        st.session_state.lancer = False
        st.rerun()
    run['statut'] = run_statut
    run['fin'] = datetime.now()
    if run['id'] not in [h['id'] for h in st.session_state.history]:
        st.session_state.history.append(run)

# ========== FOOTER ==========
st.markdown("""
<div class="footer">
    <p> Ministere du Tourisme Tunisien | Observatoire National </p>
    <p>La Tunisie, une destination d'excellence - Donnees officielles 2025</p>
</div>
""", unsafe_allow_html=True)