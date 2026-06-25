# PRD: Self-Learning Engine — Auto Post Soal Matematika

## Document Control

**Version History**

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 0.1 | 2026-06-25 | Tech Lead | Initial draft — self-learning feature addendum |

This document is adapted from `auto-post-reels-matematika/docs/self-learning-prd.md`. All sections (1–14) of that document apply equally to this bot unless noted below.

## Per-Bot Differences

| Aspect | auto-post-reels-matematika (reference) | auto-post-soal-matematika |
|---|---|---|
| Existing analytics | ✅ Has analytics.json, growth.json, classify_performance(), run_analytics_batch() | ❌ None — must build from scratch |
| Content types | quiz, fakta, tips | **quiz only** |
| Learning scope | weights + hooks + CTA + hashtags | **weights not applicable** (only 1 content type); hooks/CTA/hashtags only |
| HOOK_TEMPLATES | Existing (5 per content type) | **Does not exist** — must add hook pool |
| CTA_POOL | Existing (5 items) | **Does not exist** — must add CTA pool |
| HASHTAG_POOL | Existing (12 items) | Existing (12 items) ✅ |
| main.py style | 1130 lines, argparse CLI | 500 lines, no argparse |
| GA workflow | `data/*.json` glob — auto-catches new files | Explicit `data/history.json data/mode.json` — **must update** |
| Concurrency group | ❌ Not set | ❌ Not set |
| Build from | Full existing infrastructure exists | Minimal — quiz-only, image-based, no video |

## Impact on GA Workflow

The file `auto-post-soal-matematika/.github/workflows/auto-post.yml` must be updated:

1. Change `git add data/history.json data/mode.json` → `git add data/*.json` (or add explicit filenames)
2. Add `if: always()` guard to commit step (currently missing)
3. Consider adding concurrency group to prevent race conditions

## All Other Sections

Refer to `auto-post-reels-matematika/docs/self-learning-prd.md` Sections 1–14 for:
- Business Objectives (BO-001 through BO-003)
- Functional Requirements (FR-SL-001 through FR-SL-010)
- Non-Functional Requirements (NFR-SL-001 through NFR-SL-004)
- Data Requirements (analytics_record, classification_record, learning_iteration, learning_config schemas)
- Business Rules (BR-SL-001 through BR-SL-006)
- Workflow diagrams
- Acceptance Criteria (AC-SL-001 through AC-SL-010)
- Traceability Matrix
- Risk Assessment
- Release Strategy
- Effort Estimate
