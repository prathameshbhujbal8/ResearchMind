import os
import time
import json
import datetime
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

BLOCKED_DOMAINS = [
    "twitter.com",
    "x.com",
    "instagram.com",
    "facebook.com",
    "reddit.com",
    "quora.com",
    "pinterest.com",
    "tiktok.com",
    "youtube.com",
    "linkedin.com",
    "threads.net",
    "snapchat.com",
    "glassdoor.com",
    "ambitionbox.com",
    "indeed.com",
    "rocketreach.co",
    "zoominfo.com"
]


def is_blocked(url):
    # FIX: urlparse instead of substring check
    # Prevents "x.com" from blocking "example.com"
    try:
        hostname = urlparse(url).hostname or ""
        return any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in BLOCKED_DOMAINS
        )
    except Exception:
        return False


def generate_search_queries(company_name):

    # FIX: dynamic year so fallback queries stay current
    current_year = datetime.datetime.now().year

    prompt = f"""
    You are a professional business research analyst.

    Generate exactly 8 search queries for researching {company_name}.

    Cover:

    1. Company Overview
    2. Leadership Team
    3. Products and Services
    4. Funding and Investors
    5. Recent News
    6. Competitors
    7. Financial Performance
    8. Risks and Controversies

    IMPORTANT RULES:
    - Every single query MUST contain the company name "{company_name}"
    - Never generate a generic query without the company name
    - Queries must be specific enough to find information about {company_name} only
    - For the Recent News query, include the current year {current_year}

    Return ONLY a valid JSON array.

    Do not add explanations.
    Do not add markdown.
    Do not add ```json blocks.

    Example for company "Zepto":

    [
        "Zepto company overview India",
        "Zepto CEO leadership team founders",
        "Zepto products services quick commerce"
    ]
    """

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content

        try:
            queries = json.loads(content)

        except Exception:

            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()
            queries = json.loads(content)

        if not isinstance(queries, list) or len(queries) == 0:
            print("Query generation returned empty, using fallback queries")
            return _fallback_queries(company_name, current_year)

        return queries

    except Exception as e:

        print(f"Query Generation Error: {e}")
        return _fallback_queries(company_name, current_year)


def _fallback_queries(company_name, current_year):
    # FIX: extracted to avoid duplication + dynamic year
    return [
        f"{company_name} company overview",
        f"{company_name} CEO leadership team",
        f"{company_name} products and services",
        f"{company_name} funding investors valuation",
        f"{company_name} latest news {current_year}",
        f"{company_name} competitors market",
        f"{company_name} revenue financial performance",
        f"{company_name} risks controversies"
    ]


def search_query(query, max_results=5):

    try:

        results = DDGS().text(
            query,
            max_results=max_results
        )

        results = list(results)

        results_list = []

        for result in results:

            results_list.append(
                {
                    "title": result.get("title"),
                    "url": result.get("href"),
                    "snippet": result.get("body", "")
                }
            )

        return results_list

    except Exception as e:

        print(f"Search Error: {e}")

        return []


def search_all_queries(company_name):

    queries = generate_search_queries(company_name)

    if not queries:
        print("Warning: No queries generated for company")
        return {}

    all_results = {}

    for query in queries:

        print(f"\nSearching: {query}")

        all_results[query] = search_query(query)

        time.sleep(1.5)

    return all_results


def scrape_article(url):

    try:

        # FIX: full User-Agent string
        # Truncated UA was causing 403s on many news sites
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript"
        ]):
            tag.decompose()

        text = soup.get_text(separator=" ")

        text = " ".join(text.split())

        return text

    except Exception as e:

        print(f"Scraping Error: {e}")

        return ""


def collect_research(company_name):

    search_results = search_all_queries(company_name)

    research_data = {}

    seen_urls = set()

    for query, urls in search_results.items():

        research_data[query] = []

        for item in urls:

            try:

                # FIX: None URL guard
                # result.get("href") returns None when DuckDuckGo
                # doesn't return a URL — was crashing the pipeline
                url = item.get("url")

                if not url:
                 continue

                url = url.rstrip("/")

                if is_blocked(url):
                    print(f"Skipping blocked domain: {url}")
                    continue

                if url in seen_urls:
                    print(f"Skipping duplicate URL: {url}")
                    continue

                seen_urls.add(url)

                print(f"Scraping: {url}")

                text = scrape_article(url)

                if len(text) > 1000:

                    research_data[query].append(
                        {
                            "title": item["title"],
                            "url": url,
                            "text": text[:5000]
                        }
                    )

                elif item.get("snippet"):

                    research_data[query].append(
                        {
                            "title": item["title"],
                            "url": url,
                            "text": item["snippet"]
                        }
                    )

            except Exception as e:

                print(f"Document Error: {e}")

    return research_data