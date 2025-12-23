# src/tv_trend_analyst.py - TV SHOW TREND ANALYSIS
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

class TVTrendAnalyst:
    """📺 2025-Proof: Direct TV show trend scraping (Reddit + IMDb + Trakt + Letterboxd)"""
    
    def __init__(self):
        self.tv_keywords = {
            'exclude': ['cakeday', 'megathread', 'help', 'where', 'how', 'what', 'why',
                       'reddit', 'post', 'thread', 'ama', 'announcement', 'trailer only'],
            'tv_indicators': ['series', 'season', 'episode', 'tv show', 'television', 
                            'streaming', 'netflix', 'hbo', 'apple tv', 'prime video']
        }
        print("✅ TV Trend Analyst ready (Multi-source TV scraping)")
    
    def analyze_trending_shows(self, top_n=5) -> list:
        """Analyze trending TV shows from multiple sources"""
        buzz_scores = Counter()
        
        # 1. REDDIT TV COMMUNITIES
        print("🔍 Scraping Reddit TV communities...")
        reddit_shows = self._get_reddit_tv_scrape()
        print(f"[debug] reddit_shows: {len(reddit_shows)} items")
        for show, score in reddit_shows.items():
            buzz_scores[show] += score * 3  # High weight for Reddit TV communities
        
        # 2. IMDB TV METER
        print("📺 Scraping IMDb TV Meter...")
        imdb_shows = self._get_imdb_tv_trending()
        print(f"[debug] imdb_shows: {len(imdb_shows)} items")
        for show in imdb_shows[:8]:
            buzz_scores[show] += 20  # Highest weight - authoritative source
        
        # 3. TRAKT.TV
        print("🎬 Scraping Trakt.tv trending...")
        trakt_shows = self._get_trakt_trending()
        print(f"[debug] trakt_shows: {len(trakt_shows)} items")
        for show in trakt_shows[:10]:
            buzz_scores[show] += 15
        
        # 4. LETTERBOXD TV/SERIES
        print("📽️ Scraping Letterboxd series...")
        letterboxd_shows = self._get_letterboxd_series()
        print(f"[debug] letterboxd_shows: {len(letterboxd_shows)} items")
        for show in letterboxd_shows[:8]:
            buzz_scores[show] += 12
        
        # 5. GOOGLE TRENDS TV
        print("📈 Scraping Google Trends for TV...")
        google_shows = self._get_google_trends_tv()
        print(f"[debug] google_shows: {len(google_shows)} items")
        for show, score in google_shows.items():
            buzz_scores[show] += score * 2
        
        # Filter out non-TV shows and get top results
        top_shows = [(s, sc) for s, sc in buzz_scores.most_common(top_n * 3) 
                     if self._is_likely_tv_show(s)][:top_n]
        
        print(f"\n🎯 TOP {top_n} BUZZING TV SHOWS:")
        for i, (show, score) in enumerate(top_shows, 1):
            print(f"  {i}. {show} 🔥 {score}")
        
        return [{"title": show, "buzz_score": score} for show, score in top_shows]
    
    def _is_likely_tv_show(self, title: str) -> bool:
        """🎯 Filter out non-TV show titles"""
        if not title or len(title) < 3:
            return False
        
        title_lower = title.lower()
        
        # Exclude common Reddit/forum phrases
        for keyword in self.tv_keywords['exclude']:
            if keyword in title_lower:
                return False
        
        # Too many words = likely a discussion post
        word_count = len(title.split())
        if word_count > 10:
            return False
        
        # Must have proper title case for at least 2 words
        capitalized_words = sum(1 for word in title.split() if word and word[0].isupper())
        if capitalized_words < 2:
            return False
        
        # Reject if starts with common post patterns
        reject_starts = ['how', 'what', 'where', 'why', 'when', 'is', 'are', 'do', 'does', 'can']
        first_word = title.split()[0].lower()
        if first_word in reject_starts:
            return False
        
        return True
    
    def _get_reddit_tv_scrape(self) -> dict:
        """✅ Scrape TV-focused Reddit communities"""
        shows = Counter()
        subreddits = [
            'television',
            'tvshows', 
            'NetflixBestOf',
            'TVDetails',
            'TheLastOfUsHBO',
            'HouseOfTheDragon',
            'Severance',
            'SuccessionTV',
            'TheBear',
            'TheBoysTV'
        ]
        
        scraper = cloudscraper.create_scraper(delay=1)
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; TVBot/1.0)'}
        
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
                    
                    # Extract TV show from various patterns
                    show = self._extract_show_from_reddit(text)
                    if show and self._is_likely_tv_show(show):
                        shows[show] += 2
                
            except Exception as e:
                print(f"[debug] reddit r/{subreddit}: {e}")
                continue
        
        return dict(shows.most_common(15))
    
    def _extract_show_from_reddit(self, text: str) -> str | None:
        """🎯 Extract TV show titles from Reddit post patterns"""
        # Pattern: "Show Title" (with quotes)
        m = re.search(r'["\']([A-Z][^"\']{3,60})["\']', text)
        if m:
            candidate = m.group(1).strip()
            # Verify it's not just a quote from the show
            if not any(word in candidate.lower() for word in ['said', 'says', 'told', 'revealed']):
                return candidate
        
        # Pattern: Show Title - Season X Episode Y
        m = re.search(r'([A-Z][A-Za-z\s\':&-]{3,50})\s*[-–]\s*[Ss](?:eason)?\s*\d+', text)
        if m:
            return m.group(1).strip()
        
        # Pattern: [Show Title] Discussion or Show Title [Discussion]
        m = re.search(r'\[([A-Z][A-Za-z\s\':&-]{3,50})\]', text)
        if m:
            return m.group(1).strip()
        
        # Pattern: Show Title S01E01 or Show Title 1x01
        m = re.search(r'([A-Z][A-Za-z\s\':&-]{3,50})\s*[Ss]\d+[Ee]\d+', text)
        if m:
            return m.group(1).strip()
        
        m = re.search(r'([A-Z][A-Za-z\s\':&-]{3,50})\s*\d+x\d+', text)
        if m:
            return m.group(1).strip()
        
        # Pattern: Just watched/binged "Show" or Show is...
        m = re.search(r'(?:watched|binged|finished|loved|hated)\s+["\']?([A-Z][A-Za-z\s\':&-]{3,50})["\']?(?:\s+(?:is|was|and))?', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        
        return None
    
    def _get_imdb_tv_trending(self) -> list:
        """✅ Scrape IMDb TV Meter (most authoritative)"""
        try:
            url = 'https://www.imdb.com/chart/tvmeter/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            resp = requests.get(url, headers=headers, timeout=12)
            
            if resp.status_code != 200:
                print(f"[debug] IMDb TV: status {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            titles = []
            
            # Try multiple selectors for both old and new IMDb layouts
            selectors = [
                'td.titleColumn a',
                'h3.ipc-title__text',
                'a.ipc-title-link-wrapper',
                'li.ipc-metadata-list-summary-item a'
            ]
            
            for selector in selectors:
                for elem in soup.select(selector):
                    title = elem.get_text().strip()
                    # Remove ranking numbers like "1. Show"
                    title = re.sub(r'^\d+\.\s*', '', title)
                    if title and len(title) > 2 and not title.isdigit():
                        titles.append(title)
                
                if len(titles) > 5:
                    break
            
            return titles[:15]
            
        except Exception as e:
            print(f"[debug] IMDb TV error: {e}")
            return []
    
    def _get_trakt_trending(self) -> list:
        """✅ Scrape Trakt.tv (TV tracking community)"""
        try:
            url = 'https://trakt.tv/shows/trending'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=12)
            
            if resp.status_code != 200:
                print(f"[debug] Trakt: status {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            titles = []
            
            # Trakt uses data-title attributes and h3 tags
            selectors = [
                'h3.show-title a',
                'div.titles h3 a',
                'a[href*="/shows/"]',
            ]
            
            for selector in selectors:
                for elem in soup.select(selector):
                    title = elem.get_text().strip()
                    if title and len(title) > 2:
                        titles.append(title)
                
                if len(titles) > 8:
                    break
            
            return list(set(titles))[:15]
            
        except Exception as e:
            print(f"[debug] Trakt error: {e}")
            return []
    
    def _get_letterboxd_series(self) -> list:
        """✅ Scrape Letterboxd miniseries/limited series"""
        try:
            # Letterboxd doesn't have dedicated TV section, but has miniseries
            url = 'https://letterboxd.com/search/miniseries/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=12)
            
            if resp.status_code != 200:
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            titles = []
            
            for a in soup.select('a[href*="/film/"]'):
                title = a.get_text().strip()
                if title and len(title) > 2:
                    titles.append(title)
            
            return list(set(titles))[:10]
            
        except Exception as e:
            print(f"[debug] Letterboxd error: {e}")
            return []
    
    def _get_google_trends_tv(self) -> dict:
        """✅ Google Trends filtered for TV shows"""
        shows = Counter()
        scraper = cloudscraper.create_scraper()
        
        try:
            url = "https://trends.google.com/trends/trendingsearches/daily?geo=US"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            resp = scraper.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return {}
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract trending search titles
            selectors = [
                'div.feed-item span.title',
                'div.title a',
                'div[class*="title"]',
            ]
            
            for selector in selectors:
                items = soup.select(selector)[:20]
                if items:
                    for item in items:
                        text = item.get_text().strip()
                        text_lower = text.lower()
                        
                        # Filter for TV-related content
                        if any(indicator in text_lower for indicator in self.tv_keywords['tv_indicators']):
                            show = self._extract_show_title(text)
                            if show and self._is_likely_tv_show(show):
                                shows[show] += 8
                    break
            
        except Exception as e:
            print(f"[debug] Google Trends TV error: {e}")
        
        return dict(shows.most_common(10))
    
    def _extract_show_title(self, text: str) -> str | None:
        """General TV show title extraction"""
        if not text or len(text) < 5:
            return None
        
        # Quoted titles
        m = re.search(r'["\']([^"\']{3,})["\']', text)
        if m:
            return m.group(1).strip()
        
        # Title (Year) or Title - Season X
        m = re.search(r'([A-Z][a-zA-Z\s\':&-]{3,50})\s*(?:\(202[0-9]\)|[-–]\s*[Ss]eason)', text)
        if m:
            return m.group(1).strip()
        
        # Capitalized phrases (2-8 words)
        words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
        if 2 <= len(words) <= 8:
            title = ' '.join(words[:8])
            if 8 <= len(title) <= 80:
                return title
        
        return None


if __name__ == "__main__":
    analyst = TVTrendAnalyst()
    trending = analyst.analyze_trending_shows(top_n=5)
    print("\n💾 JSON:", json.dumps(trending, indent=2))