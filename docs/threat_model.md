# Modèle de Menace (Threat Model) — Section 4.6

## Contexte

Ce projet traite des données synthétiques du secteur touristique tunisien.
Aucune donnée personnelle réelle ou confidentielle n'est utilisée.

## Tableau des risques et contrôles

| Risque | Description | Contrôle mis en place | Fichier |
|--------|-------------|----------------------|---------|
| **Path traversal** | L'agent demande un fichier hors sandbox (`../../etc/passwd`) | Allow-list stricte des 3 fichiers CSV autorisés dans `ReadTourismDataTool` | `tourism_tools.py` |
| **Endpoint non autorisé** | L'agent appelle un endpoint inconnu (`/api/admin`) | Allow-list des 3 endpoints dans `MockTourismAPITool` + validation jsonschema dans `schemas.py` | `tourism_tools.py`, `schemas.py` |
| **Injection de paramètres** | Paramètres d'entrée invalides ou malformés | Validation `jsonschema` sur chaque entrée d'outil dans `ExecutorAgent` | `orchestrator/executor.py` |
| **Boucles infinies** | Le planificateur explore indéfiniment | `max_steps` imposé dans `BacktrackingPlanner` (élagage par profondeur) | `tourism_planner.py` |
| **Fuite entre runs** | Les données d'un run contaminent un autre run | Chaque `Orchestrator` a son propre `RunManager` (journal isolé par UUID) | `orchestrator/orchestrator.py` |
| **Fuite de secrets dans les logs** | Tokens, mots de passe visibles dans les journaux | Aucune clé API ni secret dans ce projet ; pas de données PII dans les CSV | Tous les fichiers |
| **HTTP sortant non contrôlé** | Appels vers des systèmes tiers non documentés | `MockTourismAPITool` ne fait aucun appel réseau réel ; `ALLOWED_HOSTS` documenté dans `tourism_tools.py` | `tourism_tools.py` |
| **Déni de service** | Trop de requêtes HTTP / retry infini | Retry borné à 3 tentatives via `tenacity` ; timeout HTTP 5s via `httpx` | `tourism_tools.py` |
| **Cache pollution** | Le cache DP d'un run corrompt celui d'un autre | Cache en mémoire d'instance (non partagé) ; vérifié par `test_concurrency.py` | `tourism_planner.py` |

## Redaction (Section 4.6)

Les champs potentiellement sensibles dans les CSV synthétiques :
- `hotel_id` : identifiant fictif (pas de lien avec des entités réelles)
- `gouvernorat` : donnée publique (pas d'information personnelle)

→ Aucune redaction nécessaire pour ce projet (données entièrement synthétiques).
Dans un projet réel (données clients, KYC, etc.), un module de redaction
remplacerait les champs PII par des tokens avant journalisation.

## Posture sécurité globale

Ce projet est **read-only** : aucun outil ne modifie de fichier, ne persiste
de données en base, ni ne transmet de données vers l'extérieur.
Le risque résiduel est donc minimal.
