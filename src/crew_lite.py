# src/crew_lite.py - MODIFIED FOR YOUR WEBAPP
from src.agents import (
    get_trending_movie,
    get_movie_details,
    generate_review,
    get_trending_tv,
    get_tv_details,
    generate_show_review,
)
from src.hashnode_api import publish_to_hashnode
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
from src.storage import save_last_draft, get_last_draft
from src.hashnode_api import draft_exists

load_dotenv()

def run_movie_review_pipeline():
    """🎬 COMPLETE MOVIE REVIEW PIPELINE - WORKS WITH YOUR FLASK WEBAPP"""
    print("="*80)
    print(f"🎥 MOVIE REVIEW AGENT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    try:
        # 1️⃣ RESEARCH PHASE
        print("\n📈 PHASE 1: RESEARCH - Finding trending movie...")
        movie = get_trending_movie()
        if not movie or not movie.get('title'):
            print("❌ No trending movie found")
            return
        
        print(f"✅ SELECTED: {movie['title']}")
        print(f"🔗 {movie['url']}")
        
        # 2️⃣ SCRAPE PHASE
        print("\n📝 PHASE 2: SCRAPE - Gathering details...")
        details = get_movie_details(movie['url'])
        plot_preview = details.get('plot', 'No plot')[:150] + "..."
        print(f"✅ PLOT: {plot_preview}")
        
        # 3️⃣ GENERATE PHASE  
        print("\n✍️ PHASE 3: GENERATE - Writing review...")
        review = generate_review(movie['title'], details.get('plot', ''), source_url=movie.get('url'))
        print(f"✅ REVIEW: {len(review)} characters generated")
        
        # 4️⃣ DRAFT (MOVIE): Check last movie draft and create a new draft if not duplicate
        last_movie = get_last_draft(kind="movie")
        skip_movie = False
        if last_movie and last_movie.get('item', {}).get('url') == movie.get('url'):
            try:
                ts = last_movie.get('timestamp')
                if ts and ts.endswith('Z'):
                    ts_dt = datetime.fromisoformat(ts[:-1])
                else:
                    ts_dt = datetime.fromisoformat(ts)
                age = datetime.utcnow() - ts_dt
                if age < timedelta(days=7):
                    # If the previous draft id is missing on Hashnode (deleted), allow recreation
                    prev_draft_id = last_movie.get('draft_id')
                    if prev_draft_id:
                        exists = draft_exists(prev_draft_id)
                        if not exists:
                            print("⚠️ Previous draft missing on Hashnode — will recreate.")
                        else:
                            print(f"⏭️ Skipping movie draft: same movie was drafted {age.days} day(s) ago.")
                            skip_movie = True
                    else:
                        # no draft id recorded, be conservative and allow recreation
                        print("⚠️ No draft_id recorded for last movie — will recreate.")
            except Exception:
                pass

        if not skip_movie:
            print("\n🌐 PHASE 4: DRAFT - Creating a Hashnode draft for MOVIE (not publishing)...")
            draft_res = publish_to_hashnode(movie['title'], review, publish=False)
            print(f"✅ Movie draft result: {draft_res}")
            save_last_draft(movie, draft_res.get('draft_id'), kind='movie')
            print("✍️ Movie draft saved on Hashnode.")

        # Now handle TV show: same pipeline but separate draft and duplicate check
        print("\n📈 PHASE 1b: RESEARCH - Finding trending TV show...")
        tv = get_trending_tv()
        if not tv or not tv.get('title'):
            print("❌ No trending TV show found")
            return
        print(f"✅ SELECTED TV: {tv['title']}")
        print(f"🔗 {tv['url']}")

        print("\n📝 PHASE 2b: SCRAPE - Gathering TV details...")
        tv_details = get_tv_details(tv['url'])
        tv_preview = tv_details.get('plot', 'No summary')[:150] + "..."
        print(f"✅ TV SUMMARY: {tv_preview}")

        print("\n✍️ PHASE 3b: GENERATE - Writing TV review...")
        tv_review = generate_show_review(tv['title'], tv_details.get('plot', ''), source_url=tv.get('url'))
        print(f"✅ TV REVIEW: {len(tv_review)} characters generated")

        # Duplicate check for TV
        last_tv = get_last_draft(kind="tv")
        skip_tv = False
        if last_tv and last_tv.get('item', {}).get('url') == tv.get('url'):
            try:
                ts = last_tv.get('timestamp')
                if ts and ts.endswith('Z'):
                    ts_dt = datetime.fromisoformat(ts[:-1])
                else:
                    ts_dt = datetime.fromisoformat(ts)
                age = datetime.utcnow() - ts_dt
                if age < timedelta(days=7):
                    prev_draft_id = last_tv.get('draft_id')
                    if prev_draft_id:
                        exists = draft_exists(prev_draft_id)
                        if not exists:
                            print("⚠️ Previous TV draft missing on Hashnode — will recreate.")
                        else:
                            print(f"⏭️ Skipping TV draft: same show was drafted {age.days} day(s) ago.")
                            skip_tv = True
                    else:
                        print("⚠️ No draft_id recorded for last TV — will recreate.")
            except Exception:
                pass

        if not skip_tv:
            print("\n🌐 PHASE 4b: DRAFT - Creating a Hashnode draft for TV (not publishing)...")
            tv_draft = publish_to_hashnode(tv['title'], tv_review, publish=False)
            print(f"✅ TV draft result: {tv_draft}")
            save_last_draft(tv, tv_draft.get('draft_id'), kind='tv')
            print("✍️ TV draft saved on Hashnode.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline cancelled by user.")
