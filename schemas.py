# ============================================
# schemas.py - Définition des schémas JSON pour la validation des outils
# ============================================
# Ces schémas sont utilisés par l'Executor pour valider les entrées et sorties
# des outils (Section 5.2 de l'énoncé).
# ============================================

# Schéma pour l'entrée de ReadTourismDataTool (lecture CSV hôtels)
READ_HOTELS_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {
            "type": "string",
            "pattern": "^(hotels_tunisie\\.csv|arrivees_mensuelles\\.csv|indicateurs_saisonniers\\.csv)$"
        },
        "indicator_type": {
            "type": "string",
            "enum": ["hotels", "arrivals", "seasonal"]
        }
    },
    "required": ["filepath", "indicator_type"],
    "additionalProperties": False
}

# Schéma pour la sortie de ReadTourismDataTool (succès)
READ_HOTELS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success"]},
        "data": {"type": "array"},
        "columns": {"type": "array", "items": {"type": "string"}},
        "row_count": {"type": "integer", "minimum": 1},
        "source": {"type": "string"}
    },
    "required": ["status", "data", "columns", "row_count", "source"]
}

# Schéma pour l'entrée de MockTourismAPITool
API_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "endpoint": {
            "type": "string",
            "pattern": "^/api/(occupancy|arrivals|revenue)$"
        },
        "simulate_failure": {"type": "boolean"}
    },
    "required": ["endpoint"],
    "additionalProperties": False
}

# Schéma pour la sortie succès de MockTourismAPITool (on ne valide que la présence de 'data')
API_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success"]},
        "data": {"type": "object"}
    },
    "required": ["status", "data"]
}

# Schéma pour l'entrée de ComputeKPIsTool
COMPUTE_KPIS_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "kpi_requested": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["kpi_requested"]
}

# Schéma pour la sortie de ComputeKPIsTool (succès)
COMPUTE_KPIS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"enum": ["success"]},
        "data": {"type": "object"},
        "computed_kpis": {"type": "array"}
    },
    "required": ["status", "data"]
}