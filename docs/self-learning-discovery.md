# Discovery Report: Self-Learning Feature

## 1. Executive Summary

Add a closed-loop self-learning system to 3 existing auto-post bots that analyzes Facebook content performance (via CSV export), classifies posts, and automatically adjusts content generation parameters (topic weights, hooks, CTA, hashtags, schedule) to improve engagement over time.

## 2. Problem Statement

The 3 bots currently generate and post content with fixed, hardcoded parameters (weights, hooks, CTA, hashtags). There is no mechanism to learn from which content performs better and adapt accordingly. The user manually reviews Facebook Insights but must manually adjust code to optimize. This limits account growth potential.

Success = bots autonomously shift content strategy toward what performs best, measured by increasing viral/good ratio over time.

## 3. Stakeholders

| Stakeholder | Role |
|---|---|
| Project Owner (user) | Single operator, admin, and end-user |

## 4. User Roles

| Role | Responsibilities |
|---|---|
| Admin | Download CSV from Facebook Insights, upload to Telegram, monitor performance |

## 5. Core Workflows

### Workflow A: Self-Learning (Manual Trigger, Periodic)

```
1. User downloads CSV report from Facebook Insights (personal account + Pages)
2. User sends CSV file to Telegram bot
3. Bot detects file upload in getUpdates
4. Bot downloads file via Telegram File API
5. Bot parses CSV → analytics_record.json
6. Bot classifies each post (viral/good/bad)
7. Bot runs learning engine:
   - Adjust CONTENT_TYPE_WEIGHTS
   - Re-rank HOOK_TEMPLATES
   - Re-rank CTA_POOL
   - Re-rank HASHTAG_POOL
   - Recommend optimal posting times
8. Bot saves learning_config.json + git commit & push
9. Bot sends Telegram notification: "Self-learning selesai"
```

### Workflow B: Daily Post (Existing, Modified)

```
1. Bot pulls latest code (includes learning_config.json)
2. Bot reads learning_config.json before generating content
3. Bot uses adjusted weights/hooks/CTA/hashtags
4. Generate → render → post → save history (existing flow)
```

## 6. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-SL1 | Bot must detect CSV file uploads from authorized Telegram chat | Must Have |
| FR-SL2 | Bot must download CSV file via Telegram File API | Must Have |
| FR-SL3 | Bot must parse CSV columns regardless of column order/format | Must Have |
| FR-SL4 | Bot must store parsed analytics in data/analytics.json | Must Have |
| FR-SL5 | Bot must classify each post as viral/good/bad using 2-phase threshold | Must Have |
| FR-SL6 | Bot must store classification in data/classification.json | Must Have |
| FR-SL7 | Bot must update CONTENT_TYPE_WEIGHTS based on viral/good ratio per content type | Must Have |
| FR-SL8 | Bot must re-rank HOOK_TEMPLATES by engagement rate | Must Have |
| FR-SL9 | Bot must re-rank CTA_POOL by engagement rate | Must Have |
| FR-SL10 | Bot must re-rank HASHTAG_POOL by usage frequency in viral posts | Must Have |
| FR-SL11 | Bot must save learning output to data/learning_config.json | Must Have |
| FR-SL12 | Bot must git commit & push all data/ changes for persistence across GA runs | Must Have |
| FR-SL13 | Bot must read learning_config.json before content generation | Must Have |
| FR-SL14 | Bot must send Telegram notification on learning completion | Must Have |
| FR-SL15 | Bot must implement one-variable-at-a-time iteration logging | Should Have |
| FR-SL16 | Bot must include FB Page ID in analytics records to distinguish personal vs Pages | Should Have |
| FR-SL17 | Bot must handle missing/empty CSV gracefully | Must Have |

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-SL1 | All analytics records carry `source: "manual"` (CSV export) |
| NFR-SL2 | Learning only acts on minimum 3 analytics records |
| NFR-SL3 | Zero downtime for existing posting workflow |
| NFR-SL4 | All new data files follow same git commit/push pattern as history.json |

## 8. Reporting Requirements

| Report | Format | Destination |
|---|---|---|
| Learning completion summary | Telegram message | Admin chat |
| Classification summary (viral/good/bad counts) | Stored in classification.json | Git persistence |
| Analytics records | analytics.json | Git persistence |
| Learning iterations log | learning_iteration.json | Git persistence |

## 9. Integration Requirements

| Integration | Purpose | Existing? |
|---|---|---|
| Telegram Bot API (getUpdates + file download) | Receive CSV file | ✅ Yes (polling) |
| Facebook Graph API | (Future) Direct analytics fetch | ✅ Yes (posting) |
| Git (via GA) | Persist data across runs | ✅ Yes |

## 10. Assumption Log

| Assumption | Reason | Impact | Status |
|---|---|---|---|
| CSV format follows Facebook Insights standard export | User unsure of format | Parser must be flexible (detect columns by header) | Unresolved |
| User will manually trigger CSV upload | User stated intent | Bot must detect file upload, not require command | Confirmed |
| All 3 bots share same Telegram account for receiving CSVs | All 3 notify same chat | One bot can handle CSV processing for all | Inferred |
| Learning runs on demand (when CSV uploaded), not scheduled | User said "setiap beberapa hari sekali" | No cron needed for learning | Confirmed |

## 11. Gap Analysis

| Gap | Impact | Resolution |
|---|---|---|
| auto-post-soal-matematika has no analytics infrastructure | Must build from scratch | Implement full self_learning/ module |
| auto-post-reels-matematika has partial analytics | Must extend with CSV parser + learning engine | Keep existing, add new module |
| auto-post-reels-manim has no analytics infrastructure | Must build from scratch | Implement full self_learning/ module |
| GA workflows for soal & manim use explicit file lists | Self-learning files not in commit | Update git add patterns |

## 12. Open Questions

| Question | Status |
|---|---|
| CSV column names/order? | Unresolved — Parser must auto-detect |
| Distinguish personal account posts vs Pages posts in analytics? | To be confirmed by user |

## 13. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| CSV format different from expected | Medium | Use Gemini to parse flexible headers |
| Learning degrades performance instead of improving | Low | One-variable-at-a-time logging; revert possible |
| Git conflicts from concurrent GA runs | Low | Concurrency group pattern (reels-manim already has it) |

## 14. Feature Prioritization

| Feature | Priority |
|---|---|
| CSV parsing + analytics storage | Must Have |
| Performance classification | Must Have |
| Learning engine (weights, hooks, CTA, hashtags) | Must Have |
| learning_config.json integration into main.py | Must Have |
| Git persistence of new data files | Must Have |
| One-variable-at-a-time logging | Should Have |
| Schedule optimization | Could Have |
| Facebook Insights API integration | Future (Phase 2) |

## 15. Recommendation

Proceed to PRD and implementation with CSV-first approach, flexible parser that auto-detects column headers, and per-bot self_learning/ module as designed.
