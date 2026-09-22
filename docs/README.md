# RA Nutrition & Lifestyle App

> A non-clinical lifestyle support tool that helps people living with rheumatoid arthritis (RA) build healthier daily habits through meal logging, symptom tracking, and gentle, rule-based guidance.

The RA Nutrition & Lifestyle App is designed to support — not replace — the relationship between a person and their healthcare team. It focuses on the everyday: what you eat, how you feel, and the patterns that connect the two over time. By making logging effortless and surfacing simple, transparent insights, it helps users notice trends and make small, sustainable adjustments to their routine.

> ⚠️ **This is not a medical device and does not provide medical advice.** See the [Medical Disclaimer](#medical-disclaimer) below.

---

## ✨ Key Features

- **Meal Logging** — Quickly record meals and individual foods, with a searchable food library and reusable meal templates.
- **Symptom Tracking** — Log RA-related symptoms (pain, stiffness, fatigue, flares) on a daily basis to build a personal history.
- **Rule-Based Recommendations** — Transparent, non-clinical suggestions generated from simple, explainable rules — never a black box.
- **Weekly Analytics** — Clear visual summaries of meals, symptoms, and trends so users can spot patterns at a glance.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | **FastAPI** (Python) |
| Database | **PostgreSQL** |
| Frontend | **React** + **Vite** |
| Styling | **Tailwind CSS** |
| Data fetching / state | **React Query** |
| Charts | **Recharts** |
| ML / Deep Learning *(V3)* | **scikit-learn**, **XGBoost**, **PyTorch** (LSTM / GRU / TCN) |

---

## 🗺 Roadmap

A condensed view — see [`docs/roadmap.md`](docs/roadmap.md) for the full week-by-week breakdown.

- **V1 — Rule-Based Foundation:** Meal logging, symptom tracking, the food library, transparent rule-based recommendations, and a weekly analytics dashboard.
- **V2 — Insight & Feedback:** Feedback loops, per-user recommendation tuning, trigger detection, and personalized weekly insights — all without ML.
- **V3 — ML & Deep Learning Personalization:** Once enough daily logs accumulate, add personalized **flare-risk prediction** and **pain-score forecasting** — combining interpretable classical ML (scikit-learn, XGBoost) with deep learning sequence models (LSTM/GRU/TCN in PyTorch), shipped only where they beat the rule-based baseline.

---

## 📸 Screenshots

> _Screenshots coming soon._

| Dashboard | Meal Logging | Weekly Analytics |
|-----------|--------------|------------------|
| _placeholder_ | _placeholder_ | _placeholder_ |

---

## 🔗 Live Demo

> _Live demo link coming soon._

---

## 🏗 Architecture

For a high-level overview of the system design, database schemas, and API structure, see [`docs/architecture.md`](docs/architecture.md).

### Workflows & Data Model

Visual walkthroughs (Mermaid diagrams that render directly on GitHub):

- **[`docs/workflows.md`](docs/workflows.md)** — end-to-end journeys: authentication & token refresh, meal logging, the custom meal builder, the recommendation flow, symptom escalation, weekly analytics, and the V3 prediction flow.
- **[`docs/er-diagram.md`](docs/er-diagram.md)** — the full entity-relationship diagram and the four logical database schemas (`core`, `static`, `tracking`, `intelligence`).

---

## 📚 Documentation

| Doc | What's inside |
|-----|---------------|
| [Architecture](docs/architecture.md) | System design, tiers, API structure, intelligence tier (V3) |
| [Workflows](docs/workflows.md) | Sequence & flow diagrams for every core user journey |
| [ER Diagram](docs/er-diagram.md) | Data model, entities, relationships, schema grouping |
| [Roadmap](docs/roadmap.md) | Week-by-week build plan across V1 → V3 |

---

## ⚕️ Medical Disclaimer

The RA Nutrition & Lifestyle App is a **lifestyle and wellness support tool only**. It is **not a medical device** and does **not** provide medical, diagnostic, or treatment advice.

- Nothing in this application should be interpreted as a substitute for professional medical advice, diagnosis, or treatment.
- Always seek the guidance of a qualified physician or other healthcare provider with any questions about a medical condition, medication, diet, or treatment plan.
- The recommendations provided are general, rule-based lifestyle suggestions and are **not** personalized clinical guidance.
- Never disregard professional medical advice or delay seeking it because of something you read or logged in this app.
- In a medical emergency, contact your local emergency services immediately.

Use of this application is at your own discretion and risk.
