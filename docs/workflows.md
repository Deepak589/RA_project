# Workflows

End-to-end walkthroughs of the core user journeys, expressed as [Mermaid](https://mermaid.js.org/) diagrams that render natively on GitHub. Each diagram describes the **flow of control and data** between the React client, the FastAPI backend, PostgreSQL, and (in V3) the intelligence tier.

> These describe *shape and sequence* only. Scoring math and rule-engine internals are intentionally omitted, and nothing here constitutes clinical logic. See the **Medical Disclaimer** in the [README](../README.md).

**Contents**

1. [System Overview](#1-system-overview)
2. [Authentication & Token Refresh](#2-authentication--token-refresh)
3. [Meal Logging](#3-meal-logging)
4. [Custom Meal Builder](#4-custom-meal-builder)
5. [Recommendation Flow](#5-recommendation-flow)
6. [Symptom Logging & Medical Escalation](#6-symptom-logging--medical-escalation)
7. [Weekly Analytics](#7-weekly-analytics)
8. [Prediction Flow (V3)](#8-prediction-flow-v3)

---

## 1. System Overview

How a request travels through the tiers. The frontend never touches the database directly — the backend is the single source of truth.

```mermaid
flowchart LR
  subgraph Client["Frontend - React + Vite"]
    UI[UI Components]
    RQ[React Query cache]
  end

  subgraph API["Backend - FastAPI"]
    R[Routers / HTTP layer]
    S[Services / business logic]
    M[Models / ORM]
  end

  DB[(PostgreSQL<br/>core · static · tracking · intelligence)]
  IT[["Intelligence Tier<br/>ML / DL inference (V3)"]]

  UI -->|HTTPS / JSON| R
  R --> RQ
  R --> S
  S --> M
  M -->|SQL| DB
  S -.->|features / predict| IT
  IT -.->|forecast| S
```

---

## 2. Authentication & Token Refresh

Access tokens are held in memory (never `localStorage`). On a `401`, the client transparently refreshes and retries. Refresh tokens are rotated, so a reused token is rejected.

```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant FE as Frontend
  participant API as FastAPI
  participant DB as PostgreSQL

  U->>FE: Enter credentials
  FE->>API: POST /auth/login
  API->>DB: Verify password hash
  API->>DB: Store refresh_token_hash (authentication_sessions)
  API-->>FE: access_token + refresh_token + user

  Note over FE: Tokens kept in memory only

  FE->>API: GET /dashboard/today (Bearer access_token)
  API-->>FE: 401 Unauthorized (expired)

  FE->>API: POST /auth/refresh (refresh_token)
  API->>DB: Validate + rotate session
  alt Refresh valid
    API-->>FE: New access_token + refresh_token
    FE->>API: Retry original request
    API-->>FE: 200 OK
  else Reused / expired token
    API-->>FE: 401 Unauthorized
    FE->>U: Redirect to login
  end
```

---

## 3. Meal Logging

A logged item may be a library food, a curated meal, or free-text — all land in `food_logs` and immediately update the day's nutrition summary.

```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant FE as Frontend
  participant API as FastAPI
  participant DB as PostgreSQL

  U->>FE: Search food / pick meal
  FE->>API: GET /foods/search?q=...
  API->>DB: Query static.foods
  API-->>FE: Matching foods

  U->>FE: Confirm portion + meal type
  FE->>API: POST /logs/food (FoodLogCreate)
  API->>DB: Insert tracking.food_logs
  API-->>FE: FoodLogResponse

  FE->>API: GET /logs/food/today
  API->>DB: Aggregate today's logs
  API-->>FE: items + nutrition_summary
  FE->>U: Updated daily totals
```

---

## 4. Custom Meal Builder

Users assemble a meal from ingredients. `calculate` previews nutrition with **no DB write**; saving persists it. Unknown ingredients are captured for later curation.

```mermaid
flowchart TD
  A[Add ingredients + portions] --> B[POST /meals/custom/calculate]
  B --> C{All ingredients<br/>found?}
  C -->|Yes| D[Preview nutrition<br/>no DB write]
  C -->|No| E[Exclude missing from score]
  E --> F[POST /ingredients/missing<br/>report for curation]
  D --> G{Save meal?}
  F --> G
  G -->|Yes| H[POST /meals/custom<br/>persist CustomMeal]
  G -->|No| I[Discard]
  H --> J[Available for logging + recommendations]
```

---

## 5. Recommendation Flow

The backend assembles context (preferences, recent logs, flare state), runs the transparent rule engine, returns a primary pick plus alternatives **with an explanation**, and records what was shown for feedback.

```mermaid
sequenceDiagram
  autonumber
  participant FE as Frontend
  participant API as FastAPI
  participant SVC as Recommendation Service
  participant DB as PostgreSQL

  FE->>API: GET /recommendations/next?meal_type&flare_active
  API->>SVC: Build context
  SVC->>DB: Load preferences + recent logs + curated meals
  Note over SVC: Rule engine selects + ranks<br/>(logic intentionally opaque here)
  SVC->>DB: Insert intelligence.recommendation_logs (shown)
  SVC-->>API: primary + alternatives + explanation + rule_applied
  API-->>FE: Recommendation payload

  FE->>API: POST /recommendations/{id}/feedback<br/>(accepted | skipped | replaced)
  API->>DB: Update feedback_status / replacement
  API-->>FE: { status: ok }
```

---

## 6. Symptom Logging & Medical Escalation

The hard boundary in the product. Severe symptom entries trip an escalation flag and return a message directing the user to their clinician — the app never diagnoses or advises.

```mermaid
flowchart TD
  A[User logs symptoms<br/>pain / fatigue / stiffness / swelling] --> B[POST /logs/symptoms]
  B --> C[Insert tracking.symptom_logs]
  C --> D{Severity threshold<br/>crossed?}
  D -->|No| E[Return SymptomLogResponse]
  D -->|Yes| F[escalation_triggered = true]
  F --> G[Return escalation_message:<br/>'contact your rheumatologist /<br/>seek medical advice']
  G --> H[Frontend surfaces medical-boundary banner]
  E --> I[Feed into dashboard + trends]
  H --> I
```

---

## 7. Weekly Analytics

Read-only aggregation that powers the trends dashboard — joining meal, symptom, and lifestyle history into a single weekly view.

```mermaid
sequenceDiagram
  autonumber
  participant FE as Frontend
  participant API as FastAPI
  participant DB as PostgreSQL

  FE->>API: GET /dashboard/weekly
  API->>DB: Aggregate food_logs (nutrition)
  API->>DB: Aggregate symptom_logs (pain / flare trend)
  API->>DB: Aggregate lifestyle_logs (sleep / steps / water)
  API-->>FE: Weekly trend summary
  FE->>FE: Render charts (Recharts)
```

---

## 8. Prediction Flow (V3)

The additive intelligence tier. Once a user has enough history, the backend requests a forecast; predictions **augment** rule-based guidance and fall back to the baseline when data is sparse. They never replace the transparent recommendations.

```mermaid
sequenceDiagram
  autonumber
  participant FE as Frontend
  participant API as FastAPI
  participant SVC as Prediction Service
  participant IT as Intelligence Tier
  participant DB as PostgreSQL

  FE->>API: POST /predict/flare-risk
  API->>SVC: Request forecast
  SVC->>DB: Read tracking + static history
  alt Enough history
    SVC->>IT: Assemble features + sequences
    IT->>IT: Select best model<br/>(classical ML / LSTM / GRU / TCN)
    IT-->>SVC: Forecast + confidence
    SVC->>DB: Write intelligence schema (derived)
    SVC-->>API: Prediction
  else Sparse data
    SVC-->>API: Fall back to rule-based baseline
  end
  API-->>FE: Forecast (augments recommendations)
```

---

## Legend

| Notation | Meaning |
|----------|---------|
| `solid arrow` | Synchronous request / response |
| `dotted arrow` | V3 intelligence-tier call (additive, optional) |
| `alt / else` | Branching on a runtime condition |
| `[(cylinder)]` | Persistent store (PostgreSQL) |
| `[[subroutine]]` | External / pluggable tier |
