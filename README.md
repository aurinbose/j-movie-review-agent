# Movie Review Agent

This repository contains an automated agent that finds a trending movie on IMDb, generates a review using an LLM, and saves the result as a draft on Hashnode for manual review and publishing.

Where things live
- `src/agents.py` — Scrapes IMDb for a trending movie, fetches movie details, and generates a review via the Groq client (with model fallbacks and dummy behavior if no API key).
- `src/hashnode_api.py` — Creates a Hashnode draft and can optionally publish it. Uses `contentMarkdown` (preferred) or other fields as a fallback. Returns structured results including `draft_id` when successful.
- `src/crew_lite.py` — Orchestrates the pipeline: research → scrape → generate → create Hashnode draft. It also implements duplicate-skip logic (skips drafting the same movie if it was drafted within the last 7 days).
- `src/storage.py` — Small persistence helpers: `last_draft.json` and `pending_review.json` (the web UI is deprecated but these helpers remain). Functions: `save_last_draft()`, `get_last_draft()` and `save_pending()`.
- `src/scheduler_app.py` — Uses `APScheduler` to schedule the pipeline weekly: Saturday at 10:00 IST (Asia/Kolkata). For development you can run the pipeline manually or enable a test schedule.

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

If you want, I can also add a small script to open the created draft in your browser automatically after creation.

---
Generated and maintained in the `movie-review-agent` workspace.
