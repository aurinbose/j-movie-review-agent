# Movie Review Agent

This repository contains an automated agent that finds a trending movie on IMDb, generates a review using an LLM, and saves the result as a draft on Hashnode for manual review and publishing.

Where things live
- `src/agents.py` — Scrapes IMDb for a trending movie, fetches movie details, and generates a review via the Groq client (with model fallbacks and dummy behavior if no API key).
- `src/hashnode_api.py` — Creates a Hashnode draft and can optionally publish it. Uses `contentMarkdown` (preferred) or other fields as a fallback. Returns structured results including `draft_id` when successful.
- `src/crew_lite.py` — Orchestrates the pipeline: research → scrape → generate → create Hashnode draft. It also implements duplicate-skip logic (skips drafting the same movie if it was drafted within the last 7 days).
- `src/storage.py` — Small persistence helpers: `last_draft.json` and `pending_review.json` (the web UI is deprecated but these helpers remain). Functions: `save_last_draft()`, `get_last_draft()` and `save_pending()`.
- `src/scheduler_app.py` — Uses `APScheduler` to schedule the pipeline weekly: Saturday at 10:00 IST (Asia/Kolkata). For development you can run the pipeline manually or enable a test schedule.

New features added
- TV support: the agent now scrapes IMDb TV meter (`/chart/tvmeter`) to find the top trending TV show, generates a separate TV review, and saves it as a distinct draft on Hashnode.
- Duplicate-skip logic: the agent records the last drafted item (movie and TV separately). If the same title is selected again within 7 days the agent will skip creating a duplicate draft.
	- If a previous draft id exists but the draft was deleted on Hashnode, the agent will detect this and recreate the draft even if within 7 days.
- Reference scraping: when `source_url` is available the agent scrapes up to 3 user-review snippets from the title's IMDb reviews page and includes brief reference excerpts in the LLM prompt so generated reviews are informed by existing opinions.
- Draft-only mode: drafts are created by default (not published) so you can review and publish manually on Hashnode.

Files and responsibilities (updated)
- `src/agents.py`: scraping (movies + TV), details extraction, LLM review generation for movie and TV, and reference-review scraping helpers.
- `src/hashnode_api.py`: creates drafts, optionally publishes, and provides `draft_exists(draft_id)` to verify remote existence.
- `src/crew_lite.py`: orchestrates the full pipeline — research, scrape, generate (movie + TV), dedupe checks, and draft creation.
- `src/storage.py`: persists `last_draft.json` with separate entries for `movie` and `tv`.
- `src/scheduler_app.py`: scheduler configured for Saturdays at 10:00 IST; supports a test mode for minute-level testing.

How it works (brief)
1. Research: scrape IMDb moviemeter and TV meter to pick top movie and TV show.
2. Scrape details: fetch plot/summary for each title.
3. Reference collection: optional — scrape user-review snippets from the title's `/reviews` page.
4. Generate: call Groq with a prompt that includes the plot and short reference snippets (if found).
5. Draft: create a Hashnode draft (separate drafts for movie and TV). Record draft id + timestamp in `last_draft.json`.
6. Scheduler: runs weekly (Sat 10:00 IST) or in test mode every minute.

How to run
- Create drafts now (one-off):
```powershell
python -c "from src.crew_lite import run_movie_review_pipeline; run_movie_review_pipeline()"
```
- Run scheduler (weekly Sat 10:00 IST):
```powershell
python -m src.scheduler_app
```
- Test schedule (every minute): set an env var or edit the scheduler for interval mode as documented in `src/scheduler_app.py`.

Environment variables
- `GROQ_API_KEY`, `GROQ_MODEL` — LLM config
- `HN_PUBLICATION_ID`, `HN_ACCESS_TOKEN` — Hashnode credentials

Testing and troubleshooting
- Syntax check:
```powershell
python -m py_compile src/storage.py src/agents.py src/crew_lite.py src/hashnode_api.py
```
- Dry run pipeline (creates drafts if Hashnode credentials set):
```powershell
python -c "from src.crew_lite import run_movie_review_pipeline; run_movie_review_pipeline()"
```
- If a draft isn't returned, inspect `publish_to_hashnode` output and the returned `last_response` payload for GraphQL errors.

Future enhancements
- Add a `--force` flag or CLI option to always recreate drafts bypassing the 7-day skip.
- Add a `--no-references` option to disable reference scraping for faster runs.
- Limit combined token usage when appending reference snippets to the prompt (to control LLM cost).
- Unit tests that mock IMDb and Hashnode responses, plus CI validation for env variables.
- Optional: auto-open created draft in the browser or send a notification when drafts are created.

If you want I can add a small CLI wrapper to toggle force/no-references and to run targeted jobs (movie-only, tv-only).

Environment variables
- `GROQ_API_KEY` — (optional) Groq API key used by `agents.generate_review()`. If missing, `generate_review()` returns a dummy review for local testing.
- `GROQ_MODEL` — (optional) preferred model(s), comma-separated. A recommended fallback is used if a model is decommissioned.
- `HN_PUBLICATION_ID` — Hashnode publication id used when creating drafts.
- `HN_ACCESS_TOKEN` — Hashnode GraphQL bearer token.

How to run
- Run the pipeline once (creates a draft on Hashnode):
```powershell
python -c "from src.crew_lite import run_movie_review_pipeline; run_movie_review_pipeline()"
```

- Run the scheduler (weekly job configured for Saturdays 10:00 IST):
```powershell
python -m src.scheduler_app
```

Testing during development
- To test quickly without waiting for the scheduler, run the pipeline command above.
- The scheduler file has a commented block you can enable for minute-level testing if needed. Alternatively run the pipeline in a loop or use the one-line command.

Behavior notes
- Draft creation: `publish_to_hashnode(..., publish=False)` returns `{"status": "draft_created", "draft_id": "..."}` when successful. Use the returned `draft_id` to open/edit the draft on Hashnode manually before publishing.
- Duplicate skipping: when a draft is created the agent writes `last_draft.json` (UTC timestamp). If the same movie (same IMDb URL) is found within 7 days, the agent will skip creating a duplicate draft.
- Web UI: A small Flask web UI previously existed but has been deprecated — the agent now creates drafts directly to Hashnode.

Troubleshooting
- If no draft id is returned, inspect the returned `last_response` or console logs from `src/hashnode_api.py` to see the GraphQL error (schema mismatch or auth error).
- Ensure `HN_ACCESS_TOKEN` and `HN_PUBLICATION_ID` are valid and that the token has permission to create drafts for the publication.

Next steps you might want
- Add a `--force` flag to bypass the 7-day duplicate check.
- Add unit tests around `get_last_draft()` / duplicate behavior.
- Add CI checks that validate environment variables before running the scheduled job.

---
Generated and maintained in the `movie-review-agent` workspace.
