# Supply Chain Disruption Prediction Using Provenance Tracking and Knowledge Reasoning

MSc Data Science dissertation project — University of Southampton
Supervised by Dr. Age Chapman

## Overview

A hybrid system for predicting supply chain disruption risk by combining a Neo4j knowledge graph with machine learning classifiers (XGBoost, Random Forest). The system uses **provenance tracking** — specifically confluence provenance, where multiple upstream supply inputs converge at a single node (e.g. Taiwan plastics + China semiconductors -> Germany electronic device assembly) — to model realistic multi-source supply chain dependencies.

The final system is delivered via a FastAPI backend and a Plotly Dash dashboard aimed at non-technical business analysts (supply chain managers, procurement teams).

## Data Sources

- **UN Comtrade** — international trade records across 10 countries, 4 products, 2021-2023
- **GDELT** — geopolitical event data (historical snapshots)
- **World Bank Logistics Performance Index (LPI)** — country logistics scores (2018 data used as proxy; 2023 values were unavailable)

## Project Structure

\\\
.
├── data/                   # Cleaned and raw datasets (large raw GDELT files excluded, see .gitignore)
├── ml/                     # Feature/label sets and trained models
├── clean_data.py           # Data cleaning and integration pipeline
├── country_codes.py        # M49 <-> ISO3 country code mapping
├── download_comtrade.py    # UN Comtrade API data collection
├── download_gdelt.py       # GDELT data collection
├── build_kg.py             # Neo4j knowledge graph construction
├── train_ml.py             # ML model training (XGBoost, Random Forest)
├── test_neo4j.py           # Neo4j connection test
├── test_news.py            # GDELT/news data test
├── test_setup.py           # Environment setup test
├── debug_merge.py          # Debugging script for data merge issues
└── requirements.txt        # Python dependencies
\\\

## Methodology Highlights

- **Data leakage correction:** disruption labels are defined independently of predictive features, using a >15% year-over-year trade value drop (Comtrade) rather than deriving labels from the same features used for prediction.
- **Time-based train/test split:** trained on 2021-2022 data, tested on unseen 2023 data, to reflect real-world deployment rather than leaking future information via random splits.
- **Country code standardisation:** UN Comtrade's numeric M49 codes are mapped to the ISO 3-letter codes used by LPI and GDELT.
- **Confluence provenance:** the knowledge graph schema was redesigned to represent multi-input convergence at assembly nodes, a differentiator relative to prior work.

## Results

| Model         | Accuracy | F1 Score |
|---------------|----------|----------|
| XGBoost       | 70.3%    | 0.682    |
| Random Forest | 65.4%    | 0.615    |

## Tech Stack

Python 3.12 - Neo4j (bolt://127.0.0.1:7687) - XGBoost - scikit-learn - FastAPI - Plotly Dash

## Project Status

- [x] Phase 1: Environment setup
- [x] Phase 2: Data collection and cleaning
- [x] Phase 3: Knowledge graph construction
- [x] Phase 4: ML model development
- [ ] Phase 5: Hybrid risk-scoring engine (FastAPI)
- [ ] Phase 6: Dashboard and evaluation

## Limitations

- 2023 World Bank LPI data was unavailable; 2018 values used as a proxy.
- Live GDELT integration (real-time event ingestion) has not yet been implemented.
- Raw GDELT export files are excluded from this repository due to size; use \download_gdelt.py\ to regenerate them.
