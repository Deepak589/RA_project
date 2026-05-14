# Active Tasks

## Week 9 — Testing + MVP Release

- [ ] Edge case tests: empty logs, new user no history, full flare mode, allergy conflicts
- [ ] Manually review 20–30 recommendation outputs for quality
- [ ] Add medical disclaimer banners on dashboard + escalation prompts for severe symptoms (pain ≥ 8)
- [ ] Wire Previous/Next week navigation in AnalyticsPage to backend (week offset param)
- [ ] Rerun Docker-backed pytest suite (`docker compose exec -T api pytest tests/ -q`) — confirm 95+ pass
- [ ] Deploy backend to Render.com or Railway (free tier)
- [ ] Deploy frontend to Vercel or Netlify

## Carried architecture questions (decide before V2)
- [ ] Should V2 split `feedback_logs` out of `recommendation_logs`?
- [ ] When does `dietary_flags` JSONB become a normalized join table?
