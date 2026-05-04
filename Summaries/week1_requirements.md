# Week 1 Requirements Document

## 1. Executive Summary

This app is a non-clinical lifestyle support tool for adults living with Rheumatoid Arthritis (RA). Its purpose is to help users log meals, symptoms, and daily lifestyle factors, then recommend a practical next meal using transparent nutrition rules. The product is designed for adults who want help noticing patterns, building steadier routines, and making food choices that align with anti-inflammatory guidance without replacing medical care.

The V1 product focuses on a rule-based MVP built with FastAPI, PostgreSQL, and a later React frontend. It will support onboarding, food search, meal logging, symptom and lifestyle tracking, next-meal recommendations, simple weekly trends, and clear safety messaging. V2 will add richer analytics and trigger exploration. V3 may add ML-based flare and pain risk estimation, but only after enough real-world data and clinical review.

This product matters because RA symptoms are daily, variable, and exhausting to manage. Users often face fatigue, stiffness, pain, decision overload, and uncertainty about which foods or routines actually help. The app should reduce friction, provide small practical actions, and stay within a strict wellness boundary.

## 2. User and Clinical Context

### Task 1 Research Findings

1. Common daily pain points and frustrations

- RA patients commonly deal with morning stiffness, fatigue, pain variability, reduced grip strength, and the unpredictability of flares, which makes meal planning and routine tracking hard.
- NHS guidance emphasizes keeping active, pacing activity, and balancing rest with movement, which implies the app should avoid all-or-nothing behavior and support low-effort logging.
- NIAMS describes RA as a long-term inflammatory disease with pain, swelling, stiffness, fatigue, and reduced function, reinforcing that users may have limited energy for complex workflows.
- Patient discussions on Reddit commonly mention wanting help identifying food triggers without having to maintain a burdensome diary and frustration with apps that feel generic, overly clinical, or high-effort.

2. Foods and nutrients associated with lower inflammation vs triggers

- Arthritis Foundation guidance most consistently supports Mediterranean-style eating patterns: fatty fish, olive oil, fruits, vegetables, legumes, nuts, seeds, and whole grains.
- Omega-3 fats, fiber-rich foods, and antioxidant-rich produce are commonly presented as supportive choices.
- Clinical and public guidance does not support one universal RA diet. Elimination-style claims are often patient-specific rather than broadly proven.
- Commonly reported triggers in patient communities include highly processed foods, excess added sugar, fried foods, alcohol, and foods unique to the individual. Some users also self-report issues with dairy or gluten, but these are not universal clinical rules.

3. Current clinical guidance on diet, exercise, sleep, and flare management

- NHS states there is no strong evidence that specific dietary changes can cure RA, though a healthy balanced diet is recommended.
- ACR guidance strongly supports exercise and rehabilitation as part of RA care, which supports tracking activity and encouraging realistic movement goals.
- NIAMS and NHS both frame RA management as medication plus self-management behaviors such as movement, rest, stress management, and joint protection.
- Sleep and fatigue management matter because poor sleep can worsen coping, pain burden, and daily adherence, even when not presented as a standalone RA treatment.

4. Existing apps and what users love or hate

- Existing options include symptom trackers, arthritis community tools, generic food logs, and chronic illness trackers rather than one dominant RA meal-and-symptom app.
- Positive sentiment clusters around simple logging, visible trends, symptom history for appointments, and reminders.
- Negative sentiment clusters around too many taps, weak personalization, poor explanations, generic food advice, paywalls, and tools that do not reflect flare-day reality.

5. Safety boundaries for a non-clinical lifestyle app

- The app must never diagnose RA, predict medication response, tell users to start, stop, or change medication, or claim to treat or cure inflammation.
- The app must never present meal recommendations as medical advice or imply a food cause is proven from limited self-tracked data.
- The app should escalate users toward professional care when symptoms are severe, unusual, or worsening.
- The app must clearly state that it is a supportive wellness tool and not a replacement for a rheumatologist, GP, or dietitian.

### User and Clinical Context Summary

Adults with RA manage a condition that is unpredictable, tiring, and highly individualized. Day-to-day life is shaped by pain, fatigue, morning stiffness, swelling, reduced hand function, and the uncertainty of when a flare may disrupt work, cooking, or exercise. Official guidance from NHS and NIAMS consistently frames RA management as a combination of medical treatment and self-management habits rather than any single food or routine. That means users need practical support, not miracle claims. They are likely to benefit from lightweight tracking, simple summaries, and recommendations that are easy to act on even during low-energy days.

Diet guidance for RA is supportive but cautious. Public and charity guidance most consistently favors Mediterranean-style patterns, omega-3-rich foods, high-fiber foods, fruits, vegetables, legumes, nuts, seeds, and olive oil. At the same time, there is no clinically validated universal RA diet, and trigger foods vary across individuals. This makes transparency essential: the app should explain why a meal is recommended, show which nutrition rules were applied, and avoid overstating certainty. A user should feel, "this is a sensible next option," not "the app has medically solved my flare."

Exercise, sleep, hydration, stress, and medication adherence also matter because they shape how users feel and how well they can maintain routines. The app should therefore connect food logging with symptom and lifestyle context while keeping workflows short. Existing app feedback suggests users value reminders, quick logging, and trends they can discuss with clinicians, but dislike generic advice, high-effort input, and anything that ignores flare-day limitations. These findings point to a product that is explainable, low-friction, personalized within safe limits, and explicit about its non-clinical role.

### Task 1 Sources

- NHS Rheumatoid arthritis treatment: https://www.nhs.uk/conditions/rheumatoid-arthritis/treatment/
- NIAMS Rheumatoid Arthritis overview and treatment resources: https://www.niams.nih.gov/health-topics/rheumatoid-arthritis
- Arthritis Foundation diet and anti-inflammatory guidance hub: https://www.arthritis.org/health-wellness/healthy-living/nutrition
- American College of Rheumatology RA guidelines and patient resources: https://rheumatology.org/patients/rheumatoid-arthritis
- Reddit RA community discussions used for patient pain-point themes: https://www.reddit.com/r/rheumatoid/ and related search results

✓ TASK 1 COMPLETE

## 3. Primary User Persona

### Task 2 Persona

- Name: Maya Thompson
- Age: 39
- Occupation: Operations coordinator at a mid-size logistics company
- Location: Manchester, UK
- RA diagnosis history and current status: Diagnosed 4 years ago after months of hand pain and morning stiffness. Currently on DMARD therapy with partial symptom control. Experiences 1 to 2 noticeable flare periods most months, especially during high-stress weeks or when sleep is poor.
- Daily routine and pain patterns: Wakes around 6:30 a.m. with stiffness in hands, wrists, and feet. Energy dips mid-afternoon. Cooking feels manageable on good days and overwhelming on flare days. Evening pain is worse after long desk days.
- Current diet habits and challenges: Skips breakfast on busy mornings, defaults to quick convenience lunches, and wants to eat "less inflammatory" foods but finds advice inconsistent. Has tried removing dairy before but could not tell if it helped.
- Goals for using the app: Find meals that feel realistic, log symptoms without effort, notice patterns between food and flare days, and walk into appointments with clearer history.
- Frustrations with existing tools or apps: Generic calorie trackers feel irrelevant. Symptom trackers are too clinical or time-consuming. She dislikes black-box recommendations and anything that feels judgmental.
- Tech comfort level: Comfortable with smartphone apps and online shopping; not interested in complex setup or manual data entry every hour.
- Success after 30 days: Maya has logged most days in under 3 minutes, found 5 to 7 easy meals she repeats confidently, can see whether poor sleep or certain convenience foods correlate with worse symptom days, and feels more prepared to discuss patterns with her clinician.

✓ TASK 2 COMPLETE

## 4. Scope Definition - In and Out

### Task 3 What the App Does

#### V1 Rule-Based MVP

- User registration, login, logout, and token refresh
- Onboarding flow for allergies, food preferences, dietary exclusions, medications entered for context, symptom goals, and disclaimer acceptance
- Search foods and meals from a curated nutrition dataset
- Log breakfast, lunch, dinner, and snacks
- Log symptoms including pain, fatigue, stiffness, swelling, and flare severity
- Log lifestyle factors including sleep, steps, stress, hydration, and medication taken yes/no
- Generate a next-meal recommendation using transparent nutrition rules
- Show explanation text for each recommendation
- Show daily dashboard with nutrition summary, quick logs, and current recommendation
- Show weekly dashboard with simple trend views and adherence summaries
- Capture whether a recommendation was accepted, skipped, or replaced
- Show persistent medical disclaimer and escalation prompts

#### V1 Default Recommendation Rule Priority

When recommendation rules conflict in V1, the engine should resolve them in this order:

1. Safety constraints: allergies, explicit exclusions, and blocked ingredients are hard stops.
2. Flare-state practicality: if the user logs a severe flare, high pain, or very high fatigue, prefer low-effort and easy-prep meals over theoretically more optimal meals.
3. Daily nutrition balance: fill obvious gaps from earlier logged meals such as low protein, low fiber, or overly high added sugar.
4. User dietary preferences: honor vegetarian, pescatarian, or similar profile preferences after safety and symptom practicality are satisfied.
5. Anti-inflammatory scoring: prefer meals with stronger anti-inflammatory characteristics when higher-priority constraints do not conflict.
6. Variety and usability: if multiple meals are still tied, prefer simpler prep and avoid repeating the exact same suggestion too often.

#### V2 Analytics

- Identify repeated symptom patterns across meals and lifestyle factors
- Show probable user-specific trigger candidates with confidence labels
- Add richer adherence insights and streaks
- Add appointment-ready export summaries
- Add more detailed recommendation tuning based on past responses

#### V3 ML

- Predict short-term pain or flare risk from historical patterns
- Rank meal suggestions using learned user response patterns
- Add smarter anomaly detection for worsening trends
- Add cohort-level model evaluation with clinical review checkpoints
- [VERIFY WITH CLINICIAN: any prediction language and thresholds before public release]

### Task 3 What the App Never Does

- Diagnose RA or any other condition
- Claim to treat, prevent, or cure inflammation, flares, or joint damage
- Replace a rheumatologist, GP, dietitian, or emergency care
- Tell users to start, stop, skip, increase, or decrease medication
- State that a specific food is proven to be the cause of a flare from limited self-tracking alone
- Provide emergency triage, crisis management, or urgent medical instructions beyond directing users to seek care
- Promise clinically validated predictions in V1 or V2
- Use manipulative streaks or guilt-driven notifications during symptom flares
- Share health data externally without explicit consent

### Required Medical Response Boundary

When users ask medical questions, the app must always say some form of:

"I can help you track food, symptoms, and routines, but I cannot provide medical advice or diagnose flare causes. For treatment questions or worsening symptoms, please contact your clinician."

✓ TASK 3 COMPLETE

## 5. User Stories

### Task 4 Research Note

The V1 user stories below are grounded in Task 1 research themes: users want fast logging, recommendations that are explained, support for flare-day reality, and visible summaries they can discuss with clinicians. External grounding came from the same official RA guidance sources above plus community sentiment from Reddit and public app feedback patterns.

### Task 4 User Stories

#### 1. Onboarding and profile setup

1. As a new RA user, I want to enter my food allergies and exclusions, so that meal suggestions avoid unsafe options.
Acceptance criteria:
- [ ] The onboarding flow asks about allergies and exclusions before recommendations are shown.
- [ ] The user can select multiple allergens and add an "other" note.
- [ ] Saved restrictions are applied to search and recommendations.

2. As a new RA user, I want to record medications, symptom priorities, and goals, so that the app can tailor tracking and prompts to what matters most.
Acceptance criteria:
- [ ] The user can enter current medications for context without dosage advice.
- [ ] The user can choose goals such as less fatigue, more consistency, or fewer flare-day food decisions.
- [ ] The profile can be edited later from settings.

3. As a returning user who has not opened the app in several weeks, I want the app to resume my account state without repeating onboarding, so that I can continue using it immediately.
Acceptance criteria:
- [ ] Returning authenticated users are taken to the dashboard, not back through onboarding, when onboarding is already complete.
- [ ] Previously saved restrictions, goals, and disclaimer acceptance are preserved.
- [ ] If important profile data is missing, the app asks only for the missing fields instead of restarting the full flow.

#### 2. Food and meal search

3. As a user, I want to search foods by name, so that I can quickly find what I ate.
Acceptance criteria:
- [ ] Search returns matching foods and meals with common aliases.
- [ ] Results show basic nutrition and dietary tags.
- [ ] Empty states explain when no match is found.

4. As a user, I want meal search results filtered by my restrictions and preferences, so that I do not waste time opening unsuitable options.
Acceptance criteria:
- [ ] Results exclude allergy conflicts.
- [ ] Results can be filtered by vegetarian, pescatarian, or other stored preferences.
- [ ] Restricted items display a clear reason when hidden or blocked.

#### 3. Meal logging

5. As a user, I want to log breakfast, lunch, dinner, or snacks in one flow, so that I can keep a complete food record with minimal effort.
Acceptance criteria:
- [ ] The log flow includes meal type, food, portion, and timestamp.
- [ ] Default timestamps can be edited.
- [ ] A saved log appears immediately on the dashboard.

6. As a user on a flare day, I want quick-add logging for common meals, so that I can still track without too many taps.
Acceptance criteria:
- [ ] The app offers recent meals and favorites.
- [ ] A meal can be logged in three taps or fewer from the dashboard.
- [ ] Quick-add entries remain editable afterward.

#### 4. Next-meal recommendation

7. As a user, I want the app to suggest my next meal, so that I do not have to decide what to eat when I am tired or symptomatic.
Acceptance criteria:
- [ ] The app provides one primary recommendation and at least two alternatives.
- [ ] The recommendation respects allergies, preferences, and logged meals earlier in the day.
- [ ] The recommendation can be refreshed if the user wants a different option.

8. As a user, I want an explanation for why a meal was recommended, so that I can trust the suggestion without guessing.
Acceptance criteria:
- [ ] Explanation text references simple rules such as omega-3, fiber, balanced protein, or low added sugar.
- [ ] The explanation avoids medical claims or certainty language.
- [ ] The user can mark the recommendation accepted or skipped.

9. As a user, when the app cannot generate a recommendation, I want a clear fallback message and simple next step, so that I am not stuck deciding what to eat on a bad day.
Acceptance criteria:
- [ ] The app shows a friendly fallback message when recommendation generation fails or returns no match.
- [ ] The fallback state includes at least one actionable option such as recent meals, curated safe defaults, or meal search.
- [ ] The fallback state avoids technical jargon and does not imply a medical failure.

#### 5. Symptom logging

10. As a user, I want to log pain, fatigue, stiffness, swelling, and flare severity, so that I can compare symptoms with food and routines.
Acceptance criteria:
- [ ] Each symptom can be logged on a simple numeric or categorical scale.
- [ ] The user can add an optional note.
- [ ] The dashboard reflects the latest symptom status for the day.

11. As a user, I want symptom logging to be fast and non-judgmental, so that I will keep using it during bad days.
Acceptance criteria:
- [ ] The symptom form can be completed in under one minute.
- [ ] The interface uses plain, supportive language.
- [ ] Missing optional fields do not block save.

#### 6. Lifestyle logging

12. As a user, I want to log sleep, steps, water, stress, and medication taken, so that I can see my health context around symptoms.
Acceptance criteria:
- [ ] The daily lifestyle form includes all five inputs.
- [ ] Medication tracking is recorded as taken or not taken without dosage changes.
- [ ] Users can edit the same day entry.

13. As a user, I want quick lifestyle logging from the home screen, so that I can keep up with tracking even on busy days.
Acceptance criteria:
- [ ] Sleep, water, and stress can be updated from the dashboard without opening a long form.
- [ ] The app preserves partially entered data.
- [ ] Saved values update trend summaries the same day.

14. As a user, when I lose internet or the app is interrupted during logging, I want my partial entry preserved, so that I do not lose effort on a flare day.
Acceptance criteria:
- [ ] Meal, symptom, and lifestyle forms preserve unsaved draft values locally until the user clears them or submits successfully.
- [ ] The app shows a clear retry state when submission fails.
- [ ] Restoring a draft does not create duplicate saved logs.

#### 7. Daily dashboard

15. As a user, I want one home dashboard that shows today's food, symptoms, and recommendation, so that I can understand my day at a glance.
Acceptance criteria:
- [ ] The dashboard shows meal logs, latest symptoms, lifestyle summary, and recommendation card.
- [ ] Missing sections show friendly prompts instead of blank states.
- [ ] The screen loads correctly even when no data exists yet.

16. As a user, I want quick log actions on the dashboard, so that I can add meals or symptoms without navigating through multiple pages.
Acceptance criteria:
- [ ] The dashboard includes quick actions for meal, symptom, and lifestyle logging.
- [ ] Tapping an action opens the correct prefilled flow.
- [ ] Returning from a log refreshes the dashboard state.

#### 8. Weekly analytics dashboard

17. As a user, I want to see weekly trends in food logging, symptoms, and routines, so that I can notice patterns over time.
Acceptance criteria:
- [ ] The weekly view shows symptom trends and logging consistency.
- [ ] The date range is clearly labeled.
- [ ] Empty data states encourage more logging without making claims.

18. As a user, I want a simple weekly summary of recommendation adherence, so that I can tell whether the suggestions are usable in real life.
Acceptance criteria:
- [ ] The app shows how often recommendations were accepted, skipped, or replaced.
- [ ] The summary is visual and easy to scan.
- [ ] The app does not equate adherence with medical success.

#### 9. Medical disclaimer and escalation

19. As a user, I want clear medical boundaries inside the app, so that I understand what the product can and cannot do.
Acceptance criteria:
- [ ] The onboarding flow requires disclaimer acceptance.
- [ ] A persistent footer disclaimer appears on key screens.
- [ ] The disclaimer language is supportive and non-alarming.

20. As a user with severe symptoms, I want the app to prompt me to seek medical support, so that I am not left treating the app like urgent care.
Acceptance criteria:
- [ ] Logging pain of 8 or higher or a severe flare triggers an escalation message.
- [ ] The escalation message recommends contacting a clinician or urgent care when appropriate.
- [ ] The message does not prevent the user from saving the log.

#### 10. Settings and preferences management

21. As a user, I want to update my preferences and restrictions later, so that my recommendations stay relevant as my habits change.
Acceptance criteria:
- [ ] Users can edit allergies, dietary preferences, goals, and reminders from settings.
- [ ] Changes affect future recommendations immediately.
- [ ] Previous logs are preserved.

22. As a privacy-conscious user, I want control over my account session and data preferences, so that I feel safe using the app.
Acceptance criteria:
- [ ] The user can log out from settings.
- [ ] The app clearly shows core data categories it stores.
- [ ] [DECISION NEEDED: confirm whether V1 includes account deletion or export]

✓ TASK 4 COMPLETE

## 6. Screen Inventory

### Task 5 MVP Screens

#### Splash Screen

- Screen name: Splash
- Route: `/`
- Purpose: Confirm app identity, load auth state, and route users to login or dashboard.
- Key UI elements: Logo, loading indicator, short wellness disclaimer, auth redirect logic.
- API endpoints it will call: `POST /auth/refresh` if refresh token exists.
- Edge cases to handle: Expired refresh token, no network, slow startup, first launch.

#### Login Screen

- Screen name: Login
- Route: `/login`
- Purpose: Let returning users securely access the app.
- Key UI elements: Email field, password field, login button, link to register, error banner.
- API endpoints it will call: `POST /auth/login`.
- Edge cases to handle: Invalid credentials, locked account policy if later added, offline submission.

#### Register Screen

- Screen name: Register
- Route: `/register`
- Purpose: Create a new user account.
- Key UI elements: Name, email, password, confirm password, create account CTA, link to login.
- API endpoints it will call: `POST /auth/register`.
- Edge cases to handle: Duplicate email, weak password, validation mismatch.

#### Onboarding Flow

- Screen name: Onboarding
- Route: `/onboarding`
- Purpose: Collect the minimum profile data needed for safe personalization.
- Key UI elements: Multi-step form, allergies, preferences, medications for context, goals, disclaimer acceptance checkbox, progress indicator.
- API endpoints it will call: `GET /profile`, `PUT /profile`, `POST /profile/disclaimer-acceptance`.
- Edge cases to handle: User exits halfway, missing required restrictions, disclaimer not accepted.

#### Home Dashboard

- Screen name: Home Dashboard
- Route: `/dashboard`
- Purpose: Show today's snapshot and primary actions in one place.
- Key UI elements: Today's summary cards, quick-add actions, latest symptoms, lifestyle summary, persistent disclaimer footer.
- API endpoints it will call: `GET /dashboard/today`, `GET /food-logs/today`, `GET /recommendations/next`.
- Edge cases to handle: New user with no data, partial data, stale recommendation, loading states.

#### Meal Search and Food Log

- Screen name: Meal Search and Food Log
- Route: `/meals/log`
- Purpose: Search foods or meals and save a meal log.
- Key UI elements: Search bar, filters, result list, recent items, favorites, meal type picker, portion input, save CTA.
- API endpoints it will call: `GET /foods/search`, `GET /foods/{food_id}`, `POST /food-logs`.
- Edge cases to handle: No search results, duplicate rapid submissions, missing portion size.

#### Recommendation View

- Screen name: Recommendation Card
- Route: `/recommendation`
- Purpose: Show next-meal recommendation details and feedback options.
- Key UI elements: Recommended meal card, explanation text, alternatives, accept/skip feedback buttons, refresh CTA.
- API endpoints it will call: `GET /recommendations/next`, `POST /feedback/recommendations`.
- Edge cases to handle: No eligible meal found, recommendation conflicts with new profile changes, feedback retry after failure.

#### Symptom Log

- Screen name: Symptom Log
- Route: `/symptoms/log`
- Purpose: Capture the user's current symptom state quickly.
- Key UI elements: Pain, fatigue, stiffness, swelling, flare controls, optional note, save CTA, escalation banner when triggered.
- API endpoints it will call: `POST /symptoms`, `GET /symptoms?start_date=&end_date=`.
- Edge cases to handle: Severe score escalation, accidental double-submit, optional fields left blank.

#### Lifestyle Log

- Screen name: Lifestyle Log
- Route: `/lifestyle/log`
- Purpose: Record contextual daily behaviors that may affect symptom interpretation.
- Key UI elements: Sleep input, steps, water, stress slider, medication taken toggle, save CTA.
- API endpoints it will call: `POST /lifestyle`, `GET /lifestyle?date=`.
- Edge cases to handle: Existing same-day entry, missing wearable data integration, invalid numeric ranges.

#### Weekly Analytics Dashboard

- Screen name: Weekly Analytics
- Route: `/analytics/weekly`
- Purpose: Show simple weekly trends without overstating conclusions.
- Key UI elements: Date range selector, trend charts, adherence summary, informational copy, no-claim disclaimer text.
- API endpoints it will call: `GET /dashboard/weekly`, `GET /symptoms?start_date=&end_date=`, `GET /food-logs?date=`.
- Edge cases to handle: Sparse data, empty week, timezone boundaries, misleading trend interpretation.

#### Profile and Settings

- Screen name: Profile and Settings
- Route: `/settings`
- Purpose: Let users manage preferences, goals, reminders, and session controls.
- Key UI elements: Editable profile fields, restrictions list, goals, reminder preferences, logout button, data usage summary.
- API endpoints it will call: `GET /profile`, `PUT /profile`, `POST /auth/logout`.
- Edge cases to handle: Unsaved changes, conflicting restriction edits, logout with expired token.

#### Medical Disclaimer Modal

- Screen name: Medical Disclaimer Modal
- Route: modal on protected routes
- Purpose: Reinforce safety boundaries and escalation guidance.
- Key UI elements: Disclaimer text, accept/close action depending on context, link to settings or support guidance.
- API endpoints it will call: `POST /profile/disclaimer-acceptance` on onboarding only.
- Edge cases to handle: User tries to bypass acceptance, severe symptom event, first-run vs persistent footer behavior.

✓ TASK 5 COMPLETE

## 7. API Endpoint Inventory

### Task 6 V1 FastAPI Endpoints

#### Auth

- Method + path: `POST /auth/register`
- Purpose: Create a new account.
- Request body or params: `name`, `email`, `password`.
- Response shape: `user_id`, `email`, `access_token`, `refresh_token`, `onboarding_complete`.
- Auth required: No.
- Notes / edge cases: Reject duplicate email and weak password.

- Method + path: `POST /auth/login`
- Purpose: Authenticate a returning user.
- Request body or params: `email`, `password`.
- Response shape: `user_id`, `access_token`, `refresh_token`, `onboarding_complete`.
- Auth required: No.
- Notes / edge cases: Generic error on invalid login to avoid account enumeration.

- Method + path: `POST /auth/refresh`
- Purpose: Issue a new access token.
- Request body or params: `refresh_token`.
- Response shape: `access_token`, `expires_in`.
- Auth required: No.
- Notes / edge cases: Reject revoked or expired refresh tokens.

- Method + path: `POST /auth/logout`
- Purpose: Revoke the active refresh token or session.
- Request body or params: `refresh_token`.
- Response shape: `success`.
- Auth required: Yes.
- Notes / edge cases: Idempotent logout response.

#### User Profile

- Method + path: `GET /profile`
- Purpose: Retrieve the current user's profile and onboarding state.
- Request body or params: None.
- Response shape: `user`, `allergies`, `preferences`, `medications_context`, `goals`, `disclaimer_accepted`.
- Auth required: Yes.
- Notes / edge cases: Return safe defaults for incomplete onboarding.

- Method + path: `PUT /profile`
- Purpose: Update profile, restrictions, and goals.
- Request body or params: editable profile fields and preference arrays.
- Response shape: updated profile object.
- Auth required: Yes.
- Notes / edge cases: Validate allergy list and supported preference values.

- Method + path: `POST /profile/disclaimer-acceptance`
- Purpose: Store acceptance of onboarding disclaimer.
- Request body or params: `accepted`, `accepted_at`.
- Response shape: `success`, `disclaimer_accepted`.
- Auth required: Yes.
- Notes / edge cases: Must require true value before recommendations unlock.

#### Foods

- Method + path: `GET /foods/search`
- Purpose: Search foods and meal templates.
- Request body or params: `q`, optional `meal_type`, optional filters.
- Response shape: list of `food_id`, `name`, `nutrition`, `tags`, `restriction_conflict`.
- Auth required: Yes.
- Notes / edge cases: Must apply user restriction filtering server-side.

- Method + path: `GET /foods/{food_id}`
- Purpose: Get full details for one food or meal item.
- Request body or params: path `food_id`.
- Response shape: `food_id`, `name`, `ingredients`, `nutrition`, `tags`.
- Auth required: Yes.
- Notes / edge cases: Return 404 for unknown ID.

#### Meals

- Method + path: `GET /meals`
- Purpose: List curated meal templates available to the user.
- Request body or params: optional `meal_type`, `limit`, `offset`.
- Response shape: paginated list of meal summaries.
- Auth required: Yes.
- Notes / edge cases: Exclude allergy conflicts by default.

- Method + path: `GET /meals/{meal_id}`
- Purpose: Get a meal template by ID.
- Request body or params: path `meal_id`.
- Response shape: `meal_id`, `name`, `ingredients`, `nutrition`, `reason_tags`.
- Auth required: Yes.
- Notes / edge cases: 404 for unknown ID.

- Method + path: `GET /recommendations/next`
- Purpose: Return the next best meal recommendation.
- Request body or params: optional `meal_type`.
- Response shape: `recommended_meal`, `alternatives`, `explanation`, `rules_applied`, `generated_at`.
- Auth required: Yes.
- Notes / edge cases: If data is sparse, fall back to general balanced meals and say so clearly. This route is intentionally separate from `/meals/{meal_id}` to avoid FastAPI path conflicts.

#### Food Logs

- Method + path: `POST /food-logs`
- Purpose: Create a new meal log.
- Request body or params: `food_id` or custom meal name, `meal_type`, `portion`, `logged_at`, optional notes.
- Response shape: created food log record.
- Auth required: Yes.
- Notes / edge cases: Allow custom entries when food search fails.

- Method + path: `GET /food-logs/today`
- Purpose: Get today's logged meals.
- Request body or params: optional timezone override.
- Response shape: `date`, `entries`, `nutrition_summary`.
- Auth required: Yes.
- Notes / edge cases: Handle timezone boundaries safely.

- Method + path: `GET /food-logs`
- Purpose: Get food logs for a specific date.
- Request body or params: `date`.
- Response shape: `date`, `entries`, `nutrition_summary`.
- Auth required: Yes.
- Notes / edge cases: Return empty list if no entries exist.

#### Symptom Logs

- Method + path: `POST /symptoms`
- Purpose: Create a symptom log.
- Request body or params: `pain`, `fatigue`, `stiffness`, `swelling`, `flare_level`, optional note, `logged_at`.
- Response shape: created symptom log plus `escalation_triggered`.
- Auth required: Yes.
- Notes / edge cases: Trigger escalation metadata when pain >= 8 or flare is severe.

- Method + path: `GET /symptoms`
- Purpose: Get symptom logs by date range.
- Request body or params: `start_date`, `end_date`.
- Response shape: list of symptom logs plus basic aggregates.
- Auth required: Yes.
- Notes / edge cases: Limit maximum date range in V1 for performance.

#### Lifestyle Logs

- Method + path: `POST /lifestyle`
- Purpose: Create or update a same-day lifestyle log.
- Request body or params: `date`, `sleep_hours`, `steps`, `water_ml`, `stress_level`, `medication_taken`.
- Response shape: saved lifestyle record.
- Auth required: Yes.
- Notes / edge cases: Upsert by date for simplicity in V1.

- Method + path: `GET /lifestyle`
- Purpose: Get lifestyle data for a selected date.
- Request body or params: `date`.
- Response shape: lifestyle record for that date.
- Auth required: Yes.
- Notes / edge cases: Return null-safe empty shape when missing.

#### Dashboard

- Method + path: `GET /dashboard/today`
- Purpose: Return a single today summary payload for the home screen.
- Request body or params: optional timezone override.
- Response shape: `date`, `meal_summary`, `latest_symptoms`, `lifestyle_summary`, `recommendation_snapshot`, `quick_actions`.
- Auth required: Yes.
- Notes / edge cases: Must still work for brand new users with no logs.

- Method + path: `GET /dashboard/weekly`
- Purpose: Return simple weekly trends and adherence.
- Request body or params: `start_date`, `end_date`.
- Response shape: `date_range`, `symptom_trends`, `logging_adherence`, `recommendation_feedback_summary`.
- Auth required: Yes.
- Notes / edge cases: Avoid causal wording in summary text.

#### Feedback

- Method + path: `POST /feedback/recommendations`
- Purpose: Record whether the user accepted, skipped, or replaced a recommendation.
- Request body or params: `recommendation_id`, `action`, optional `replacement_food_id`, optional reason.
- Response shape: `success`, saved feedback object.
- Auth required: Yes.
- Notes / edge cases: Validate action enum and support anonymous "skip" reason choices later.

✓ TASK 6 COMPLETE

## 8. Success Metrics and Acceptance Criteria

### Task 7 MVP Launch Criteria

- Users can register, log in, refresh tokens, and log out successfully.
- Onboarding cannot be completed without allergy and disclaimer steps.
- A user can search foods and create a meal log in under 60 seconds on a normal connection.
- Daily dashboard loads correctly for both new users and returning users with data.
- The recommendation endpoint always returns either a valid recommendation with explanation or a safe fallback message.
- Symptom logging correctly triggers escalation messaging for pain scores of 8 or higher or severe flare selection.
- Weekly dashboard displays seven days of data without broken charts or misleading labels.
- Settings changes update future recommendations without deleting historical logs.
- All protected endpoints reject unauthorized access correctly.
- Persistent disclaimer text is visible on core in-app screens.

### Task 7 Recommendation Quality Criteria

- Test that a user with a fish allergy never receives a fish-based recommendation.
- Test that a user who logged a high-sugar snack earlier in the day can still receive a balanced, lower-added-sugar next meal.
- Test that recommendation explanation text matches the actual nutrition rule outputs.
- Test that recommendations still work when a user has no prior logs beyond onboarding.
- Test that accepted vs skipped feedback is stored and visible in weekly adherence summaries.
- Test that meal suggestions remain practical across breakfast, lunch, dinner, and snack contexts.

### Task 7 Safety Criteria

- No screen or endpoint claims to diagnose, treat, or cure RA.
- No recommendation text tells users to change medication use.
- Severe symptom logs always show escalation guidance before the user leaves the flow.
- Analytics views avoid causal language such as "this food caused your flare."
- [VERIFY WITH CLINICIAN: review escalation threshold wording and disclaimer language before real-user testing]

✓ TASK 7 COMPLETE

## 9. Medical Disclaimers

### Task 8 Exact Text

#### Onboarding Disclaimer

"This app is a wellness support tool for tracking meals, symptoms, and daily habits related to living with Rheumatoid Arthritis. It does not provide medical advice, diagnosis, or treatment, and it is not a substitute for a rheumatologist, GP, or registered dietitian. Food and lifestyle recommendations in this app are general, non-clinical suggestions based on your inputs and should not be used to change medications or delay care. If your symptoms are severe, new, or worsening, contact a qualified healthcare professional."

#### Persistent Footer Disclaimer

"Wellness support only - not medical advice or diagnosis."

#### Escalation Message

"You logged symptoms that may need medical attention. This app cannot assess urgent health problems or tell you how to treat a flare. If this pain or flare is severe, unusual for you, getting worse, or you are worried about your safety, please contact your clinician, urgent care, or local emergency services as appropriate."

✓ TASK 8 COMPLETE

## 10. Open Questions

- [RESOLVED IN SPEC: V1 food search and nutrition metadata will use USDA FoodData Central as the primary external food data source]
- [RESOLVED IN SPEC: V1 will use curated meals only for recommendations, plus custom free-text meal/food log entries; no custom meal builder in V1]
- [RESOLVED IN SPEC: reminders and notifications are postponed to V2 to avoid adding extra delivery complexity to the V1 MVP]
- [RESOLVED IN SPEC: V1 should support account deletion; data export is postponed to V2]
- [RESOLVED IN SPEC: recommendation rule conflicts in V1 follow the default priority order defined in the Scope Definition section]
- [RESOLVED IN SPEC: use `GET /recommendations/next` instead of `GET /meals/recommendation` to avoid route conflicts with `GET /meals/{meal_id}` in FastAPI]
- [VERIFY WITH CLINICIAN: review wording around flare triggers, escalation thresholds, and analytics labels before testing with real users]

## 11. Appendix: Rough Entity List

This appendix is a Week 2 planning aid. It is intentionally rough and exists to bridge the gap between the product requirements and the ER diagram / PostgreSQL schema work. Field names may change during implementation, but these entities should be treated as the default storage model unless a better design is chosen in Week 2.

### users

- `id`
- `name`
- `email`
- `password_hash`
- `timezone`
- `is_active`
- `created_at`
- `updated_at`
- `last_login_at`

### user_preferences

- `id`
- `user_id`
- `allergies_json`
- `dietary_flags_json`
- `disliked_foods_json`
- `goal_flags_json`
- `reminder_preferences_json`
- `onboarding_completed`
- `disclaimer_accepted`
- `disclaimer_accepted_at`
- `created_at`
- `updated_at`

### user_medications

- `id`
- `user_id`
- `medication_name`
- `schedule_note`
- `is_active`
- `created_at`
- `updated_at`

### foods

- `id`
- `external_source`
- `external_id`
- `name`
- `brand_name`
- `category`
- `serving_size_g`
- `calories`
- `protein_g`
- `carbs_g`
- `fat_g`
- `fiber_g`
- `sugar_g`
- `sodium_mg`
- `omega3_g`
- `ingredients_text`
- `dietary_tags_json`
- `created_at`
- `updated_at`

### meals

- `id`
- `name`
- `description`
- `meal_type`
- `prep_time_minutes`
- `anti_inflammatory_score`
- `protein_g`
- `fiber_g`
- `sugar_g`
- `sodium_mg`
- `calories`
- `is_curated`
- `dietary_tags_json`
- `reason_tags_json`
- `created_at`
- `updated_at`

### meal_items

- `id`
- `meal_id`
- `food_id`
- `quantity`
- `unit`
- `grams`

### food_logs

- `id`
- `user_id`
- `food_id`
- `meal_id`
- `custom_food_name`
- `meal_type`
- `portion_g`
- `portion_label`
- `notes`
- `logged_at`
- `created_at`
- `updated_at`

### symptom_logs

- `id`
- `user_id`
- `pain_score`
- `fatigue_score`
- `stiffness_score`
- `swelling_score`
- `flare_level`
- `note`
- `escalation_triggered`
- `logged_at`
- `created_at`

### lifestyle_logs

- `id`
- `user_id`
- `log_date`
- `sleep_hours`
- `steps`
- `water_ml`
- `stress_level`
- `medication_taken`
- `notes`
- `created_at`
- `updated_at`

### recommendation_logs

- `id`
- `user_id`
- `meal_id`
- `recommended_for_meal_type`
- `recommendation_context_json`
- `explanation_text`
- `alternatives_json`
- `rules_applied_json`
- `shown_at`
- `feedback_status`
- `feedback_reason`
- `replacement_food_id`
- `feedback_at`
- `created_at`

### authentication_sessions

- `id`
- `user_id`
- `refresh_token_hash`
- `expires_at`
- `revoked_at`
- `created_at`
- `last_used_at`

### Relationships to Assume for Week 2

- One `users` record has one `user_preferences` record.
- One `users` record can have many `user_medications`, `food_logs`, `symptom_logs`, `lifestyle_logs`, `recommendation_logs`, and `authentication_sessions`.
- One `meals` record can have many `meal_items`.
- One `meal_items` record links one `meals` record to one `foods` record.
- One `food_logs` record may reference either a `food_id`, a `meal_id`, or a `custom_food_name`, depending on how the user logged the entry.
- One `recommendation_logs` record references the meal that was recommended and optionally the replacement food chosen by the user.

✓ TASK 9 COMPLETE

✓ WEEK 1 COMPLETE - ready for Week 2
