# AuctionEdge

**A bid-price optimization and A/B test framework for used-vehicle acquisition.**

Most of the Gross Profit per Unit (GPU) a used-car retailer can earn is decided
at the moment a vehicle is bought, not when it's sold. Overpay at auction and
no amount of downstream reconditioning or pricing recovers the margin.

AuctionEdge is an end-to-end analytics project that models bid prices on
used-vehicle auction lots, predicts expected GPU per lot with confidence
intervals, and includes a built-in A/B test framework for safely rolling out
the model into production.

> **Status:** Active development, May 2026 – Present.
> This README documents the project plan. Code, models, and dashboard are
> being built incrementally — see the [Roadmap](#roadmap) section for what's
> live today vs. coming next.

---

## Why This Project

I built AuctionEdge to think seriously about a specific problem: how should
a used-car retailer decide how much to bid on a vehicle at auction, when the
eventual gross profit depends on dozens of downstream variables (reconditioning
cost, days-to-sale, financing attach rate, regional demand)?

The project answers three questions:

1. **What's the right bid for a given vehicle?** A regression model trained
   on 550K real auction lots, with quantile regression producing prediction
   intervals — not just a point estimate.
2. **Where are we systematically overpaying?** SHAP-driven segmentation
   surfaces make / model / region / age combinations where bids consistently
   exceed downstream realized GPU.
3. **How do we roll the model out safely?** A built-in A/B test designer
   with power analysis, holdout split, sequential monitoring, and a rollout
   simulator showing cumulative GPU lift under three launch strategies.

---

## Data

| Source | Description | Use |
|---|---|---|
| Kaggle: Used Cars Auction Prices | ~550K Manheim-style auction lots (make, model, year, odometer, MMR, sellingprice) | Primary training data for bid-price model |
| FRED: Manheim Used Vehicle Value Index | Monthly wholesale market index | Macro anchor for synthetic downstream economics |
| FRED: Used Car CPI, Auto Loan Rate, Consumer Sentiment | Monthly macro covariates | Feature engineering |
| Synthetic: Downstream lifecycle | Reconditioning cost, listing price, days-to-sale, financing/VSC/GAP attach, sale price | Simulated to complete the auction → eventual GPU loop |

Synthetic distributions are anchored to Carvana's publicly reported Q1 2026
unit economics (187K retail units, $1.27B gross profit) so downstream numbers
are defensible against real industry economics. The synthetic generator and
its assumptions are documented in `notebooks/01_synthetic_data_design.ipynb`.

---

## Architecture

```text
Kaggle (550K auction lots) ─┐
FRED API (macro indicators) ─┤
Synthetic generator         ─┘
            │
            ▼
DuckDB (local warehouse)
            │
            ▼
dbt models
├── staging
├── facts (fact_auction, fact_lifecycle)
└── marts (mart_bid_recommendations)
            │
            ▼
Python modeling layer
├── XGBoost (point estimate)
├── Quantile regression (prediction intervals)
├── SHAP (driver attribution)
└── A/B test designer (power, MDE, holdout)
            │
            ▼
Tableau dashboard (5 pages)
```

## Dashboard

The Tableau workbook has five pages, each answering one question a
real Strategy team would ask:

1. **Bid Recommendation Engine** — given a vehicle spec, what's the
   recommended max bid and the predicted GPU range?
2. **Bid Performance vs. Manheim MMR** — historical comparison of
   "we paid vs. market vs. eventual sale," surfacing systematic gaps.
3. **Segment Drivers** — which makes, models, regions, and age bands
   show the largest gaps between bid and realized GPU.
4. **A/B Test Designer** — interactive sample size, MDE, and runtime
   calculator for testing the bid model in production.
5. **Rollout Simulator** — Monte Carlo simulation of cumulative GPU
   lift under three rollout strategies (full launch, phased,
   holdout-only).

---

## Stack

| Layer | Tools |
|---|---|
| Ingestion | Python (requests, pandas), FRED API |
| Warehouse | DuckDB |
| Transformation | dbt |
| Modeling | scikit-learn, XGBoost, statsmodels (quantile regression), SHAP |
| Experimentation | Python (statsmodels, scipy.stats) |
| Visualization | Tableau |
| Version control | Git / GitHub |

---

## Roadmap

- [x] Project scope and architecture defined
- [x] Data sources identified and licensed
- [ ] Synthetic lifecycle generator (in progress)
- [ ] dbt project: staging and fact models
- [ ] XGBoost bid-price baseline
- [ ] Quantile regression for prediction intervals
- [ ] SHAP-driven segmentation analysis
- [ ] A/B test designer module
- [ ] Rollout simulator (Monte Carlo)
- [ ] Tableau workbook (5 pages)
- [ ] Executive summary memo (PDF)
- [ ] 3-minute walkthrough video

Target launch: end of June 2026.

---

## Limitations

A few things I want to be upfront about:

- **Synthetic downstream data.** Real Carvana data is not public. I
  anchored synthetic distributions to publicly reported financials, but
  the absolute dollar values are illustrative, not predictive. Relative
  comparisons (which segments overpay vs. underpay) are the defensible
  output.
- **No real bid history.** The Kaggle dataset captures auction sale
  prices, not the losing bids that would have been available. The bid
  model is therefore trained on transaction prices, not bid distributions.
- **Single-period model.** The current scope doesn't dynamically update
  bids based on real-time inventory pressure — a real production system
  would.

These are not blocking for the project's purpose (demonstrating analytical
judgment and method), but they're worth naming.

---

## About

Built by Shiva Ganapathy Ramamoorthy as part of a focused job search.
M.S. in Data Science, Analytics, and Engineering, Arizona State
University, May 2026.

LinkedIn: [linkedin.com/in/shiva-ganapathy-ramamoorthy](https://linkedin.com/in/shiva-ganapathy-ramamoorthy)
Email: sramamo7@asu.edu

---

*If you're on a Strategy, Analytics, or Acquisitions team in the
used-vehicle space and you'd like to share feedback on the approach,
I'd genuinely value the conversation.*
