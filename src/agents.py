# src/agents.py
import os
import logging
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from groq import Groq, BadRequestError, NotFoundError, AuthenticationError


load_dotenv()

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# Recommended fallback when Groq reports a model is decommissioned
RECOMMENDED_MODEL = os.getenv("GROQ_RECOMMENDED_MODEL", "llama-3.3-70b-versatile")

# Logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Initialize Groq client if key present
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        logger.exception("Failed to initialize Groq client")
        groq_client = None


def get_trending_movie():
    """
    Return a simple dict: {title, url}
    Currently: just takes the first movie from IMDb Trending.
    Later you can switch to a true 'trending' page.
    """
    # Try multiple IMDb pages in order of preference — moviemeter first,
    # then fallback to Top 250. This helps if one page is blocked or has
    # changed layout.
    urls = [
        "https://www.imdb.com/chart/moviemeter/",
        "https://www.imdb.com/chart/top/",
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    # A set of selectors to try on each page. We try more specific selectors
    # first, then fall back to a broad title link selector.
    selectors = [
        "table.chart.full-width tr td.titleColumn a",
        "td.titleColumn a",
        ".lister-list .lister-item-header a",
        "h3.lister-item-header a",
        "a[data-testid='title-link']",
        "a[href^='/title/']",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception:
            logger.warning("Failed to fetch IMDb page %s", url)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        first_row = None
        for sel in selectors:
            first_row = soup.select_one(sel)
            if first_row:
                break

        if first_row:
            # Robust title extraction: prefer visible text, then common attributes,
            # then image alt text (some IMDb listings use images/links without text).
            title = first_row.get_text(strip=True) or first_row.get("title") or first_row.get("aria-label")
            if not title:
                img = first_row.find("img")
                if img and img.get("alt"):
                    title = img.get("alt")

            title = (title or "").strip()
            link = "https://www.imdb.com" + first_row.get("href", "").split("?")[0]
            logger.info("Selected trending movie: %s (%s)", title, link)
            return {"title": title, "url": link}

    # If we get here nothing matched on any page — return None so callers
    # (like `crew_lite`) can handle the absence gracefully.
    logger.warning("Could not find a trending movie on IMDb using any known selector")
    return None


def get_trending_tv():
    """Return top trending TV show from IMDb TV meter as {title, url} or None."""
    url = "https://www.imdb.com/chart/tvmeter/"
    headers = {"User-Agent": "Mozilla/5.0"}
    selectors = [
        "table.chart.full-width tr td.titleColumn a",
        "td.titleColumn a",
        "a[data-testid='title-link']",
        "a[href^='/title/']",
    ]

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception:
        logger.warning("Failed to fetch IMDb TV meter %s", url)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    first_row = None
    for sel in selectors:
        first_row = soup.select_one(sel)
        if first_row:
            break

    if not first_row:
        logger.warning("Could not find top TV show on IMDb TV meter")
        return None

    title = first_row.get_text(strip=True) or first_row.get("title") or first_row.get("aria-label")
    if not title:
        img = first_row.find("img")
        if img and img.get("alt"):
            title = img.get("alt")
    title = (title or "").strip()
    link = "https://www.imdb.com" + first_row.get("href", "").split("?")[0]
    logger.info("Selected trending TV show: %s (%s)", title, link)
    return {"title": title, "url": link}


def get_movie_details(movie_url: str):
    """
    Scrape the movie page for a plot summary (very simple).
    This is intentionally minimal to keep it beginner-friendly.
    """
    if not movie_url:
        raise ValueError("movie_url is required")

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(movie_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.exception("Failed to fetch movie details from %s", movie_url)
        raise
    soup = BeautifulSoup(resp.text, "html.parser")

    # Very rough selectors – may need adjustment as IMDb changes:
    plot_elem = soup.select_one("span[data-testid='plot-l']")
    if not plot_elem:
        plot_elem = soup.select_one("span[data-testid='plot-xl']")
    plot = plot_elem.text.strip() if plot_elem else "Plot not found."

    return {"plot": plot}


def get_tv_details(tv_url: str):
    """Scrape a TV show page for a summary/plot (reuses movie selectors)."""
    # IMDb TV show pages generally contain similar plot selectors as movies
    return get_movie_details(tv_url)


def generate_review(title: str, plot: str, source_url: str | None = None) -> str:
    """Generate AI review using Groq (or dummy if no API key).

    Args:
        title: Movie title string
        plot: Plot summary
        source_url: optional IMDb movie URL to scrape reference reviews from
    """
    if not groq_client:
        return f"""## {title} - AI Movie Review

This film tells {plot[:100]}... 

**Rating: ★★★★☆** 
A timeless classic that resonates with audiences worldwide."""

    ref_reviews = []
    if source_url:
        try:
            ref_reviews = get_similar_reviews(source_url, max_reviews=3)
        except Exception:
            logger.exception("Failed to fetch reference reviews for %s", source_url)

    references_block = ""
    if ref_reviews:
        references_block = "\n\nREFERENCE REVIEWS:\n"
        for i, r in enumerate(ref_reviews, start=1):
            # keep snippets short
            snippet = (r.strip()[:800]).replace('\n', ' ')
            references_block += f"{i}) {snippet}\n"

    prompt = (
        f"Write a 400-600 word original movie review for '{title}'.\n\n"
        f"PLOT SUMMARY: {plot}\n\n"
        "Your review should:\n"
        "1. Start with an engaging hook\n"
        "2. Analyze themes, characters, direction\n"
        "3. Give honest critique (strengths + weaknesses)\n"
        "4. End with rating (★ out of ★★★★★) and recommendation\n\n"
        "Write in engaging, conversational style like a professional film critic."
    )
    if references_block:
        prompt = prompt + references_block

    # Try models from GROQ_MODEL (comma-separated) and fall back to a
    # recommended model if Groq reports decommissioning.
    models = [m.strip() for m in (GROQ_MODEL or "").split(",") if m.strip()]
    if not models:
        models = [RECOMMENDED_MODEL]

    completion = None
    tried = []
    for model in models:
        tried.append(model)
        try:
            completion = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a witty, insightful film critic."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800,
            )
            logger.info("Groq completion succeeded using model %s", model)
            break
        except BadRequestError as e:
            msg = str(e).lower()
            logger.warning("Groq BadRequest for model %s: %s", model, msg)
            if ("decommissioned" in msg or "model_decommissioned" in msg) and RECOMMENDED_MODEL not in models:
                logger.info("Appending recommended model %s and retrying", RECOMMENDED_MODEL)
                models.append(RECOMMENDED_MODEL)
                continue
            return f"[REVIEW ERROR] Groq request failed: BadRequest ({model})"
        except NotFoundError:
            logger.warning("Groq model not found: %s (trying next)", model)
            continue
        except AuthenticationError:
            logger.exception("Groq authentication failed")
            return "[REVIEW ERROR] Groq authentication failed: check GROQ_API_KEY"
        except Exception as e:
            logger.exception("Groq API call failed for model %s", model)
            return f"[REVIEW ERROR] Groq request failed: {e.__class__.__name__}"

    if completion is None:
        logger.error("No Groq completion produced; models tried: %s", ",".join(tried))
        return "[REVIEW ERROR] Groq request failed: no completion returned"

    try:
        return completion.choices[0].message.content.strip()
    except Exception:
        logger.exception("Failed to parse Groq response")
        return "[REVIEW ERROR] Failed to parse Groq response"

def generate_show_review(title: str, plot: str, source_url: str | None = None) -> str:
    """Generate a TV show review using the same LLM pipeline but a TV-specific prompt.

    Args:
        title: Show title
        plot: Series summary
        source_url: optional IMDb show URL to scrape reference reviews from
    """
    ref_reviews = []
    if source_url:
        try:
            ref_reviews = get_similar_reviews(source_url, max_reviews=3)
        except Exception:
            logger.exception("Failed to fetch reference reviews for TV %s", source_url)

    references_block = ""
    if ref_reviews:
        references_block = "\n\nREFERENCE REVIEWS:\n"
        for i, r in enumerate(ref_reviews, start=1):
            snippet = (r.strip()[:800]).replace('\n', ' ')
            references_block += f"{i}) {snippet}\n"

    if not groq_client:
        base = f"## {title} - AI TV Review\n\nA TV show about {plot[:100]}...\n\n**Rating: ★★★★☆**"
        return base + references_block

    prompt = (
        f"Write a 400-600 word original TV show review for '{title}'.\n\n"
        f"SERIES SUMMARY: {plot}\n\n"
        "Your review should:\n"
        "1. Start with an engaging hook\n"
        "2. Discuss season/episode structure, performances, themes\n"
        "3. Give honest critique (strengths + weaknesses)\n"
        "4. End with rating (★ out of ★★★★★) and recommendation\n\n"
        "Write in engaging, conversational style like a professional TV critic."
    )

    # Reuse same model loop as generate_review
    models = [m.strip() for m in (GROQ_MODEL or "").split(",") if m.strip()]
    if not models:
        models = [RECOMMENDED_MODEL]

    completion = None
    tried = []
    for model in models:
        tried.append(model)
        try:
            completion = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a witty, insightful TV critic."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800,
            )
            logger.info("Groq completion (TV) succeeded using model %s", model)
            break
        except BadRequestError as e:
            msg = str(e).lower()
            logger.warning("Groq BadRequest for model %s: %s", model, msg)
            if ("decommissioned" in msg or "model_decommissioned" in msg) and RECOMMENDED_MODEL not in models:
                models.append(RECOMMENDED_MODEL)
                continue
            return f"[REVIEW ERROR] Groq request failed: BadRequest ({model})"
        except NotFoundError:
            continue
        except AuthenticationError:
            logger.exception("Groq authentication failed")
            return "[REVIEW ERROR] Groq authentication failed: check GROQ_API_KEY"
        except Exception as e:
            logger.exception("Groq API call failed for model %s", model)
            return f"[REVIEW ERROR] Groq request failed: {e.__class__.__name__}"

    if completion is None:
        logger.error("No Groq completion produced for TV; models tried: %s", ",".join(tried))
        return "[REVIEW ERROR] Groq request failed: no completion returned"

    try:
        return completion.choices[0].message.content.strip()
    except Exception:
        logger.exception("Failed to parse Groq response (TV)")
        return "[REVIEW ERROR] Failed to parse Groq response"


def extract_imdb_id(url: str) -> str | None:
    import re
    if not url:
        return None
    m = re.search(r"/title/(tt\d+)", url)
    if m:
        return m.group(1)
    return None


def get_similar_reviews(source_url: str, max_reviews: int = 3) -> list:
    """Scrape top user review snippets from the IMDb reviews page for the given title URL.

    Returns a list of text snippets (may be empty).
    """
    tt = extract_imdb_id(source_url)
    if not tt:
        logger.debug("No IMDb id found in URL %s", source_url)
        return []

    reviews_url = f"https://www.imdb.com/title/{tt}/reviews"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(reviews_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception:
        logger.warning("Failed to fetch IMDb reviews page %s", reviews_url)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    selectors = [
        "div.review-container div.content div.text",
        "div.text.show-more__control",
        "div.review-container .content",
    ]

    snippets = []
    for sel in selectors:
        elems = soup.select(sel)
        for e in elems:
            text = e.get_text(separator=" ", strip=True)
            if text:
                snippets.append(text)
            if len(snippets) >= max_reviews:
                break
        if len(snippets) >= max_reviews:
            break

    # fallback: try paragraphs
    if not snippets:
        for p in soup.select(".ipl-zebra-list__item p"):
            t = p.get_text(strip=True)
            if t:
                snippets.append(t)
            if len(snippets) >= max_reviews:
                break

    return snippets[:max_reviews]

