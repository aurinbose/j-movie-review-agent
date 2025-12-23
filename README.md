# 🎬📺 Movie & TV Review Agent

**Your AI-powered content creation machine that finds the BUZZIEST movies and TV shows, writes killer reviews, and drops them straight into Hashnode drafts!**

***

## 🚀 What Does This Do?

This agent is **smart**. It doesn't just pick random movies from IMDb—it analyzes **social buzz** across multiple sources (TMDB, Reddit, Google Trends, Letterboxd), finds what people are **actually talking about**, scrapes IMDb for details, generates professional AI reviews using Groq, and creates ready-to-publish drafts on Hashnode.

**TL;DR:** Set it, forget it, review amazing content weekly! 🎯

***

## 🏗️ Architecture Overview

```
🧠 Trend Analysis → 🔍 IMDb Scraping → ✍️ AI Review → 📝 Hashnode Draft
   (Multi-source)     (Plot/Details)    (Groq LLM)    (Manual Publish)
```

### 📂 File Structure

- **`src/movie_trend_analyst.py`** 🎬 — Finds BUZZING movies using TMDB + IMDb + Google Trends + Reddit
- **`src/tv_trend_analyst.py`** 📺 — Finds trending TV shows using TMDB + Trakt + JustWatch
- **`src/agents.py`** 🤖 — IMDb scraping, review generation, URL resolution, reference reviews
- **`src/hashnode_api.py`** 📰 — Creates Hashnode drafts with GraphQL (publish-ready or draft-only)
- **`src/crew_lite.py`** 🎯 — **MAIN ORCHESTRATOR** - runs full movie + TV pipeline with trend analysis
- **`src/storage.py`** 💾 — Saves draft metadata (`last_draft.json`) to prevent duplicates
- **`src/scheduler_app.py`** ⏰ — APScheduler for weekly automation (Saturday 10:00 IST)

***

## 🎉 New Features (Production Ready!)

### 🔥 Multi-Source Trend Analysis
**Movies:** TMDB Trending + TMDB Popular + IMDb Moviemeter + fallbacks  
**TV Shows:** TMDB TV Trending + Trakt + JustWatch + IMDb TV Meter  

**Why?** Picks movies/shows people **actually want to read about** (not just old classics)

### 🧠 Buzz Score Algorithm
Each source gets weighted scores:
- **TMDB Trending:** 40 points (highest authority)
- **TMDB Popular:** 30 points
- **Reddit mentions:** 25 points (social proof)
- **IMDb boost:** 15 points (baseline)

**Result:** The #1 buzzing movie/show wins! 🏆

### 📺 Dual Content Pipeline
- **Movies** → Friday 6 PM IST
- **TV Shows** → Sunday 6 PM IST  
*(Configurable in scheduler)*

### 🚫 Smart Duplicate Detection
- Tracks last drafted items separately (movie vs TV)
- Skips duplicates within **7 days**
- Detects deleted Hashnode drafts and recreates them
- Checks by **both title AND URL** for accuracy

### 📚 Reference Review Scraping
Scrapes up to **3 user reviews** from IMDb's `/reviews` page and includes snippets in the AI prompt for context-aware, informed reviews.

### 🛡️ Production Bulletproofing
- **Timezone-aware datetime** (no deprecation warnings)
- **Multi-model fallback** (handles Groq model decommissioning)
- **URL resolution** moved to `agents.py` (clean separation)
- **Graceful fallbacks** at every step (trend analysis → IMDb direct)

***

## ⚙️ How It Works (Step-by-Step)

### 🎬 **MOVIE PIPELINE**
```
1. 📈 TREND ANALYSIS
   └─ Scrape TMDB + Reddit + Google Trends + IMDb
   └─ Calculate buzz scores
   └─ Pick #1 movie (e.g., "Wicked" buzz: 70)

2. 🔍 IMDB RESOLUTION
   └─ Search IMDb for movie title
   └─ Resolve to actual title page (/title/tt1234567/)

3. 📝 SCRAPE DETAILS
   └─ Get plot, rating, year from IMDb

4. 📚 REFERENCE REVIEWS (Optional)
   └─ Scrape 3 user reviews from IMDb /reviews page

5. ✍️ AI GENERATION
   └─ Groq LLM generates 400-600 word review
   └─ Includes plot + references + star rating

6. 📤 HASHNODE DRAFT
   └─ Create draft (not published)
   └─ Save draft_id + timestamp to last_draft.json
   └─ Skip if same movie drafted < 7 days ago
```

### 📺 **TV PIPELINE** (Same structure, separate sources)
Same 6 steps but uses `TVTrendAnalyst` and TV-specific scrapers.

***

## 🚀 Quick Start

### 1️⃣ Install Dependencies
```bash
pip install requests beautifulsoup4 cloudscraper groq apscheduler python-dotenv
```

### 2️⃣ Set Environment Variables
Create a `.env` file:
```env
# Groq LLM (required for AI reviews)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Hashnode (required for drafts)
HN_PUBLICATION_ID=your_publication_id
HN_ACCESS_TOKEN=your_hashnode_token
```

### 3️⃣ Run Once (Manual Test)
```powershell
python -c "from src.crew_lite import run_movie_review_pipeline; run_movie_review_pipeline()"
```

**Expected Output:**
```
🎬 MOVIE PIPELINE
📈 PHASE 1: MOVIE TREND ANALYSIS...
🎯 SELECTED MOVIE (Buzz: 70): Wicked
✅ Draft created: 12abc34def56

📺 TV SHOW PIPELINE
📈 PHASE 1: TV TREND ANALYSIS...
🎯 SELECTED TV SHOW (Buzz: 65): The Last of Us
✅ TV draft created: 78ghi90jkl12

🎉 PIPELINE COMPLETED
```

### 4️⃣ Enable Weekly Automation
```powershell
python -m src.scheduler_app
```

**Default Schedule:**  
📅 **Saturday 10:00 AM IST** (runs both movie + TV pipelines)

***

## 🧪 Testing & Development

### Syntax Check
```powershell
python -m py_compile src/agents.py src/crew_lite.py src/movie_trend_analyst.py src/tv_trend_analyst.py
```

### Test Trend Analysts Separately
```bash
# Test movie trend analysis
python -m src.movie_trend_analyst

# Test TV trend analysis  
python -m src.tv_trend_analyst
```

### Force Re-draft (Bypass 7-day skip)
Delete `last_draft.json` or manually edit timestamps.

***

## 📊 Supported Sources

### 🎬 **Movie Sources**
- ✅ TMDB Trending API (JSON)
- ✅ TMDB Popular API (JSON)
- ✅ IMDb Moviemeter (scraping)
- ✅ Hardcoded recent hits (failsafe)

### 📺 **TV Sources**
- ✅ TMDB TV Trending API
- ✅ Trakt TV API
- ✅ JustWatch trending
- ✅ IMDb TV Meter (scraping)

### 📈 **Social/Buzz Sources** *(Future - currently fallbacks)*
- Reddit (r/movies, r/Cinema, r/TrueFilm)
- Google Trends (movie searches)
- Letterboxd (popular films)

***

## 🎯 Customization Options

### Change Schedule
Edit `src/scheduler_app.py`:
```python
# Current: Saturday 10:00 IST
scheduler.add_job(
    run_movie_review_pipeline,
    'cron',
    day_of_week='sat',
    hour=10,
    minute=0,
    timezone=timezone(timedelta(hours=5, minutes=30))
)
```

### Adjust Buzz Weights
Edit `src/movie_trend_analyst.py`:
```python
# Increase TMDB weight
for movie in tmdb_movies:
    buzz_scores[movie] += 50  # Default: 40
```

### Skip TV Pipeline
Comment out TV section in `src/crew_lite.py` lines 150-250.

***

## 🐛 Troubleshooting

### ❌ "No trending movies found"
- **Cause:** TMDB API down or scraping blocked
- **Fix:** Check internet connection, run trend analyst separately for debug output

### ❌ "Failed to create draft on Hashnode"
- **Cause:** Invalid `HN_ACCESS_TOKEN` or `HN_PUBLICATION_ID`
- **Fix:** Verify credentials at [Hashnode Settings](https://hashnode.com/settings/developer)

### ⚠️ "Groq authentication failed"
- **Cause:** Invalid `GROQ_API_KEY`
- **Fix:** Get free key at [console.groq.com](https://console.groq.com)

### 🔄 "SKIPPING: Same movie drafted X days ago"
- **Expected:** Duplicate prevention working correctly
- **Override:** Delete `last_draft.json` to force re-draft

***

## 🚀 Future Enhancements

- [ ] **CLI wrapper** (`--force`, `--movie-only`, `--tv-only`)
- [ ] **GitHub Actions** workflow for cloud automation
- [ ] **Discord/Slack notifications** when drafts created
- [ ] **Auto-publish** mode (currently draft-only)
- [ ] **Multi-language reviews** (Spanish, French, etc.)
- [ ] **Podcast episode reviews** (same pipeline, new sources)
- [ ] **Token usage tracking** for Groq cost control
- [ ] **Unit tests** with mocked IMDb/Hashnode responses

***

## 📝 Notes

- **Drafts are NOT auto-published** — you review and publish manually on Hashnode ✅
- **Duplicate detection** works across runs (persists in `last_draft.json`)
- **Reference reviews** enhance AI quality but are optional (can be disabled)
- **Timezone-aware** — uses `datetime.now(timezone.utc)` (Python 3.11+)

***

## 🤝 Contributing

Found a bug? Have ideas? Open an issue or PR! This agent is built for the community. 🎉

***

## 📜 License

MIT License - Do whatever you want! 🚀

***

**Built with ❤️ by AI-powered content creators**  
🎬 Movies -  📺 TV Shows -  🤖 Automation -  ✍️ AI Reviews

*Now go publish some amazing content!* 🔥