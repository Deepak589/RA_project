# Architecture

A high-level overview of how the RA Nutrition & Lifestyle App is structured. This document intentionally describes the system at a conceptual level and **does not** cover scoring logic or the internal rule engine.

---

## System Design

The application follows a conventional three-tier architecture with a clear separation between the client, the API, and persistent storage.

```
┌─────────────────────┐        HTTPS / JSON        ┌─────────────────────┐
│      Frontend       │ ─────────────────────────▶ │       Backend       │
│  React + Vite       │                            │      FastAPI        │
│  Tailwind CSS       │ ◀───────────────────────── │   (Python, REST)    │
│  React Query        │        JSON responses      │                     │
└─────────────────────┘                            └─────┬─────────┬─────┘
                                                          │ SQL     │ predict
                                                          ▼         ▼
                                          ┌─────────────────┐  ┌──────────────────────┐
                                          │   PostgreSQL    │  │  Intelligence Tier    │
                                          │ (logical schemas)│ │  ML / DL inference    │
                                          └─────────────────┘  │  (V3)                 │
                                                               └──────────────────────┘
```

The first two tiers (V1/V2) are the rule-based system. The **intelligence tier** is introduced in V3 and is described separately below; it is an additive layer, not a rewrite of the existing tiers.

### Frontend
A single-page application built with **React** and **Vite**, styled with **Tailwind CSS**. **React Query** manages server state — caching, background refetching, and synchronization with the API. The frontend communicates exclusively through the backend's REST API and holds no direct database access.

### Backend
A **FastAPI** service exposing a JSON REST API. It is responsible for authentication, request validation, business logic, and persistence. The backend is the single source of truth for all data operations and is the only tier permitted to talk to the database.

### Database
A **PostgreSQL** instance organized into logical schemas (see below). Schema changes are managed through versioned migrations rather than ad-hoc DDL.

### Intelligence Tier (V3)
A prediction layer that the backend calls to produce personalized forecasts — **flare-risk** and **pain-score** predictions. It combines interpretable classical machine learning with deep learning sequence models, and is described in more detail in [Intelligence Tier (V3)](#intelligence-tier-v3-1) below. In V1/V2 this tier is absent and all guidance comes from the rule engine; in V3 it augments — but never replaces — the rule-based recommendations.

---

## Database Schema Overview

Data is organized into four logical schemas, each with a distinct responsibility:

| Schema | Responsibility |
|--------|----------------|
| **core** | Foundational entities such as users and accounts. |
| **static** | Reference and lookup data that changes infrequently (e.g. the food library). |
| **tracking** | Time-series user activity such as meal logs and symptom entries. |
| **intelligence** | Derived data supporting recommendations and analytics. |

> Only schema names and responsibilities are described here. Table-level details, scoring fields, and rule-engine internals are intentionally omitted.

---

## API Structure

The API is organized into resource-oriented route groups, each backed by a service layer that encapsulates business logic. Endpoints follow REST conventions and exchange JSON.

```
┌──────────────────────────────────────────────┐
│                  FastAPI App                   │
├──────────────────────────────────────────────┤
│  Routers (HTTP layer)                          │
│    • Auth & users                              │
│    • Foods & meal library                      │
│    • Meal logging                              │
│    • Symptom tracking                          │
│    • Recommendations                           │
│    • Analytics                                 │
│    • Predictions (V3)                           │
├──────────────────────────────────────────────┤
│  Services (business logic)                     │
│    • Prediction service (V3) ───┐               │
├─────────────────────────────────┼─────────────┤
│  Models / persistence (PostgreSQL)             │
└─────────────────────────────────┼─────────────┘
                                  ▼
                       ┌──────────────────────┐
                       │  Intelligence tier    │
                       │  (V3 ML / DL models)  │
                       └──────────────────────┘
```

- **Routers** handle HTTP concerns: request parsing, validation, and response shaping. The V3 *Predictions* router exposes endpoints such as `POST /predict/flare-risk` and `POST /predict/pain`.
- **Services** contain the business logic and orchestrate persistence. The V3 *prediction service* assembles features and delegates inference to the intelligence tier.
- **Models** map to the logical schemas described above.

This layering keeps the HTTP surface thin and the business logic testable and independent of transport details.

---

## Intelligence Tier (V3)

The intelligence tier is the V3 personalization layer. It turns a user's accumulated history into forward-looking forecasts and feeds them back into the recommendation experience. It is conceptually separate from the rule engine and is only active once a user has enough logged history.

```
┌──────────────────────────────────────────────────────────┐
│                     Intelligence Tier                      │
├──────────────────────────────────────────────────────────┤
│  Feature assembly                                          │
│    • tabular lag/window features                           │
│    • sequence tensors (for temporal models)                │
├──────────────────────────────────────────────────────────┤
│  Models                                                    │
│    • Classical ML  (scikit-learn, XGBoost)                 │
│    • Deep learning (PyTorch: LSTM / GRU / TCN)             │
├──────────────────────────────────────────────────────────┤
│  Selection & inference                                     │
│    • best-performing model per task, with baseline fallback│
├──────────────────────────────────────────────────────────┤
│  Monitoring                                                │
│    • accuracy tracking, drift detection, scheduled retrain │
└──────────────────────────────────────────────────────────┘
```

- **Feature assembly** reads from the `tracking` and `static` schemas to build two representations: tabular lag/window features for classical models and rolling sequence tensors for deep learning models.
- **Models** span two families. Classical ML provides an interpretable, low-data baseline; deep learning sequence models capture multi-day temporal patterns in the user's logs.
- **Selection & inference** picks the best-performing model per task (flare-risk, pain-score) and falls back to the classical baseline — or to the rule engine — when per-user data is sparse.
- **Monitoring** tracks live prediction accuracy, watches for drift, and triggers periodic retraining.

Predictions are written to the **intelligence** schema (derived data) and surfaced through the *Predictions* router. They **augment** the rule-based recommendations — for example, prioritizing anti-inflammatory, easy-prep meals on a predicted high-risk day — but never replace the transparent rule-based guidance, and never constitute clinical advice.

> Model internals, feature definitions, and scoring logic are intentionally omitted here; this document describes only the conceptual shape of the tier.
