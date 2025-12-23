# src/trend_analyst.py - OPTIMIZED: Better movie filtering & scraping
import requests
from bs4 import BeautifulSoup
import cloudscraper
from collections import Counter
import re
import json
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

class TrendAnalyst:
    """🧠 2025-Proof: Direct scraping with intelligent movie filtering"""
    
    def __init__(self):
        self.movie_keywords = {
            'exclude': ['cakeday', 'megathread', 'discussion', 'official', 'trailer', 
                       'review', 'question', 'help', 'where', 'how', 'what', 'why',
                       'reddit', 'post', 'thread', 'ama', 'announcement'],
            'movie_indicators': ['movie', 'film', 'cinema', 'watched', 'directed by']
        }
        print("✅ Trend Analyst ready (Optimized filtering)")
    
    def analyze_trending_movies(self, top_n=5) -> list:
        buzz_scores = Counter()
        
        # 1. GOOGLE TRENDS
        print("📈 Scraping Google Trends...")
        google_movies = self._get_google_trends_scrape()
        print(f"[debug] google_movies: {len(google_movies)} items")
        for movie, score in google_movies.items():
            buzz_scores[movie] += score * 4
        
        # 2. REDDIT SCRAPING
        print("🔍 Scraping Reddit...")
        reddit_movies = self._get_reddit_scrape()
        print(f"[debug] reddit_movies: {len(reddit_movies)} items")
        for movie, score in reddit_movies.items():
            buzz_scores[movie] += score * 2
        
        # 3. LETTERBOXD
        print("🎥 Scraping Letterboxd...")
        letterboxd_movies = self._get_letterboxd_trending()
        print(f"[debug] letterboxd_movies: {len(letterboxd_movies)} items")
        for movie in letterboxd_movies[:8]:
            buzz_scores[movie] += 15
        
        # 4. IMDB MOVIEMETER
        print("🎬 Scraping IMDb...")
        imdb_movies = self._get_imdb_trending()
        print(f"[debug] imdb_movies: {len(imdb_movies)} items")
        for movie in imdb_movies[:5]:
            buzz_scores[movie] += 12
        
        # Filter out non-movies and get top results
        top_movies = [(m, s) for m, s in buzz_scores.most_common(top_n * 3) 
                      if self._is_likely_movie(m)][:top_n]
        
        print(f"\n🎯 TOP {top_n} BUZZING MOVIES:")
        for i, (movie, score) in enumerate(top_movies, 1):
            print(f"  {i}. {movie} 🔥 {score}")
        
        return [{"title": movie, "buzz_score": score} for movie, score in top_movies]
    
    def _is_likely_movie(self, title: str) -> bool:
        """🎯 CRITICAL: Filter out non-movie titles"""
        if not title or len(title) < 3:
            return False
        
        title_lower = title.lower()
        
        # Exclude common Reddit/forum phrases
        for keyword in self.movie_keywords['exclude']:
            if keyword in title_lower:
                return False
        
        # Too many words = likely a discussion post
        word_count = len(title.split())
        if word_count > 8:
            return False
        
        # Must have proper title case for at least 2 words
        capitalized_words = sum(1 for word in title.split() if word and word[0].isupper())
        if capitalized_words < 2:
            return False
        
        # Reject if starts with common post patterns
        reject_starts = ['how', 'what', 'where', 'why', 'when', 'is', 'are', 'do', 'does']
        first_word = title.split()[0].lower()
        if first_word in reject_starts:
            return False
        
        return True
    
    def _get_google_trends_scrape(self) -> dict:
        """✅ FIXED: Better Google Trends parsing"""
        movies = Counter()
        scraper = cloudscraper.create_scraper()
        
        try:
            url = "https://trends.google.com/trends/trendingsearches/daily?geo=US"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            resp = scraper.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"[debug] Google Trends: status {resp.status_code}")
                return {}
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Try multiple selectors (Google changes these)
            selectors = [
                'div.feed-item span.title',
                'div.title a',
                'div[class*="title"]',
                'span[class*="title"]'
            ]
            
            for selector in selectors:
                items = soup.select(selector)[:20]
                if items:
                    for item in items:
                        text = item.get_text().strip()
                        if 'movie' in text.lower() or 'film' in text.lower():
                            movie = self._extract_movie_title(text)
                            if movie and self._is_likely_movie(movie):
                                movies[movie] += 10
                    break
            
        except Exception as e:
            print(f"[debug] Google Trends error: {e}")
        
        return dict(movies.most_common(8))
    
    def _get_reddit_scrape(self) -> dict:
        """✅ FIXED: Better Reddit movie extraction"""
        movies = Counter()
        subreddits = ['movies', 'flicks', 'TrueFilm', 'MovieSuggestions']
        
        scraper = cloudscraper.create_scraper(delay=1)
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; MovieBot/1.0)'}
        
        for subreddit in subreddits:
            try:
                url = f"https://old.reddit.com/r/{subreddit}/hot/"
                resp = scraper.get(url, headers=headers, timeout=12)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Get post titles
                for post in soup.find_all('div', class_='thing')[:25]:
                    title_elem = post.find('a', class_='title')
                    if not title_elem:
                        continue
                    
                    text = title_elem.get_text().strip()
                    
                    # Extract movie from various patterns
                    movie = self._extract_movie_from_reddit(text)
                    if movie and self._is_likely_movie(movie):
                        movies[movie] += 2
                
            except Exception as e:
                print(f"[debug] reddit r/{subreddit}: {e}")
                continue
        
        return dict(movies.most_common(12))
    
    def _extract_movie_from_reddit(self, text: str) -> str | None:
        """🎯 Extract movie titles from Reddit post patterns"""
        # Pattern: "Movie Title" (with quotes)
        m = re.search(r'["\']([A-Z][^"\']{3,50})["\']', text)
        if m:
            return m.group(1).strip()
        
        # Pattern: Movie Title (2024) or Movie Title (2023)
        m = re.search(r'([A-Z][A-Za-z\s\':&-]{3,50})\s*\((202[0-9])\)', text)
        if m:
            return m.group(1).strip()
        
        # Pattern: [Discussion] Movie Title or Movie Title [Discussion]
        m = re.search(r'\[(?:Discussion|Review|Official)\]\s*([A-Z][A-Za-z\s\':&-]{3,50})', text)
        if m:
            return m.group(1).strip()
        
        m = re.search(r'([A-Z][A-Za-z\s\':&-]{3,50})\s*\[(?:Discussion|Review)', text)
        if m:
            return m.group(1).strip()
        
        # Pattern: Just watched/saw "Movie" or Movie is...
        m = re.search(r'(?:watched|saw|loved|hated)\s+["\']?([A-Z][A-Za-z\s\':&-]{3,50})["\']?(?:\s+(?:is|was|and))?', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        
        return None
    
    def _get_letterboxd_trending(self) -> list:
        """✅ FIXED: More robust Letterboxd scraping"""
        try:
            url = 'https://letterboxd.com/films/popular/this/week/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=12)
            
            if resp.status_code != 200:
                print(f"[debug] Letterboxd: status {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            titles = []
            
            # Try multiple selectors
            selectors = [
                'h2.headline-2',
                'img.image',  # alt text has movie titles
                'a[href*="/film/"]'
            ]
            
            for selector in selectors:
                if selector == 'img.image':
                    for img in soup.select(selector):
                        title = img.get('alt', '').strip()
                        if title and len(title) > 2:
                            titles.append(title)
                else:
                    for elem in soup.select(selector):
                        title = elem.get_text().strip()
                        if title and len(title) > 2:
                            titles.append(title)
                
                if len(titles) > 10:
                    break
            
            return list(set(titles))[:15]
            
        except Exception as e:
            print(f"[debug] Letterboxd error: {e}")
            return []
    
    def _get_imdb_trending(self) -> list:
        """✅ FIXED: More reliable IMDb scraping"""
        try:
            url = 'https://www.imdb.com/chart/moviemeter/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            resp = requests.get(url, headers=headers, timeout=12)
            
            if resp.status_code != 200:
                print(f"[debug] IMDb: status {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            titles = []
            
            # Try both old and new IMDb structures
            selectors = [
                'td.titleColumn a',
                'h3.ipc-title__text',
                'a.ipc-title-link-wrapper'
            ]
            
            for selector in selectors:
                for elem in soup.select(selector):
                    title = elem.get_text().strip()
                    # Remove ranking numbers like "1. Movie"
                    title = re.sub(r'^\d+\.\s*', '', title)
                    if title and len(title) > 2 and not title.isdigit():
                        titles.append(title)
                
                if len(titles) > 5:
                    break
            
            return titles[:10]
            
        except Exception as e:
            print(f"[debug] IMDb error: {e}")
            return []
    
    def _extract_movie_title(self, text: str) -> str | None:
        """General movie title extraction"""
        if not text or len(text) < 5:
            return None
        
        # Quoted titles
        m = re.search(r'["\']([^"\']{3,})["\']', text)
        if m:
            return m.group(1).strip()
        
        # Title (YEAR)
        m = re.search(r'([A-Z][a-zA-Z\s\':&-]{3,50})\s*\(202[0-9]\)', text)
        if m:
            return m.group(1).strip()
        
        # Capitalized phrases (2-6 words)
        words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
        if len(words) >= 2:
            title = ' '.join(words[:6])
            if 8 <= len(title) <= 60:
                return title
        
        return None

if __name__ == "__main__":
    analyst = TrendAnalyst()
    trending = analyst.analyze_trending_movies(top_n=5)
    print("\n💾 JSON:", json.dumps(trending, indent=2))