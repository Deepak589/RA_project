# Roadmap

The RA Nutrition & Lifestyle App is being built in three phases. Each phase builds on the last: a rule-based logging foundation (V1), feedback-driven insight (V2), and finally personalized intelligence powered by **machine learning and deep learning** (V3).

> This roadmap describes product direction at a feature level. Week ranges are indicative and subject to change.

| Phase | Focus | Weeks |
|-------|-------|-------|
| **V1** | Rule-based recommendations + symptom tracking + analytics dashboard | 1–9 |
| **V2** | Feedback loops + trigger detection + personalized insights | 10–14 |
| **V3** | ML **& Deep Learning** personalization: flare-risk prediction + pain-score forecasting | 15–22+ |

> ⚠️ **Medical boundary:** This is a supportive lifestyle tool — not a diagnostic system and not a replacement for a rheumatologist or dietitian. The disclaimer is shown prominently throughout the app. See the [README](../README.md#medical-disclaimer).

---

## V1 — Rule-Based MVP (Weeks 1–9)

Build the working product: rule-based food recommendations, symptom and meal logging, and a weekly analytics dashboard. No ML yet.

### Week 1 — Problem Framing
- User stories for meal logging, symptom tracking, next-meal suggestions, and dashboard views
- Define the medical safety boundary: supportive lifestyle tool, not a diagnostic system
- Define what the app is **not** (no diagnosing, no replacing clinicians)
- List every MVP screen and API endpoint with acceptance criteria
- **Deliverable:** Requirements document + product flow diagram

### Week 2 — Database Design
- Full ER diagram: `users`, `foods`, `meals`, `meal_ingredients`, `daily_food_logs`, `symptom_logs`, `activity_logs`, `recommendation_logs`, `feedback_logs`
- Confirm stack: FastAPI (Python) + PostgreSQL + React
- Project repository, dev environment, and folder structure
- Alembic migration files for all initial tables
- **Deliverable:** ER diagram + repo scaffolding with migrations

### Week 3 — Nutrition Data Ingestion
- Register for the USDA FoodData Central API (free for low usage)
- Python script to pull and normalize food records (calories, protein, carbs, sugar, fiber, sodium, fat, omega-3)
- Load 500–1,000 common foods into the PostgreSQL `foods` table
- Build `/api/foods/search` with filters
- **Deliverable:** Food master dataset loaded + `/search` endpoint working

### Week 4 — Curated Meal Library
- Create 100–200 curated meals (breakfast, lunch, dinner, snacks)
- Tag each meal: high-protein, low-sugar, flare-friendly, vegetarian, budget-friendly, quick-prep, etc.
- Assign an anti-inflammatory score (0–10) to each meal
- Map each meal to its ingredients with gram-level portions
- **Deliverable:** `meals` + `meal_ingredients` tables seeded with 100–200 entries

### Week 5 — Rule Engine (Core Recommendation Logic)
- Meal scoring: bonuses for fiber, omega-3, lean protein, calcium/vit-D; penalties for sugar, sodium, saturated fat, ultra-processed foods
- Hard exclusion filters: allergy conflicts, preference flags (vegetarian, etc.)
- Daily balancing: e.g. "breakfast was low protein → boost protein-rich lunches"
- Flare-mode logic: prefer simple, easy-to-prepare, joint-friendly meals
- Per-recommendation explanation text: "Suggested because today's protein is low"
- **Deliverable:** Working `/api/recommend` endpoint with explanations

### Week 6 — Backend APIs
- Auth: `POST /register`, `POST /login`, JWT refresh
- Meal logs: `POST /logs/meals`, `GET /logs/meals/today`
- Symptom logs: `POST /logs/symptoms` (pain 0–10, fatigue, flare, stiffness, sleep)
- Profile + preferences: `GET/PUT /users/me`
- Dashboard summary: `GET /dashboard/weekly` (nutrient totals, pain avg, adherence)
- **Deliverable:** Full backend API, testable via FastAPI auto-docs at `/docs`

### Week 7 — Frontend Screens (React)
- Onboarding: name, age, weight, allergies, preferences, medications
- Home dashboard: today's recommendation card + quick-log buttons
- Meal log screen: food search, add meal, running daily nutrition totals
- Symptom screen: pain/fatigue/sleep sliders, flare toggle
- Recommendation card: name, score, explanation, accept/skip
- **Deliverable:** Usable UI prototype connected to the real API

### Week 8 — Analytics Dashboard
- Weekly trend charts: pain, fatigue, and meal-quality score over 7 days (Recharts)
- Adherence summary: % of recommendations accepted vs skipped
- Simple correlation highlights: "High-sugar days correlated with worse next-day pain"
- Top foods logged this week
- **Deliverable:** Analytics dashboard with charts and trend summaries

### Week 9 — Testing + MVP Release
- Edge cases: empty logs, brand-new users, full flare mode, allergy conflicts
- Manually review 20–30 recommendation outputs for quality
- Medical disclaimer banners + escalation prompts for severe symptoms
- Deploy backend (Render/Railway) and frontend (Vercel/Netlify)
- **Deliverable:** Stable MVP deployed and live — **end of V1**

---

## V2 — Analytics & Feedback (Weeks 10–14)

Collect real user logs, surface meaningful patterns and correlations, and make recommendations smarter using feedback — still no ML.

### Week 10 — User Data Collection & Feedback Loops
- Log skip/accept feedback on every recommendation (with an optional "why I skipped" note)
- Improve logging UX: fewer taps per meal, quick-add shortcuts
- Begin accumulating 90–180 daily logs per user — **this is the ML/DL fuel**
- Track consistently-skipped meals to build per-user penalties
- **Deliverable:** Growing longitudinal dataset + behavior-aware scoring

### Week 11 — Feedback-Aware Recommendation Improvement
- Penalize consistently-skipped foods per user
- Boost accepted meal types per user
- Add a "rarely eaten" penalty so ignored meals stop reappearing
- **Deliverable:** Per-user feedback-weighted recommendation engine

### Week 12 — Trigger Detection & Personalized Insights
- 3-day sugar average vs next-day pain correlation
- Sleep hours vs next-day fatigue correlation
- Processed-food days vs next-day symptom severity
- Weekly "Patterns we noticed" dashboard card
- Example: "On days after poor sleep, your pain averages 2 pts higher"
- **Deliverable:** Personalized weekly insights card in the app

### Weeks 13–14 — Seasonal Adjustment & V2 Polish
- Seasonal meal adjustment: lighter meals in summer, warming meals in winter
- Export weekly summary as PDF (useful for appointments)
- UX improvements from real user feedback
- Data-quality audit ahead of V3: missing values, label consistency
- **Deliverable:** V2 stable + an ML/DL-ready dataset beginning to form

---

## V3 — ML & Deep Learning Personalization (Weeks 15–22+)

Once a user has 90–180 daily logs, layer in **personalized intelligence**. V3 combines interpretable classical machine learning with deep learning sequence models to forecast pain scores and predict flare risk. The two families are evaluated head-to-head, and the app only ships whichever meaningfully outperforms the rule-based baseline.

> Deep learning is added *because the data is sequential*: each user produces a daily time series of meals, symptoms, sleep, and activity. Temporal models (LSTM/GRU/Temporal Convolutional Networks) are well suited to learning these multi-day patterns, while classical ML (XGBoost, logistic regression) provides a strong, interpretable baseline and a fallback when per-user data is still sparse.

### Week 15 — ML & DL Dataset Preparation
- Clean missing values in symptom and meal logs (impute or drop)
- Engineer lag/window features: 3-day sugar average, last night's sleep, yesterday's steps, flares in the last 7 days
- Build **sequence windows** for deep learning: rolling N-day tensors of meal, symptom, sleep, and activity features
- Define targets: tomorrow's pain score (regression) and tomorrow's flare (binary classification)
- Time-aware train/validation/test split — no leakage across time
- Requirement: at least 90–180 daily logs per active user before training
- **Deliverable:** ML-ready tabular features **and** DL-ready sequence tensors

### Weeks 16–17 — Baseline ML Models
- Logistic regression for flare risk (start simple)
- Random forest / XGBoost for pain-score regression
- Evaluate: MAE and RMSE for pain, F1 + ROC-AUC for flare
- Feature importance for interpretability: "Recent sleep is the strongest predictor"
- Compare against the rule-based baseline
- **Deliverable:** Classical ML baseline + evaluation report

### Weeks 18–19 — Deep Learning Sequence Models
- Build temporal models on the sequence tensors: **LSTM/GRU** (and a **Temporal Convolutional Network** as an alternative) for pain-score forecasting and flare classification
- Tooling: **PyTorch** (or TensorFlow/Keras), with early stopping, dropout, and regularization to fight overfitting on small per-user histories
- Handle short histories gracefully: per-user fine-tuning on top of a global model, plus graceful fallback to the XGBoost baseline when data is sparse
- Add interpretability: attention weights / SHAP-style attributions so predictions remain explainable
- Evaluate with the **same metrics and time-aware splits** as the ML baseline for an apples-to-apples comparison
- **Deliverable:** Trained DL forecasting models + a head-to-head ML-vs-DL comparison report

### Weeks 20–22+ — Model Selection, Integration & Monitoring
- Select the winning model per task (ML or DL) based on accuracy, latency, and data requirements — **only ship if it meaningfully beats the rule-based baseline**
- Serve the chosen model behind FastAPI: `POST /predict/flare-risk`, `POST /predict/pain`
- "Tomorrow looks like a higher-risk day" UI card, with the reason shown
- Use predictions to steer suggestions: on high-risk days, prioritize anti-inflammatory, easy-prep meals
- Model monitoring: track live prediction accuracy, detect drift, and retrain periodically
- Keep the medical disclaimer prominent — predictions are supportive, **not** clinical
- **Deliverable:** Live personalized flare/pain prediction integrated in the app — **end of V3**

---

## Updated Tech Stack for V3

| Layer | Technology |
|-------|------------|
| Feature engineering | **pandas**, **NumPy** |
| Classical ML | **scikit-learn**, **XGBoost** |
| Deep learning | **PyTorch** (LSTM / GRU / TCN); TensorFlow/Keras as an alternative |
| Interpretability | feature importance, **SHAP**, attention attributions |
| Serving | model exposed via existing **FastAPI** prediction endpoints |
| Monitoring | accuracy tracking, drift detection, scheduled retraining |

---

## Key Reminders

- **Don't add V3 until there are 90–180 daily logs per active user.** Sparse data makes deep learning look impressive in demos but perform poorly in practice.
- The `recommendation_logs` table (what was shown, accepted, skipped, and why) is critical — set it up in Week 2 and never skip logging it.
- The curated meal library (Week 4) is the hardest manual task; build an admin UI early.
- Use USDA FoodData Central's bulk CSV for Week 3 — faster than per-food API calls.
- **Interpretability is non-negotiable.** A deep model is only acceptable here if its predictions can still be explained to the user.

---

> ⚠️ All features remain **non-clinical lifestyle support**. The app does not provide medical advice, diagnosis, or treatment — see the Medical Disclaimer in the [README](../README.md#medical-disclaimer). Always consult a rheumatologist or dietitian for medical nutrition issues.
