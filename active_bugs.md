# Active Bugs — OF-Scraper

Verified 2026-05-01. All entries confirmed by direct file read (4-agent parallel audit).

---

## CRITICAL (will crash at runtime)

### 1. `MetadataStats.skipped_count` AttributeError
- **File:** `ofscraper/managers/stats.py:450`
- **Code:** `stat_obj.skipped_count += 1`
- **Problem:** `MetadataStats` (lines 18-24) defines `unchanged_count`, not `skipped_count`. `skipped_count` exists on `DownloadStats` and `TextStats` but `_update_metadata_stats_helper` receives a `MetadataStats` object.
- **Fix:** Change `stat_obj.skipped_count` to `stat_obj.unchanged_count`, or add `skipped_count` attribute to `MetadataStats`.

### 2. `globals().update()` overwrites module imports (5 sites)
- **File:** `ofscraper/classes/placeholder.py:113,248,271,454,476`
- **Code:** `globals().update(self._variables)`
- **Problem:** Injects all placeholder variables (`model_username`, `model_id`, `mediatype`, etc.) into the module's global namespace. A model whose username matches an imported module name (`log`, `os`, `re`, `pathlib`, `json`) would overwrite that import, causing unpredictable crashes downstream.
- **Fix:** Remove all 5 `globals().update()` calls. Use explicit local variable access or a dict-based lookup instead.

### 3. Typo `"inpit"` causes NoneType crash
- **File:** `ofscraper/prompts/prompt_groups/merge.py:120`
- **Code:** `"type": "inpit"`
- **Problem:** Typo for `"input"`. `getType("inpit")` returns `None`, then called as `None(...)` → `TypeError: 'NoneType' object is not callable`.
- **Fix:** Change to `"type": "input"`.

---

## HIGH (wrong results, data loss, common crashes)

### Pagination — offset advanced by `len(batch)` not fixed limit (6 sites)

OF API uses absolute offset positioning. Server-skipped items (deleted accounts, hidden content) occupy slots without being returned. Advancing by `len(batch)` (which is smaller than the page limit when items are skipped) causes overlapping re-fetches and silently missed data. Fix: advance by the page limit constant, not `len(returned)`.

| # | File | Line | Code |
|---|------|------|------|
| 4 | `ofscraper/data/api/pinned.py` | 141 | `current_offset += len(batch)` |
| 5 | `ofscraper/data/api/highlights.py` | 251 | `current_offset += len(data)` |
| 6 | `ofscraper/data/api/labels.py` | 248 | `current_offset += len(batch)` |
| 7 | `ofscraper/data/api/labels.py` | 302 | `current_offset += len(batch)` |
| 8 | `ofscraper/data/api/subscriptions/lists.py` | 149 | `current_offset += len(out_list)` |
| 9 | `ofscraper/data/api/subscriptions/lists.py` | 261 | `current_offset += len(users)` (⚠️ partial — fallback path only; server-provided `nextOffset` bypasses bug. Triggers only if API omits `nextOffset`.) |

### `arrow.get(None)` — missing `or 0` guard (2 sites)

`arrow.get(None)` silently returns `arrow.utcnow()` instead of raising. This corrupts date-range filters and sort orders. All other sites in the codebase correctly use `or 0` — these 2 were missed.

| # | File | Line | Code |
|---|------|------|------|
| 10 | `ofscraper/data/api/archive.py` | 137 | `arrow.get(x.get("created_at")).float_timestamp` |
| 11 | `ofscraper/data/api/streams.py` | 143 | `arrow.get(x.get("created_at")).float_timestamp` |

**Fix for both:** Change to `arrow.get(x.get("created_at") or 0).float_timestamp`.

### Classes — hard dict access / None crashes

| # | File | Line | Code | Problem | Fix |
|---|------|------|------|---------|-----|
| 12 | `ofscraper/classes/of/posts.py` | 244 | `self._post["id"]` | KeyError if API response missing `"id"` key | `self._post.get("id")` |
| 13 | `ofscraper/classes/of/posts.py` | 252 | `arrow.get(self.date)` | `self.date` (line 248) returns `None` if both `postedAt` and `createdAt` absent → TypeError | Guard with `if self.date:` or `or 0` |
| 14 | `ofscraper/classes/of/models.py` | 66,79 | `key=lambda x: x["price"]` | KeyError if promo dict lacks `"price"` key in `all_claimable_promo` and `all_promo` sort | `key=lambda x: x.get("price", 0)` |
| 15 | `ofscraper/classes/of/models.py` | 159-161 | `if self.sub_price is not None: return self.sub_price` | `sub_price` (line 39) returns `self._model.get("currentSubscribePrice")` which can be `{}` (empty dict). `{} is not None` is True → `final_current_price` returns `{}` instead of a number. Downstream arithmetic/sorting crashes. | Check `isinstance(self.sub_price, (int, float))` or add fallback for non-numeric |
| 16 | `ofscraper/classes/of/media.py` | 178 | `arrow.get(self.duration)` | Treats float seconds as Unix timestamp (epoch + seconds). Works accidentally for floats but semantically wrong and fragile for string values. | Use `datetime.timedelta(seconds=self.duration)` or format manually |

### Table/TUI — broken filters

| # | File | Line | Code | Problem | Fix |
|---|------|------|------|---------|-----|
| 17 | `ofscraper/classes/table/fields/selectfield.py` | 43-44 | `value in self.query_one(SelectionList).selected` | Row values are Python bool (`True`/`False`). SelectionList values are strings (`"True"`/`"False"`). `True in ["True", "False"]` is `False` (bool int 1 ≠ str). **Download and Unlock filters are 100% broken — they pass all items unfiltered.** | Cast both sides: `str(value) in selected` |
| 18 | `ofscraper/classes/table/fields/responsefield.py` | 97 | `elif val == "Stream":` | Should be `"Streams"` (matching the Selection value at line 60). Clicking a Streams table cell to populate the filter results in blank/no selection state. | Change to `"Streams"` |

### Prompts — logic error

| # | File | Line | Code | Problem | Fix |
|---|------|------|------|---------|-----|
| 19 | `ofscraper/prompts/prompt_groups/area.py` | 39 | `("like" or "unlike") in args.actions` | Python `or` with strings: `"like" or "unlike"` evaluates to `"like"` (non-empty string is truthy). **Unlike-only actions are dead code.** The `more_instruction` never displays for unlike-only. | `"like" in args.actions or "unlike" in args.actions` |

### Utils — data corruption

| # | File | Line | Code | Problem | Fix |
|---|------|------|------|---------|-----|
| 20 | `ofscraper/utils/text.py` | 51 | `await p.writelines(wrapped_text)` | `io.IOBase.writelines()` (and `aiofiles`) does **not** add newline separators. All wrapped text lines are concatenated into one blob → corrupted text file output. | `await p.write("\n".join(wrapped_text))` or add `"\n"` to each line |
| 21 | `ofscraper/utils/config/schema.py` | 11 | `"main_profile" if config is False else of_env.getattr("mainProfile")` | `of_env.getattr("mainProfile")` checks `os.environ.get("mainProfile")` (env var unlikely to exist) then `config_dict.get("mainProfile")` (no such key in `get_all_configs()`) → returns `None` → schema dict gets key `None` instead of `"main_profile"`. | Use static key `"main_profile"` or reference `of_env.getattr("PROFILE_DEFAULT")` |
| 22 | `ofscraper/utils/config/file.py` | 62-66 | `auto_update_config` replaces entire config | Builds fresh dict from schema functions only — drops any user config keys not known to the schema. **Silent data loss on config upgrade.** | Merge new schema with existing config instead of full replacement |

---

## MEDIUM (subtle wrong behavior, resource leaks)

| # | File | Line | Problem | Fix |
|---|------|------|---------|-----|
| 23 | `ofscraper/utils/context/run_async.py` | 10 | Uses deprecated `asyncio.get_event_loop()`. Should use `get_running_loop()` with RuntimeError fallback (same pattern already used correctly at line 36 of same file). | `asyncio.get_running_loop()` with fallback to `asyncio.new_event_loop()` |
| 24 | `ofscraper/utils/context/run_async.py` | 26-27 | `if loop.is_running(): loop.run_until_complete(loop.shutdown_asyncgens())` — loop is never running at this point (run() creates/gets loop but doesn't start it), so `shutdown_asyncgens()` is never called → async generator resource leak. | Remove `if` guard, always call `shutdown_asyncgens()` |
| 25 | `ofscraper/utils/cache/cache.py` | 29-44 | `set()` defaults `auto_close=True` → closes cache after every write, next op reopens. Massively inefficient for bulk operations. | Default `auto_close=False` or add bulk set method |
| 26 | `ofscraper/classes/of/base.py` | 15 | `text_trunicate` method name typo (missing 'c'). Propagates to `trunicated_filepath`, `trunicated_filename`, `trunicated_filedir` throughout placeholder.py. | Rename to `text_truncate` and update all references |

---

## New Bugs from 2026-04-30 Audit

### HIGH (missing guards / direct dict indexing)

| # | File | Line | Code | Problem | Fix |
|---|------|------|------|---------|-----|
| 27 | `ofscraper/commands/check.py` | 584 | `profile.scrape_profile(model_id)["username"]` | `scrape_profile` may return `None` on auth/network failure. Subscripting `None` → `TypeError`. | Guard: `data = profile.scrape_profile(model_id); user_name = data.get("username") if data else None` |
| 28 | `ofscraper/commands/check.py` | 667 | `profile.scrape_profile(name)["username"]` | Same None dereference. | Same guard |
| 29 | `ofscraper/commands/check.py` | 724 | `profile.scrape_profile(user_name)["username"]` | Same None dereference. | Same guard |
| 30 | `ofscraper/commands/manual.py` | 259-260 | `data.get("username"), data.get("id")` | `data` may be `None`; calling `.get()` on None → `AttributeError`. | Guard: `if not data: return None, None` |
| 31 | `ofscraper/utils/auth/utils/prompt.py` | 30-31 | `auth["auth_uid_"]` | `auth_schema` normalizes key to `"auth_uid"` (no trailing underscore). `auth["auth_uid_"]` raises `KeyError` on auth setup. | Use `"auth_uid"` (matches schema output) or `auth.get("auth_uid_")` |
| 32 | `ofscraper/classes/of/models.py` | 23 | `self._model["username"]` | Direct dict index — API may omit key → `KeyError`. | `self._model.get("username")` |
| 33 | `ofscraper/classes/of/models.py` | 27 | `self._model["id"]` | Direct dict index → `KeyError`. | `self._model.get("id")` |
| 34 | `ofscraper/classes/of/models.py` | 31 | `self._model["avatar"]` | Direct dict index → `KeyError`. | `self._model.get("avatar")` |
| 35 | `ofscraper/classes/of/models.py` | 35 | `self._model["header"]` | Direct dict index → `KeyError`. | `self._model.get("header")` |
| 36 | `ofscraper/classes/of/models.py` | 73 | `self.all_claimable_promo[0]["price"]` | If promo dict lacks `"price"` key → `KeyError`. | `.get("price", 0)` |
| 37 | `ofscraper/classes/of/models.py` | 86 | `self.all_promo[0]["price"]` | Same KeyError risk. | `.get("price", 0)` |
| 38 | `ofscraper/classes/of/media.py` | 210 | `self._media["id"]` | Direct dict index → `KeyError`. | `self._media.get("id")` |
| 39 | `ofscraper/classes/of/posts.py` | 274 | `self._post["fromUser"]["id"]` | Outer key guarded by `.get("fromUser")` but inner `"id"` is direct index. If fromUser dict omits `id` → `KeyError`. | `.get("fromUser", {}).get("id")` |
| 40 | `ofscraper/data/api/timeline.py` | 324 | `float(x["postedAtPrecise"])` | Missing `.get()` fallback → `KeyError` if API omits key. | `float(x.get("postedAtPrecise", 0))` |

### MEDIUM — `arrow.get(None)` missing `or 0` guard

| # | File | Line | Code | Problem | Fix |
|---|------|------|------|---------|-----|
| 41 | `ofscraper/db/operations_/posts.py` | 414, 422, 430, 438 | `arrow.get(x["posted_at"])` | 4 functions (`get_oldest_archived_date`, `get_youngest_archived_date`, `get_oldest_streams_date`, `get_youngest_streams_date`). If `posted_at` is None, `arrow.get(None)` returns `utcnow()`, corrupting sort order. | `arrow.get(x["posted_at"] or 0)` |
| 42 | `ofscraper/classes/placeholder.py` | 221 | `arrow.get(ele.postdate)` | `ele.postdate` (from Media.postdate → Post.date) can be None. | `arrow.get(ele.postdate or 0)` |
| 43 | `ofscraper/classes/of/media.py` | 414 | `arrow.get(self.date)` | `self.date` may be None in Profile branch. | `arrow.get(self.date or 0)` |
| 44 | `ofscraper/classes/of/media.py` | 575, 578 | `arrow.get(self.date)` | Same in `get_text()`. | `arrow.get(self.date or 0)` |
| 45 | `ofscraper/data/api/messages.py` | 339-341 | `arrow.get(x.get("createdAt") or x.get("postedAt"))` | If both fields None → `arrow.get(None)` returns `utcnow()`. Messages outside valid date range may be incorrectly included. | `arrow.get((x.get("createdAt") or x.get("postedAt")) or 0)` |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High | 33 |
| Medium | 9 |
| **Total** | **45** |

### By area (sums to 45):
- **Data/API layer:** 10 (pagination ×6, arrow.get(None) ×3 in archive/streams/messages, timeline KeyError ×1)
- **Classes:** 18 (placeholder globals ×1 entry / 5 sites, placeholder arrow ×1, posts ×3, models ×8, media ×4, base ×1)
- **Table/TUI:** 2 (selectfield, responsefield)
- **Prompts:** 2 (merge typo, area operator precedence)
- **Utils:** 7 (text, schema, config, run_async ×2, cache, auth prompt auth_uid_)
- **Stats:** 1 (skipped_count AttributeError)
- **Commands:** 4 (check.py ×3, manual.py ×1)
- **DB operations:** 1 (arrow.get(None) ×4 sites in posts.py, single entry)

### Audit notes (2026-05-01)
- All 45 entries verified by direct file read via 4-agent parallel audit.
- 0 hallucinations.
- #9 partially stale — server `nextOffset` bypass mitigates most calls; bug only fires on fallback path.
- #40 categorized under "direct dict indexing" (KeyError on `x["postedAtPrecise"]`) — not arrow.get cluster.
- #2 (`globals().update`) interacts with #26 (`text_trunicate` typo) in placeholder.py — a model username `trunicated_filepath` would shadow that helper.

---

## Closure Log

**2026-05-02:** All 45 verified bugs + 1 finding (#46) fixed across 6 themed commits on `main`.

| Batch | Commit | Bugs |
|-------|--------|------|
| 1 | `33cc3f0e` | #3, #17, #18, #19 (TUI + prompts) |
| 2 | `cfea4601` | #1, #20, #21, #22, #23, #24, #25 (stats + utils) |
| 3 | `871a6701` | #4, #5, #6, #7, #8, #9, #40 (pagination + timeline) |
| 4 | `f52a1fcd` | #10, #11, #41, #42, #43, #44, #45 (`arrow.get(None)` guards) |
| 5 | `10b0717b` | #12, #13, #14, #15, #16, #26, #32-#39, **#46** (class dict access + `text_trunicate` rename) |
| 6 | `1e38d3d9` | #2, #27, #28, #29, #30, #31 (placeholder globals + commands + auth) |

### Caveats / Known residual

- **#9 partial:** server `nextOffset` bypass mitigates most calls; bug only fires on fallback path. Cannot fix further without an authoritative API page-size constant.
- **#16 numeric_duration:** semantics changed from `arrow.get(N) - arrow.get(0)` to `datetime.timedelta(seconds=int(...))`. Identical output for integer seconds; sub-second precision dropped (OF API returns int — no impact in practice).
- **#22 auto_update_config:** shallow merge — preserves user top-level keys (the bug we fixed) but won't backfill new nested schema keys added in future. Acceptable per spec; flag if schema later adds nested defaults.

### Findings during sweep (logged as future cleanup, not blocking)

- **#46 placeholder.py:427** — `arrow.get(ele.date)` missed by original audit. Caught during Batch 4 review, fixed in Batch 5. Mirror of #42.
- **#47 timeline.py:147** — `sorted(..., key=lambda x: arrow.get(x["created_at"]))` no guard. Downstream filter at line 148 strips None entries, so sort is wasteful but correctness preserved. Cosmetic perf nit.
- **#48 timeline/archive/streams `max_ts = 0` propagation** — `.get("postedAtPrecise", 0)` fix in #40 (and pre-existing same pattern in archive/streams) means a batch where ALL posts lack the field would compute `max_ts=0` → next URL cursor = epoch → potential silent loop. Rare; recommend filter-out approach: `[float(x["postedAtPrecise"]) for x in batch if "postedAtPrecise" in x]` + empty-batch guard.
- **#49 `prompts/prompt_groups/config.py:52`** — different misspelling `trunication_default: toggle for trunicating filenames` in help-text docstring. Cosmetic; not caught by `trunicate` grep. One-line cleanup candidate.
- **#50 `update_table_val` (selectfield.py:57-61)** — same bool/string mismatch class as #17 but currently safe path (DataTable stringifies before reaching it). Defensive `str(val)` would harden against future bool-typed columns.
- **#51 `data.get_main_profile` (config/data.py)** — still reads via `of_env.getattr("mainProfile")` while schema (post-#21) writes hardcoded `"main_profile"`. Symmetric only when env var unset; user setting `OFSC_MAIN_PROFILE_NAME=custom` would break. Pre-existing read logic, not introduced by sweep.

### Verification method

- 4 parallel read-only audit agents independently confirmed all 45 entries before sweep started (2026-05-01).
- Each batch reviewed by spec-compliance + code-quality reviewers post-implementation.
- Static checks (`python -m py_compile`) passed every batch. Pre-commit hooks not skipped.
- No tests exist beyond `test_constants.py`; user smoke between batches was the runtime verification gate.

### Polish commit (post-Batch-6)

- `commands/check.py:728-732` — renamed loop variable `user_name` → `input_name` so the `log.warning(...)` skip message includes the offending input. Caught by Batch 6 code-quality reviewer.
