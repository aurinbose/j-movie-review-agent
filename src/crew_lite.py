# src/crew_lite.py - MOVIES + TV TREND ANALYSIS INTEGRATED
from src.agents import (
    get_trending_movie,
    get_movie_details,
    generate_review,
    get_trending_tv,
    get_tv_details,
    generate_show_review,
    resolve_imdb_title_url,  # ✅ Imported from agents
)
from src.hashnode_api import publish_to_hashnode, draft_exists
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone  # ✅ Added timezone
from pathlib import Path
from src.storage import save_last_draft, get_last_draft

load_dotenv()


def run_movie_review_pipeline():
    """🎬📺 COMPLETE CONTENT PIPELINE - MOVIES + TV SHOWS WITH TREND ANALYSIS"""
    print("="*80)
    print(f"🎥📺 CONTENT REVIEW AGENT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # 🎬 MOVIE PIPELINE WITH TREND ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        
        print("\n🎬 MOVIE PIPELINE")
        print("-" * 80)
        
        # PHASE 1: MOVIE TREND ANALYSIS
        print("\n📈 PHASE 1: MOVIE TREND ANALYSIS (Multi-source)...")
        from src.movie_trend_analyst import TrendAnalyst
        
        movie_analyst = TrendAnalyst()
        trending_movies = movie_analyst.analyze_trending_movies(top_n=5)
        
        movie = None
        details = None
        
        # PRIMARY: Use movie trend analysis
        if trending_movies:
            best_movie_data = trending_movies[0]
            movie_title = best_movie_data['title']
            buzz_score = best_movie_data['buzz_score']
            
            print(f"\n🎯 SELECTED MOVIE (Buzz: {buzz_score}):")
            print(f"   {movie_title}")
            
            # Show alternatives
            if len(trending_movies) > 1:
                print(f"\n📊 Other trending movies:")
                for i, alt in enumerate(trending_movies[1:4], 2):
                    print(f"   {i}. {alt['title']} (buzz: {alt['buzz_score']})")
            
            # Resolve IMDb URL
            imdb_search_query = movie_title.replace(' ', '+')
            imdb_search_url = f"https://www.imdb.com/find?q={imdb_search_query}"
            
            print(f"\n🔍 PHASE 2a: Resolving IMDb URL for '{movie_title}'...")
            imdb_title_url = resolve_imdb_title_url(imdb_search_url, movie_title)
            
            if imdb_title_url:
                print(f"✅ Resolved: {imdb_title_url}")
                movie = {
                    'title': movie_title,
                    'url': imdb_title_url,
                    'buzz_score': buzz_score,
                    'source': 'trend_analysis'
                }
                
                print(f"\n📝 PHASE 2b: Scraping IMDb for plot...")
                details = get_movie_details(movie['url'])
            
            # Fallback to other trending movies
            if not details or not details.get('plot'):
                print("⚠️ Failed to fetch movie details, trying alternatives...")
                for fallback in trending_movies[1:3]:
                    print(f"   Attempting: {fallback['title']}")
                    fallback_search_url = f"https://www.imdb.com/find?q={fallback['title'].replace(' ', '+')}"
                    fallback_title_url = resolve_imdb_title_url(fallback_search_url, fallback['title'])
                    
                    if fallback_title_url:
                        details = get_movie_details(fallback_title_url)
                        if details and details.get('plot'):
                            movie = {
                                'title': fallback['title'],
                                'url': fallback_title_url,
                                'buzz_score': fallback['buzz_score'],
                                'source': 'trend_analysis'
                            }
                            movie_title = fallback['title']
                            print(f"✅ Success: {movie_title}")
                            break
        
        # FALLBACK: IMDb moviemeter
        if not movie or not details or not details.get('plot'):
            print("\n🔄 FALLBACK: Using IMDb moviemeter...")
            imdb_movie = get_trending_movie()
            
            if imdb_movie:
                movie = {
                    'title': imdb_movie['title'],
                    'url': imdb_movie['url'],
                    'buzz_score': 0,
                    'source': 'imdb_fallback'
                }
                print(f"🎯 {movie['title']}")
                details = get_movie_details(movie['url'])
        
        # Process movie if valid
        if movie and details and details.get('plot'):
            movie_title = movie['title']
            print(f"\n✅ MOVIE: {movie_title}")
            print(f"📍 Source: {movie.get('source')}")
            print(f"✅ Plot: {details.get('plot', '')[:150]}...")
            
            # Generate review
            print(f"\n✍️ PHASE 3: Generating review...")
            review = generate_review(movie['title'], details.get('plot', ''), source_url=movie.get('url'))
            print(f"✅ Review: {len(review)} chars")
            
            # Draft management
            print("\n🌐 PHASE 4: Draft management...")
            last_movie = get_last_draft(kind="movie")
            skip_movie = False
            
            if last_movie and (last_movie.get('item', {}).get('title') == movie['title'] or 
                              last_movie.get('item', {}).get('url') == movie['url']):
                try:
                    ts = last_movie.get('timestamp')
                    ts_dt = datetime.fromisoformat(ts.rstrip('Z'))
                    age = datetime.now(timezone.utc) - ts_dt  # ✅ FIXED: timezone-aware
                    
                    if age < timedelta(days=7):
                        prev_draft_id = last_movie.get('draft_id')
                        if prev_draft_id and draft_exists(prev_draft_id):
                            print(f"⏭️ SKIPPING: Same movie drafted {age.days} day(s) ago.")
                            skip_movie = True
                except:
                    pass
            
            if not skip_movie:
                print(f"📤 Creating draft: {movie_title}")
                draft_res = publish_to_hashnode(movie['title'], review, publish=False)
                
                if draft_res and draft_res.get('draft_id'):
                    print(f"✅ Draft created: {draft_res.get('draft_id')}")
                    save_last_draft(movie, draft_res.get('draft_id'), kind='movie')
        else:
            print("❌ Movie pipeline failed")
        
        # ═══════════════════════════════════════════════════════════════
        # 📺 TV SHOW PIPELINE WITH TREND ANALYSIS
        # ═══════════════════════════════════════════════════════════════
        
        print("\n" + "="*80)
        print("📺 TV SHOW PIPELINE")
        print("-" * 80)
        
        # PHASE 1: TV TREND ANALYSIS
        print("\n📈 PHASE 1: TV TREND ANALYSIS (Multi-source)...")
        from src.tv_trend_analyst import TVTrendAnalyst
        
        tv_analyst = TVTrendAnalyst()
        trending_shows = tv_analyst.analyze_trending_shows(top_n=5)
        
        tv = None
        tv_details = None
        
        # PRIMARY: Use TV trend analysis
        if trending_shows:
            best_show_data = trending_shows[0]
            show_title = best_show_data['title']
            buzz_score = best_show_data['buzz_score']
            
            print(f"\n🎯 SELECTED TV SHOW (Buzz: {buzz_score}):")
            print(f"   {show_title}")
            
            # Show alternatives
            if len(trending_shows) > 1:
                print(f"\n📊 Other trending shows:")
                for i, alt in enumerate(trending_shows[1:4], 2):
                    print(f"   {i}. {alt['title']} (buzz: {alt['buzz_score']})")
            
            # Resolve IMDb URL for TV
            imdb_search_query = show_title.replace(' ', '+')
            imdb_search_url = f"https://www.imdb.com/find?q={imdb_search_query}"
            
            print(f"\n🔍 PHASE 2a: Resolving IMDb URL for '{show_title}'...")
            imdb_title_url = resolve_imdb_title_url(imdb_search_url, show_title)
            
            if imdb_title_url:
                print(f"✅ Resolved: {imdb_title_url}")
                tv = {
                    'title': show_title,
                    'url': imdb_title_url,
                    'buzz_score': buzz_score,
                    'source': 'trend_analysis'
                }
                
                print(f"\n📝 PHASE 2b: Scraping IMDb for summary...")
                tv_details = get_tv_details(tv['url'])
            
            # Fallback to other trending shows
            if not tv_details or not tv_details.get('plot'):
                print("⚠️ Failed to fetch show details, trying alternatives...")
                for fallback in trending_shows[1:3]:
                    print(f"   Attempting: {fallback['title']}")
                    fallback_search_url = f"https://www.imdb.com/find?q={fallback['title'].replace(' ', '+')}"
                    fallback_title_url = resolve_imdb_title_url(fallback_search_url, fallback['title'])
                    
                    if fallback_title_url:
                        tv_details = get_tv_details(fallback_title_url)
                        if tv_details and tv_details.get('plot'):
                            tv = {
                                'title': fallback['title'],
                                'url': fallback_title_url,
                                'buzz_score': fallback['buzz_score'],
                                'source': 'trend_analysis'
                            }
                            show_title = fallback['title']
                            print(f"✅ Success: {show_title}")
                            break
        
        # FALLBACK: IMDb TV trending
        if not tv or not tv_details or not tv_details.get('plot'):
            print("\n🔄 FALLBACK: Using IMDb TV trending...")
            imdb_tv = get_trending_tv()
            
            if imdb_tv:
                tv = {
                    'title': imdb_tv['title'],
                    'url': imdb_tv['url'],
                    'buzz_score': 0,
                    'source': 'imdb_fallback'
                }
                print(f"🎯 {tv['title']}")
                tv_details = get_tv_details(tv['url'])
        
        # Process TV show if valid
        if tv and tv_details and tv_details.get('plot'):
            show_title = tv['title']
            print(f"\n✅ TV SHOW: {show_title}")
            print(f"📍 Source: {tv.get('source')}")
            print(f"✅ Summary: {tv_details.get('plot', '')[:150]}...")
            
            # Generate review
            print(f"\n✍️ PHASE 3: Generating TV review...")
            tv_review = generate_show_review(tv['title'], tv_details.get('plot', ''), source_url=tv.get('url'))
            print(f"✅ Review: {len(tv_review)} chars")
            
            # Draft management
            print("\n🌐 PHASE 4: TV Draft management...")
            last_tv = get_last_draft(kind="tv")
            skip_tv = False
            
            if last_tv and (last_tv.get('item', {}).get('title') == tv['title'] or 
                           last_tv.get('item', {}).get('url') == tv['url']):
                try:
                    ts = last_tv.get('timestamp')
                    ts_dt = datetime.fromisoformat(ts.rstrip('Z'))
                    age = datetime.now(timezone.utc) - ts_dt  # ✅ FIXED: timezone-aware
                    
                    if age < timedelta(days=7):
                        prev_draft_id = last_tv.get('draft_id')
                        if prev_draft_id and draft_exists(prev_draft_id):
                            print(f"⏭️ SKIPPING: Same show drafted {age.days} day(s) ago.")
                            skip_tv = True
                except:
                    pass
            
            if not skip_tv:
                print(f"📤 Creating TV draft: {show_title}")
                tv_draft = publish_to_hashnode(tv['title'], tv_review, publish=False)
                
                if tv_draft and tv_draft.get('draft_id'):
                    print(f"✅ TV draft created: {tv_draft.get('draft_id')}")
                    save_last_draft(tv, tv_draft.get('draft_id'), kind='tv')
        else:
            print("❌ TV pipeline failed")
        
        # ═══════════════════════════════════════════════════════════════
        # PIPELINE COMPLETION
        # ═══════════════════════════════════════════════════════════════
        
        print("\n" + "="*80)
        print("🎉 PIPELINE COMPLETED")
        print("="*80)
        if movie:
            print(f"🎬 Movie: {movie.get('title')} (source: {movie.get('source')})")
            if movie.get('buzz_score'):
                print(f"   Buzz: {movie['buzz_score']}")
        if tv:
            print(f"📺 TV: {tv.get('title')} (source: {tv.get('source')})")
            if tv.get('buzz_score'):
                print(f"   Buzz: {tv['buzz_score']}")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline cancelled by user.")
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_movie_review_pipeline()
