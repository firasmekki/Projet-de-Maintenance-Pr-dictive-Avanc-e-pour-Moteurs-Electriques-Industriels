 ORBIT AI — Copilote Intelligent de Maintenance Prédictive pour Moteurs Électriques Industriels

> **Projet de Fin d'Études (PFE)**  
> Système d'intelligence artificielle avancé pour la surveillance, le diagnostic et la prédiction de défaillances des moteurs électriques industriels.

---

## Aperçu du Projet

**ORBIT AI** est une plateforme full-stack de maintenance prédictive qui combine le machine learning, l'analyse spectrale et un assistant IA conversationnel pour permettre aux ingénieurs de maintenance industrielle de :

- Détecter les défauts moteurs **avant** la panne (réduction des arrêts non planifiés)
- Estimer la **durée de vie résiduelle (RUL)** des équipements
- Générer des **rapports d'analyse complets** avec explications IA
- Interroger un **chatbot spécialisé** en maintenance industrielle

---

## Interfaces & Fonctionnalités

### 1. Page d'Import (Upload)
Interface de glisser-déposer pour l'import des fichiers CSV de télémétrie moteur.
- Validation du format et qualité des données en temps réel
- Indicateur de score qualité du dataset
- Aperçu du nombre de lignes, colonnes et valeurs manquantes
- Support des fichiers jusqu'à 50 Mo
<img width="2880" height="3146" alt="localhost_5173_ (2)" src="https://github.com/user-attachments/assets/6278b428-f227-4a3c-a5ea-639b6feda26d" />


---

### 2. Page de Prévisualisation (Data Preview)
Analyse exploratoire automatique du dataset importé.
- Tableau interactif des premières lignes avec pagination
- Statistiques descriptives par colonne (min, max, moyenne, écart-type, médiane)
- Détection automatique des colonnes pertinentes (température, vibration, courant, tension, puissance)
- Indicateurs de tendance par variable
<img width="2880" height="3242" alt="localhost_5173_ (3)" src="https://github.com/user-attachments/assets/49874d27-2b27-4d38-b632-dd83758be657" />



---

### 3. Page d'Analyse en Cours (Analyzing)
Interface animée pendant le traitement multi-modèles.
- Progression en temps réel du pipeline d'analyse
- Affichage des étapes : prétraitement → ML → FFT → RUL → rapport IA
- Estimation du temps restant
<img width="2880" height="3242" alt="localhost_5173_ (4)" src="https://github.com/user-attachments/assets/63f92fc9-92db-4ed9-b212-fe38c2da0233" />


---

### 4. Page de Résultats (Results) — Interface Principale
Tableau de bord complet avec tous les indicateurs de santé moteur.

#### Indicateurs KPI (en-tête)
- **Score de Santé Global** : jauge animée 0–100%
- **Défaut Détecté** : classification du type de panne
- **Sévérité** : FAIBLE / MOYEN / ÉLEVÉ / CRITIQUE
- **Niveau de Risque** : indicateur couleur
- **Anomalies** : pourcentage de points anormaux détectés

#### Graphiques & Analyses
| Composant | Description |
|-----------|-------------|
| **Distribution des Défauts** | Donut SVG interactif — répartition probabiliste des types de défauts avec effet glow au survol |
| **Analyse Spectrale FFT** | Diagramme en barres des fréquences vibratoires — identification de la fréquence dominante |
| **Chronologie de Santé** | Timeline des phases d'évolution de l'état moteur |
| **Prévision Temporelle** | Trajectoire de santé prédite sur 7 / 14 / 30 jours (LSTM + régression) |
| **Matrice de Corrélation** | Heatmap des corrélations entre variables physiques |
| **Graphiques de Tendance** | Séries temporelles : température, vibration, courant, tension, puissance, charge |
| **Estimation RUL** | Durée de vie résiduelle estimée avec intervalle de confiance |
| **XAI — Contributions** | Explication des facteurs déterminants dans le diagnostic (Explainable AI) |
| **Profil Moteur** | Caractéristiques techniques de l'équipement analysé |
| **Priorités de Maintenance** | Actions recommandées classées par urgence (immédiate / jours / semaines / mois) |


<img width="2880" height="11870" alt="localhost_5173_ (6)" src="https://github.com/user-attachments/assets/48bc0ebf-602d-4123-b485-1059d0408a7a" />

---

### 5. Page Historique (History)
Consultation de tous les rapports d'analyse précédents.
- Liste chronologique des analyses avec score de santé et défaut détecté
- Rechargement d'un rapport complet depuis l'historique
- Indicateurs visuels de risque par entrée
<img width="2880" height="1830" alt="localhost_5173_ (2)" src="https://github.com/user-attachments/assets/1b06f9a6-5db1-4c04-9044-36109bbdfa5c" />


---

### 6. Chatbot IA (Assistant Conversationnel)
Widget flottant accessible depuis toutes les interfaces.
- Réponses contextualisées basées sur le dernier rapport d'analyse chargé
- Architecture **RAG** (Retrieval-Augmented Generation) avec ChromaDB
- Base de connaissances en maintenance industrielle intégrée
- Modèle LLM local **Ollama** (Qwen 2.5) — données 100% locales, aucun envoi cloud
- Support du français et de l'anglais
<img width="1917" height="866" alt="Capture d’écran 2026-07-04 211516" src="https://github.com/user-attachments/assets/c2a6db34-6b44-4125-934c-0632f673734a" />


---

## Architecture Technique

```
orbit-ai/
├── backend/                    # FastAPI — Python 3.11+
│   ├── app/
│   │   ├── api/               # Routes REST (/api/v1/...)
│   │   ├── core/              # Config, sécurité, settings
│   │   ├── services/          # Pipeline ML, RAG, chatbot
│   │   ├── repositories/      # Accès base de données
│   │   └── schemas/           # Modèles Pydantic
│   └── Dockerfile
├── frontend/                   # React 18 + TypeScript + Vite
│   └── src/
│       ├── components/        # Composants réutilisables
│       ├── pages/             # Upload, Preview, Analyzing, Results, History
│       ├── hooks/             # useTheme, useChartTheme
│       └── types/             # Interfaces TypeScript
├── ml/                        # Modèles & entraînement
├── alembic/                   # Migrations base de données
├── docker-compose.yml         # Orchestration complète
└── .env.example               # Template de configuration
```

---

## Stack Technologique

### Backend
| Technologie | Rôle |
|-------------|------|
| **FastAPI** | API REST asynchrone |
| **PostgreSQL** | Stockage des rapports et historique |
| **SQLAlchemy (async)** | ORM |
| **Alembic** | Migrations base de données |
| **XGBoost** | Classification des défauts moteur |
| **LSTM (PyTorch/Keras)** | Prédiction temporelle de santé |
| **AutoEncoder** | Détection d'anomalies non supervisée |
| **FFT (NumPy/SciPy)** | Analyse spectrale vibratoire |
| **ChromaDB** | Base vectorielle pour RAG |
| **Ollama + Qwen 2.5** | LLM local pour le chatbot IA |
| **Docker / Docker Compose** | Containerisation complète |

### Frontend
| Technologie | Rôle |
|-------------|------|
| **React 18** | Interface utilisateur |
| **TypeScript** | Typage statique |
| **Vite** | Build tool |
| **TailwindCSS** | Styles utilitaires |
| **Recharts** | Graphiques interactifs |
| **SVG custom** | Donut chart avancé |
| **Lucide Icons** | Iconographie |

---

## Installation & Démarrage

### Prérequis
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Ollama installé localement ([ollama.ai](https://ollama.ai))

### 1. Cloner le dépôt
```bash
git clone https://github.com/firasmekki/Projet-de-Maintenance-Pr-dictive-Avanc-e-pour-Moteurs-Electriques-Industriels.git
cd Projet-de-Maintenance-Pr-dictive-Avanc-e-pour-Moteurs-Electriques-Industriels
```

### 2. Configurer l'environnement
```bash
# Backend
cp backend/.env.example backend/.env
# Éditez backend/.env avec vos paramètres (BDD, Ollama, etc.)
```

### 3. Démarrer avec Docker
```bash
docker compose up -d
```

### 4. Démarrer le modèle LLM
```bash
ollama pull qwen2.5:1.5b
ollama serve
```

### 5. Frontend (développement)
```bash
cd frontend
npm install
npm run dev
# Ouvre sur http://localhost:5173
```

### 6. Backend (développement sans Docker)
```bash
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
# API disponible sur http://localhost:8000
# Documentation Swagger : http://localhost:8000/docs
```

---

## Sécurité

- Les fichiers `.env` sont exclus du dépôt Git via `.gitignore`
- Les mots de passe de base de données doivent être changés avant tout déploiement
- Le LLM Ollama tourne **entièrement en local** — aucune donnée n'est transmise à des services cloud
- Les données uploadées restent sur le serveur local
- CORS configuré pour n'autoriser que les origines déclarées
- Clé secrète JWT à générer avec `openssl rand -hex 32`

---

## Variables d'Environnement

Copiez `backend/.env.example` vers `backend/.env` et renseignez :

| Variable | Description | Exemple |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | `MotDePasse_Fort_2024!` |
| `SECRET_KEY` | Clé JWT (64 chars) | `openssl rand -hex 32` |
| `OLLAMA_MODEL` | Modèle LLM utilisé | `qwen2.5:1.5b` |
| `OLLAMA_BASE_URL` | URL d'Ollama | `http://localhost:11434` |
| `BACKEND_CORS_ORIGINS` | Origines CORS autorisées | `["http://localhost:5173"]` |

---

## Auteur

**Firas Mekki**  
Étudiant ingénieur — Projet de Fin d'Études  
Spécialité : Intelligence Artificielle & Systèmes Industriels

---

## Licence

Ce projet est développé dans le cadre d'un PFE académique.  
Tous droits réservés — © 2024 Firas Mekki
