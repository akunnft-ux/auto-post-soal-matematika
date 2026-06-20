# Database Design — Auto Post Soal Matematika CPNS/TKA/SNBT

## 1. Database Overview

**No database server used.** This project is a headless automation bot with minimal state requirements. All persistent data is stored in a single JSON file tracked in the Git repository.

| Aspect | Detail |
|---|---|
| Storage engine | File system (JSON) |
| Server | None |
| Schema versioning | Git tracking |
| Backup | Git history (full version history) |
| Concurrency | Single-writer (1 sesi per GitHub Actions run) |

---

## 2. Entity List

| Entity | Storage | Purpose |
|---|---|---|
| History | `data/history.json` | Track previously posted questions for anti-duplication |

---

## 3. Entity Definitions

### History

| Attribute | Type | Required | Description |
|---|---|---|---|
| items | `string[]` | Yes | Array of question text strings, max 60 items (FIFO) |

**Constraints:**
- Max 60 items (oldest removed when new added)
- No duplicate strings allowed
- Valid JSON encoding (UTF-8)

---

## 4. Relationship Map

No relationships. Single flat entity.

---

## 5. ERD

```
┌───────────────────┐
│    history.json    │
├───────────────────┤
│ items: string[]   │
│ (max 60, FIFO)    │
└───────────────────┘
```

---

## 6. Table Definitions

Not applicable — no database tables.

### JSON Structure for `data/history.json`

```json
[
  "1, 4, 9, 16, 25, ...",
  "3, 6, 12, 24, 48, ...",
  "2, 5, 10, 17, 26, ..."
]
```

---

## 7. Constraints

| Constraint | Implementation |
|---|---|
| Max 60 items | Python slicing on save: `history[-MAX_ITEMS:]` |
| No duplicates | Check before appending: `if soal in history: retry` |
| Valid JSON | `json.load()` / `json.dump()` with `ensure_ascii=False` |

---

## 8. Index Strategy

Not applicable — file is fully loaded into memory. O(n) scan for duplicate check against max 60 items is negligible.

---

## 9. Unique Constraints

| Constraint | Enforcement |
|---|---|
| Soal text unik | Check before append (in-memory set intersection) |

---

## 10. Audit Strategy

| Action | Recorded |
|---|---|
| Question posted | Appended to history.json (visible in git diff) |
| System failure | Printed to stdout (GitHub Actions log) + Telegram |

**Git-based audit:** Every update to `history.json` is a Git commit with timestamp and author (`github-actions[bot]`). Full diff available in commit history.

---

## 11. RLS Matrix

Not applicable — no database server, no multi-user access. Single admin with full access to repo.

---

## 12. Reporting Strategy

Not applicable — no reporting queries. History is consumed programmatically (prevention of duplicates) and visually (git log).

---

## 13. Migration Strategy

**Initial:** Create `data/history.json` with empty array `[]`.

**Incremental:** No schema migrations needed. If the format ever changes (e.g., add metadata per entry), a one-time migration script will:
1. Read existing file
2. Transform to new format
3. Write back

**Rollback:** `git revert` the commit that changed the format.

---

## 14. Backup Strategy

| Aspect | Detail |
|---|---|
| Frequency | Every git push (after each post) |
| Method | Git repository (full history) |
| Retention | Full git history (indefinite unless repo is pruned) |
| RPO | < 1 posting cycle (max ~8 hours) |
| RTO | Minutes (git clone) |

---

## 15. Retention Strategy

| Entity | Retention | Enforcement |
|---|---|---|
| History items | Max 60 latest | `history[-60:]` on save |
| Git history | Indefinite | Git default |
| Generated PNG files | Deleted after post | Not tracked in git; cleaned up each run |

---

## 16. Security Design

| Concern | Approach |
|---|---|
| Data at rest | Plain JSON in repo (no sensitive data stored — only question text) |
| Data in transit | N/A (read/written locally in runner) |
| Access control | Repo access controls (single owner) |

---

## 17. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| JSON file corruption | History lost, duplicate possible | Git version history allows recovery |
| Concurrent write | Not possible (single session per run) | Acceptable |
| File size growth | 60 items ~5KB max | Trivial |

---

## 18. Recommendations

1. **No database server needed** — JSON file is sufficient for this scale
2. **If scale grows** (100+ pages, 1000+ items): migrate to SQLite (same-file simplicity) or PostgreSQL
3. **If metadata needed** (topic, tanggal post, engagement): migrate each history entry to an object `{soal, topik, tanggal}` instead of plain string
