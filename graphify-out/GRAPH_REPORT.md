# Graph Report - RA_project  (2026-05-16)

## Corpus Check
- 148 files · ~88,898 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 873 nodes · 1832 edges · 31 communities detected
- Extraction: 60% EXTRACTED · 40% INFERRED · 0% AMBIGUOUS · INFERRED: 739 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 40|Community 40]]

## God Nodes (most connected - your core abstractions)
1. `Meal` - 72 edges
2. `Select()` - 53 edges
3. `Food` - 50 edges
4. `RecommendationLog` - 37 edges
5. `DailyNutritionState` - 29 edges
6. `get_next_meal_recommendation()` - 28 edges
7. `NutritionGaps` - 24 edges
8. `main()` - 24 edges
9. `FoodLog` - 23 edges
10. `normalize_usda_food()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `V3 ML` --semantically_similar_to--> `V3 ML Personalization (Weeks 15-20+)`  [INFERRED] [semantically similar]
  week1_requirements.md → RA_App_Project_Roadmap.pdf
- `V1 Rule-Based MVP` --semantically_similar_to--> `V1 Rule-Based MVP (Weeks 1-9)`  [INFERRED] [semantically similar]
  week1_requirements.md → RA_App_Project_Roadmap.pdf
- `V2 Analytics` --semantically_similar_to--> `V2 Analytics & Feedback (Weeks 10-14)`  [INFERRED] [semantically similar]
  week1_requirements.md → RA_App_Project_Roadmap.pdf
- `Non-clinical wellness boundary` --semantically_similar_to--> `Supportive lifestyle tool boundary`  [INFERRED] [semantically similar]
  week1_requirements.md → RA_App_Project_Roadmap.pdf
- `Weekly analytics dashboard` --semantically_similar_to--> `Week 8 - Analytics Dashboard`  [INFERRED] [semantically similar]
  week1_requirements.md → RA_App_Project_Roadmap.pdf

## Hyperedges (group relationships)
- **V1 problem framing and delivery scope** — week1_requirements_v1_rule_based_mvp, roadmap_pdf_v1_rule_based_mvp, roadmap_pdf_week1_problem_framing [INFERRED 0.85]
- **V3 ML readiness gate** — week1_requirements_v3_ml, roadmap_pdf_v3_ml_personalization, roadmap_pdf_v3_data_threshold_90_180_daily_logs [INFERRED 0.90]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (78): Base, Base, TodayDashboard, WeeklyDashboard, DeclarativeBase, AccountDeletionStatus, MissingIngredientStatus, Food (+70 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (79): BaseModel, get_today_dashboard_endpoint(), TodayDashboardResponse, WeeklyDashboardResponse, Enum, FlareLevel, MealType, RecommendationFeedbackStatus (+71 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (72): refresh(), get_weekly_dashboard_endpoint(), _avg(), detect_meal_type_by_time(), generate_weekly_insights(), get_today_dashboard(), get_weekly_dashboard(), create_food_log() (+64 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (58): CustomMealCalculateRequest, CustomMealCreateRequest, CustomMealIngredientInput, CustomMealIngredientResponse, CustomMealListResponse, CustomMealNutrients, CustomMealResponse, _build_tags() (+50 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (34): AnalyticsPage(), weekLabel(), App(), PrivateRoute(), CustomMealLogItem(), CustomMealPage(), DashboardPage(), hasRealDietPreference() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (38): calculate_anti_inflammatory_score(), _decimal_attr(), fetch_fish_candidates(), is_target_fish(), _json_decimal(), main(), _now_iso(), save_report() (+30 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (39): apply_animal_guard(), build_food_lookup(), calculate_meal_score(), calculate_totals(), _food_to_ns(), _is_animal_food(), main(), resolve_food() (+31 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (22): change_password(), _issue_tokens(), _load_user(), login(), logout(), register(), update_me(), _build_token() (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (29): result_context(), best_match(), build_lookup(), build_meal(), build_tags(), calculate_meal_score(), calculate_totals(), is_vegetarian() (+21 more)

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (25): Graphify Extraction Instructions, Curated meal library, React + Vite / FastAPI / PostgreSQL stack, recommendation_logs table, Rule-based baseline comparison, Sparse data makes ML look impressive but perform poorly, Supportive lifestyle tool boundary, USDA FoodData Central API (+17 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (19): MealSearchResponse, _apply_meal_filters(), get_flare_safe_meals(), get_meal_by_id(), get_meals(), get_meals_by_tag(), get_flare_safe_meals_endpoint(), get_meal_endpoint() (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (19): _clean_text(), _extract_nutrient_id(), _extract_nutrients(), _extract_serving_size_g(), map_usda_category(), normalize_usda_food(), _to_decimal(), _to_int() (+11 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (16): FoodBase, FoodCreate, FoodSearchResponse, MealBase, MealCreate, MealItemBase, MealItemCreate, MealItemResponse (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (7): _meal_matches_dietary_flags(), _meal(), test_non_vegetarian_flag_excludes_vegan_tagged_meal(), test_non_vegetarian_flag_excludes_vegetarian_meal(), test_non_vegetarian_flag_keeps_meat_meal(), test_vegetarian_flag_excludes_non_vegetarian_meal(), test_vegetarian_flag_keeps_vegetarian_meal()

### Community 14 - "Community 14"
Cohesion: 0.3
Nodes (13): apply_medication_filter(), _bump(), _current_score(), _meal_has_any(), MedicationFilterResult, _number(), _meal(), test_corticosteroids_boost_high_protein_meals() (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.37
Nodes (13): _call(), _make_db_mock(), _meal(), _no_gaps(), _no_prefs(), _prefs_with_flags(), test_D1_non_veg_override_returns_non_veg_meal(), test_D2_veg_override_returns_veg_meal() (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (9): delete_medication(), get_profile(), post_medication(), put_preferences(), add_medication(), get_full_profile(), remove_medication(), update_preferences() (+1 more)

### Community 17 - "Community 17"
Cohesion: 0.47
Nodes (8): _auth_headers(), test_login_sets_refresh_cookie(), test_patch_symptoms_today_creates_log_when_missing(), test_patch_symptoms_today_sets_escalation_when_pain_is_high(), test_patch_symptoms_today_updates_existing_log(), test_refresh_accepts_cookie_and_rotates_refresh_session(), test_register_duplicate_email_returns_structured_409(), _unique_email()

### Community 19 - "Community 19"
Cohesion: 0.46
Nodes (7): _display_note(), _factor_for(), _json_decimal(), main(), _now_iso(), _save_report(), _state_for()

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (1): Service layer package.

### Community 21 - "Community 21"
Cohesion: 0.33
Nodes (3): BaseSettings, get_settings(), Settings

### Community 22 - "Community 22"
Cohesion: 0.47
Nodes (5): downgrade(), _extend_static_meals(), meal library and food metadata  Revision ID: 0004_meal_library Revises: 0003_foo, _remove_static_meal_columns(), upgrade()

### Community 23 - "Community 23"
Cohesion: 0.4
Nodes (3): AuthProvider(), configureApiAuth(), configureApiToken()

### Community 26 - "Community 26"
Cohesion: 0.5
Nodes (1): initial schema  Revision ID: 0001_initial_schema Revises: Create Date: 2026-04-1

### Community 27 - "Community 27"
Cohesion: 0.5
Nodes (1): add food nutrition scoring fields  Revision ID: 0002_food_score Revises: 0001_in

### Community 28 - "Community 28"
Cohesion: 0.5
Nodes (1): set food external source default to usda  Revision ID: 0003_food_source Revises:

### Community 29 - "Community 29"
Cohesion: 0.5
Nodes (1): food log enhancements and week 5 tracking fields  Revision ID: 0005_food_log_enh

### Community 30 - "Community 30"
Cohesion: 0.5
Nodes (1): missing ingredients and week 6 fixes  Revision ID: 0006_missing_ingredients Revi

### Community 31 - "Community 31"
Cohesion: 0.5
Nodes (1): add user role  Revision ID: 0007_add_user_role Revises: 0006_missing_ingredients

### Community 32 - "Community 32"
Cohesion: 0.5
Nodes (1): add_missing_tables  Revision ID: 2dddb02d5f05 Revises: 0007_add_user_role Create

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (2): isEmail(), validateRegister()

## Knowledge Gaps
- **21 isolated node(s):** `initial schema  Revision ID: 0001_initial_schema Revises: Create Date: 2026-04-1`, `add food nutrition scoring fields  Revision ID: 0002_food_score Revises: 0001_in`, `set food external source default to usda  Revision ID: 0003_food_source Revises:`, `meal library and food metadata  Revision ID: 0004_meal_library Revises: 0003_foo`, `food log enhancements and week 5 tracking fields  Revision ID: 0005_food_log_enh` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 20`** (7 nodes): `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`, `Service layer package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (4 nodes): `downgrade()`, `initial schema  Revision ID: 0001_initial_schema Revises: Create Date: 2026-04-1`, `upgrade()`, `0001_initial_schema.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (4 nodes): `downgrade()`, `add food nutrition scoring fields  Revision ID: 0002_food_score Revises: 0001_in`, `upgrade()`, `0002_add_food_nutrition_scoring_fields.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (4 nodes): `downgrade()`, `set food external source default to usda  Revision ID: 0003_food_source Revises:`, `upgrade()`, `0003_set_food_external_source_default.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (4 nodes): `downgrade()`, `food log enhancements and week 5 tracking fields  Revision ID: 0005_food_log_enh`, `upgrade()`, `0005_food_log_enhancements.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (4 nodes): `downgrade()`, `missing ingredients and week 6 fixes  Revision ID: 0006_missing_ingredients Revi`, `upgrade()`, `0006_missing_ingredients_and_fixes.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (4 nodes): `downgrade()`, `add user role  Revision ID: 0007_add_user_role Revises: 0006_missing_ingredients`, `upgrade()`, `0007_add_user_role.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (4 nodes): `downgrade()`, `add_missing_tables  Revision ID: 2dddb02d5f05 Revises: 0007_add_user_role Create`, `upgrade()`, `2dddb02d5f05_add_missing_tables.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (3 nodes): `validators.js`, `isEmail()`, `validateRegister()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Select()` connect `Community 2` to `Community 1`, `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 12`, `Community 16`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `Meal` connect `Community 0` to `Community 3`, `Community 6`, `Community 8`, `Community 13`, `Community 14`, `Community 15`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `get_next_meal_recommendation()` connect `Community 2` to `Community 0`, `Community 3`, `Community 8`, `Community 14`, `Community 15`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `Meal` (e.g. with `Food` and `MealItem`) actually correct?**
  _`Meal` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `Select()` (e.g. with `require_current_user()` and `_load_user()`) actually correct?**
  _`Select()` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Food` (e.g. with `Base` and `FoodLog`) actually correct?**
  _`Food` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `str` (e.g. with `require_current_user_id()` and `create_access_token()`) actually correct?**
  _`str` has 42 INFERRED edges - model-reasoned connections that need verification._