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

# ── Blocked Domains ───────────────────────────────────────────────────────────
# Social media and login-walled sites that scrape as empty or garbage.

BLOCKED_DOMAINS = [
    "twitter.com", "x.com", "instagram.com",
    "facebook.com", "reddit.com", "quora.com",
    "pinterest.com", "tiktok.com", "youtube.com",
    "linkedin.com", "threads.net", "snapchat.com"
]

# ── Preferred Domains ─────────────────────────────────────────────────────────
# RANK 2: Authoritative sources sorted to top of results before scraping.
# LLMs weight earlier context more heavily (primacy bias).
# Putting Bloomberg before a random blog improves financial accuracy.

PREFERRED_DOMAINS = [
    "wikipedia.org",
    "crunchbase.com",
    "bloomberg.com",
    "reuters.com",
    "techcrunch.com",
    "forbes.com",
    "livemint.com",
    "economictimes.indiatimes.com",
    "moneycontrol.com",
    "thehindu.com",
    "businessstandard.com",
    "sec.gov",
    "nseindia.com",
    "bseindia.com",
    # RANK 1B: Investor relations domains added explicitly
    # These are the highest-authority sources for financial figures
    # and are deprioritised by DuckDuckGo vs general news sites
    "investor.nvidia.com",
    "investors.microsoft.com",
    "investor.apple.com",
    "ir.tesla.com",
    "abc.xyz",              # Alphabet IR
    "macrotrends.net",
    "wsj.com",
    "ft.com",
    "barrons.com"
]

# ── Low Authority Domains ─────────────────────────────────────────────────────
# Domains that pass scraping and relevance filters but produce
# content that undermines report credibility when visible in Sources.
# These are retail investor blogs, crypto news sites, entertainment
# publications, and personal finance blogs not suitable for
# professional intelligence reports.
# Checked in collect_research() — content skipped entirely.

LOW_AUTHORITY_DOMAINS = [
    # Retail investor / personal finance blogs
    "franknez.com",
    "blog.moneyfarm.com",
    "ainvest.com",
    "dreamridiculous.com",
    "insider-trading.org",
    "bullfincher.io",
    "stockanalysis.com",
    "wccftech.com",
    "wishesh.com",
    "pocketoption.com",
    # Crypto / gambling adjacent sites
    "en.bitcoinhaber.net",
    "worldcoinindex.com",
    "coincodex.com",
    # Entertainment / gaming publications used for business analysis
    "hollywoodreporter.com",
    "vgchartz.com",
    "pcgamesn.com",
    "mobilesyrup.com",
    # Unknown / low-signal domains
    "wireunwired.com",
    "answertabs.com",
    "gadgetmates.com",
    "ts2.tech",
    "a.mahiti.org",
    # Priority 3 additions — observed in Microsoft and NVIDIA reports
    "cliffsnotes.com",
    "researchgate.net",
    "productgym.io",
    "vcbeast.com",
    "ypredict.ai",
    "audioholics.com",
    "deepresearchglobal.com",
    "techbloat.com",
    "breezyscroll.com",
    "studioglobal.ai",
    "taskade.com",
    "strategyfinders.com",
    "stockstoday.com",
    "mergr.com",
    "acquired.fm",
    "execmag.com",
    "parameter.io",
    "companies-explained.com",
    "atouchofbusiness.com",
    "siliconanalysts.com",
    "globalny.biz",
    "newsdailynation.com",
    "fntalk.com",
]


def is_low_authority(url):
    """
    Returns True if URL belongs to a low-authority domain.
    Used in collect_research() to skip content before scraping.
    Separate from is_blocked() so the two lists stay independent
    and easy to maintain.
    """
    try:
        hostname = urlparse(url).hostname or ""
        hostname = hostname.replace("www.", "")
        return any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in LOW_AUTHORITY_DOMAINS
        )
    except Exception:
        return False


def is_blocked(url):
    try:
        hostname = urlparse(url).hostname or ""
        return any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in BLOCKED_DOMAINS
        )
    except Exception:
        return False


def source_priority(url):
    """
    RANK 2: Returns sort key for result ordering.
    0 = preferred domain (sorted first)
    1 = everything else
    Stable sort preserves DuckDuckGo ranking within each group.
    """
    try:
        hostname = urlparse(url).hostname or ""
        for domain in PREFERRED_DOMAINS:
            if hostname == domain or hostname.endswith("." + domain):
                return 0
        return 1
    except Exception:
        return 1


def generate_search_queries(company_name):

    current_year = datetime.datetime.now().year

    prompt = f"""
    You are a professional business research analyst.

    Generate exactly 9 search queries for researching {company_name}.

    Cover EXACTLY these topics in this order:

    1. Company Overview
    2. Leadership Team
    3. Products and Services
    4. Funding and Investors
    5. Recent News
    6. Competitors
    7. Annual Financial Results (revenue, net income, operating income)
    8. Quarterly Earnings (most recent quarter results)
    9. Risks and Controversies

    IMPORTANT RULES:
    - Every single query MUST contain the company name "{company_name}"
    - Never generate a generic query without the company name
    - Queries must be specific enough to find information about {company_name} only
    - For the Recent News query, include the current year {current_year}
    - For query 7 (Annual Financial Results): use terms like
      "annual revenue", "fiscal year results", "investor relations"
    - For query 8 (Quarterly Earnings): use terms like
      "quarterly earnings", "Q results", "earnings report {current_year}"
    - For query 6 (Competitors): include specific product or market segment
      not just "competitors" — e.g. "GPU market competitors" not "competitors"

    Return ONLY a valid JSON array.

    Do not add explanations.
    Do not add markdown.
    Do not add ```json blocks.

    Example for company "NVIDIA":

    [
        "NVIDIA company overview history founded",
        "NVIDIA CEO Jensen Huang leadership team executives",
        "NVIDIA GPU products Blackwell H100 data center",
        "NVIDIA funding investors venture capital",
        "NVIDIA news announcements {current_year}",
        "NVIDIA GPU market competitors AMD Intel custom silicon",
        "NVIDIA annual revenue fiscal year 2026 investor relations",
        "NVIDIA quarterly earnings Q1 2027 results",
        "NVIDIA risks export restrictions regulatory controversies"
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
    # RANK 1B: 9 queries with two dedicated financial queries
    # Index 6 = annual results, Index 7 = quarterly earnings
    # These indices are used in search_all_queries() for timelimit control
    return [
        f"{company_name} company overview history",
        f"{company_name} CEO leadership team executives",
        f"{company_name} products services portfolio",
        f"{company_name} funding investors valuation",
        f"{company_name} latest news {current_year}",
        f"{company_name} competitors market share",
        f"{company_name} annual revenue fiscal year {current_year} investor relations",
        f"{company_name} quarterly earnings results {current_year}",
        f"{company_name} risks controversies regulatory"
    ]


def search_query(query, max_results=5, timelimit="y"):
    # IMPROVEMENT 1: Date filter on all searches.
    # timelimit="y" restricts results to the past 12 months.
    # Eliminates stale product pages, outdated leadership data,
    # and old news articles that pass the relevance filter
    # because the company name appears in them.
    # Recent News queries pass timelimit="m" (past month) from
    # search_all_queries() for tighter recency on that section.

    try:

        results = DDGS().text(
            query,
            max_results=max_results,
            timelimit=timelimit
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

        # RANK 2: Sort preferred domains to top before returning
        results_list.sort(
            key=lambda r: source_priority(r.get("url") or "")
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

    # Query index reference (matches prompt ordering):
    # 0 = Company Overview      → yearly
    # 1 = Leadership Team       → yearly
    # 2 = Products & Services   → yearly
    # 3 = Funding & Investors   → yearly
    # 4 = Recent News           → monthly (tightest recency)
    # 5 = Competitors           → yearly
    # 6 = Annual Financial      → yearly (want full year data)
    # 7 = Quarterly Earnings    → monthly (most recent quarter)
    # 8 = Risks & Controversies → yearly
    NEWS_QUERY_INDEX     = 4
    QUARTERLY_QUERY_INDEX = 7

    for i, query in enumerate(queries):

        print(f"\nSearching: {query}")

        if i in (NEWS_QUERY_INDEX, QUARTERLY_QUERY_INDEX):
            # Monthly timelimit for recency-sensitive queries
            all_results[query] = search_query(query, timelimit="m")
        else:
            all_results[query] = search_query(query, timelimit="y")

        time.sleep(1.5)

    return all_results


def scrape_article(url):

    try:

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

                url = item.get("url")

                if not url:
                    continue

                # Priority 1: Block stale investor relations URLs.
                # microsoft.com/Investor/earnings/FY-2014-Q1 scrapes
                # successfully (static HTML) while FY-2026-Q3 returns
                # a JavaScript shell. The pipeline picks up the 2014
                # page, sees microsoft.com as the source label, and the
                # LLM uses the 2013 revenue figure with full confidence.
                # Blocking pre-FY2023 IR paths prevents this entirely.
                import re as _re
                _STALE_IR = _re.compile(
                    r'/(FY-20[01][0-9]|FY-202[0-2]|fy-20[01][0-9]|fy-202[0-2])/',
                    _re.IGNORECASE
                )
                if _STALE_IR.search(url):
                    print(f"Skipping stale fiscal year URL: {url}")
                    continue

                # Priority 3: Block ad redirect URLs.
                # DuckDuckGo occasionally returns Bing ad click-tracker
                # URLs that resolve to vendor pages. These appear in the
                # Sources page as 400-character encoded strings and
                # destroy report credibility on sight.
                if "/aclick" in url or "bing.com/aclick" in url:
                    print(f"Skipping ad redirect URL: {url}")
                    continue

                if is_blocked(url):
                    print(f"Skipping blocked domain: {url}")
                    continue

                # RANK 1A: Low authority domain filter
                # Skips domains that produce content which undermines
                # report credibility when visible in Sources page.
                if is_low_authority(url):
                    print(f"Skipping low-authority domain: {url}")
                    continue

                if url in seen_urls:
                    print(f"Skipping duplicate URL: {url}")
                    continue

                seen_urls.add(url)

                print(f"Scraping: {url}")

                text = scrape_article(url)

                if len(text) > 1000:

                    # RANK 1: Relevance filter
                    company_in_body = company_name.lower() in text.lower()

                    if not company_in_body:
                        print(f"Skipping irrelevant content: {url}")
                        continue

                    # RANK 1C: Stale content detection
                    # DuckDuckGo timelimit filters by crawl date not publish date.
                    # Old articles re-indexed recently pass the year filter.
                    # Check first 600 chars of scraped text for old year strings.
                    # If the opening of the article declares a pre-2023 year,
                    # the content is likely outdated regardless of crawl date.
                    text_header = text[:600]
                    stale_years = [
                        str(y) for y in range(2010, 2023)
                    ]
                    # Only reject if an old year appears in the header
                    # AND no recent year appears — avoids rejecting articles
                    # that compare historical vs current data
                    recent_years = [str(y) for y in range(2023, datetime.datetime.now().year + 1)]
                    header_has_old_year    = any(yr in text_header for yr in stale_years)
                    header_has_recent_year = any(yr in text_header for yr in recent_years)

                    if header_has_old_year and not header_has_recent_year:
                        print(f"Skipping stale content (old year in header): {url}")
                        continue

                    # RANK 5: Title match boost
                    # Articles with company name in title get larger
                    # text budget — they are more likely to be directly
                    # about the company rather than tangentially mentioning it.
                    company_in_title = company_name.lower() in (
                        item.get("title") or ""
                    ).lower()

                    text_limit = 7000 if company_in_title else 5000

                    # Priority 4: Wikipedia content truncation.
                    # Wikipedia is a preferred domain and sorts first,
                    # but its articles contain outdated financial figures
                    # in the body text (e.g. $150B market cap for NVIDIA).
                    # The stale year detector misses these because they
                    # appear without year context.
                    # Cap Wikipedia content at 2000 chars — enough for
                    # founding history and description, but cuts off the
                    # body text where stale financial figures appear.
                    try:
                        _wiki_host = urlparse(url).hostname or ""
                        if "wikipedia.org" in _wiki_host:
                            text_limit = min(text_limit, 2000)
                    except Exception:
                        pass

                    research_data[query].append(
                        {
                            "title": item["title"],
                            "url": url,
                            "text": text[:text_limit],
                            "title_match": company_in_title
                        }
                    )

                elif item.get("snippet"):

                    # Snippet fallback: only use if company name appears
                    snippet = item["snippet"]
                    if company_name.lower() in snippet.lower():
                        research_data[query].append(
                            {
                                "title": item["title"],
                                "url": url,
                                "text": snippet,
                                "title_match": False
                            }
                        )

            except Exception as e:

                print(f"Document Error: {e}")

    return research_data