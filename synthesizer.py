import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Company Overview",
    "Analyst Assessment"
]


def compute_research_confidence(research_data):
    """
    RANK 3: Scores research quality before synthesis runs.

    Scoring:
    - 8 queries x 12.5 points each = 100 max
    - Full article (text > 1000 chars): full points
    - Snippet only: 40% of points
    - No data: 0 points

    Returns dict with score, breakdown, and total_sources.
    Used to reject weak reports before wasting an LLM call.
    """

    total_queries = len(research_data)

    if total_queries == 0:
        return {
            "score": 0,
            "breakdown": {},
            "total_sources": 0
        }

    points_per_query = 100 / total_queries
    breakdown        = {}
    total_score      = 0
    total_sources    = 0

    for query, documents in research_data.items():

        if not documents:
            breakdown[query] = {
                "sources": 0,
                "quality": "No Data"
            }
            continue

        has_full_article = any(
            len(d.get("text", "")) > 1000
            for d in documents
        )

        if has_full_article:
            query_score = points_per_query
            quality     = "Good"
        else:
            query_score = points_per_query * 0.4
            quality     = "Weak"

        total_score   += query_score
        total_sources += len(documents)

        breakdown[query] = {
            "sources": len(documents),
            "quality": quality
        }

    return {
        "score":        round(total_score),
        "breakdown":    breakdown,
        "total_sources": total_sources
    }


# ── Marketing Language Patterns ──────────────────────────────────────────────
# RANK 2A: Sentences containing these phrases are stripped from scraped
# text before it enters the LLM context. This prevents marketing copy
# from microsoft.com, apple.com, and similar consumer-facing pages from
# being reproduced verbatim in the final report.
# Uses sentence-level removal, not character substitution, so surrounding
# content is preserved.

MARKETING_PATTERNS = [
    "empower individuals",
    "empower people",
    "achieve more",
    "committed to excellence",
    "committed to innovation",
    "committed to sustainability",
    "our mission is to",
    "we are dedicated to",
    "industry-leading solutions",
    "best-in-class",
    "world-class",
    "cutting-edge technology",
    "state-of-the-art",
    "innovative solutions",
    "driving innovation",
    "transforming the way",
    "seamlessly integrates",
    "cookie policy",
    "privacy policy",
    "terms of use",
    "all rights reserved",
    "subscribe to our newsletter",
    "sign up for updates",
    "click here to learn more",
]


def strip_marketing_language(text):
    """
    Removes sentences containing known marketing or boilerplate phrases.
    Operates at sentence level — splits on period, filters, rejoins.
    Preserves surrounding factual content.
    """
    if not text:
        return text

    sentences = text.split(". ")
    cleaned   = []

    for sentence in sentences:
        sentence_lower = sentence.lower()
        is_marketing   = any(
            pattern in sentence_lower
            for pattern in MARKETING_PATTERNS
        )
        if not is_marketing:
            cleaned.append(sentence)

    return ". ".join(cleaned)


def generate_full_report(research_data, min_confidence=35):
    """
    RANK 3: min_confidence gate added.
    Reports below threshold are rejected before LLM synthesis.
    Prevents weak hallucinated reports from reaching the user.

    Default 35 allows partial data through while blocking
    near-empty research datasets.
    """

    # ── Confidence check before any LLM call ─────────────────────────────────
    confidence = compute_research_confidence(research_data)

    print(f"Research confidence score: {confidence['score']}/100")
    print(f"Total sources collected:   {confidence['total_sources']}")

    if confidence["score"] < min_confidence:

        print(f"Report rejected: score {confidence['score']} below threshold {min_confidence}")

        rejection_report = (
            "## Insufficient Research Data\n\n"
            f"Research confidence score: {confidence['score']}/100\n\n"
            "Not enough reliable public data was found to generate "
            f"an accurate report. Only {confidence['total_sources']} "
            "source(s) were collected across all research areas.\n\n"
            "**Suggestions:**\n"
            "- Try a more well-known company\n"
            "- Check the spelling of the company name\n"
            "- Try adding the country or industry "
            "(e.g. 'Zepto India' instead of 'Zepto')"
        )

        return rejection_report, confidence

    # ── Build combined research context ──────────────────────────────────────
    # Each document prefixed with [SOURCE: domain.com | Title] so the LLM
    # can use these labels for inline attribution (Rule 8).
    #
    # PRIORITY ORDERING: Financial queries are placed FIRST in the context.
    # Previous bug: combined_research was built in query order (0-8).
    # With a 10,000 char cap, queries 0-3 consumed the full budget and
    # financial queries (index 6-7) never reached the LLM — causing empty
    # Financial Performance sections despite having scraped the data.
    #
    # Fix: Separate research_data into financial and non-financial buckets.
    # Build context as: financial_parts + other_parts, then cap the total.
    # Financial data now guaranteed to appear in the first chars of context.

    from urllib.parse import urlparse

    def _build_doc_block(section_name, documents):
        """Returns list of strings for one query's documents."""
        block = []
        block.append(f"\n\nSECTION: {section_name}\n")
        for doc in documents:
            try:
                domain = urlparse(doc.get("url", "")).hostname or "unknown"
                domain = domain.replace("www.", "")
            except Exception:
                domain = "unknown"
            title        = doc.get("title", "")[:80]
            source_label = f"[SOURCE: {domain} | {title}]"
            clean_text   = strip_marketing_language(doc["text"][:2500])
            block.append(source_label + "\n")
            block.append(clean_text)
            block.append("\n\n")
        return block

    # Keywords that identify financial queries in the research_data dict
    FINANCIAL_KEYWORDS = [
        "annual", "revenue", "financial", "earnings",
        "quarterly", "fiscal", "investor", "results"
    ]

    financial_parts = []
    other_parts     = []

    for section_name, documents in research_data.items():
        if not documents:
            continue
        section_lower = section_name.lower()
        is_financial  = any(kw in section_lower for kw in FINANCIAL_KEYWORDS)
        block         = _build_doc_block(section_name, documents)
        if is_financial:
            financial_parts.extend(block)
        else:
            other_parts.extend(block)

    # Financial content first — guaranteed to be within the context cap
    combined_research = "".join(financial_parts + other_parts)

    # ── Confidence note passed into prompt ───────────────────────────────────
    confidence_note = (
        f"Research Quality Score: {confidence['score']}/100 "
        f"based on {confidence['total_sources']} sources collected."
    )

    prompt = f"""
You are a senior business intelligence analyst.
Write a Company Intelligence Report using ONLY the research data provided below.

Output these 10 sections in this exact order:
## Executive Summary
## Company Overview
## Leadership Team
## Products and Services
## Funding and Investors
## Recent News
## Competitors
## Financial Performance
## Risks and Controversies
## Analyst Assessment

RULES:
1. 80-150 words per section. No exceptions.
2. Executive Summary: exactly 3 sentences — (1) what the company does and its scale, (2) most significant recent development, (3) one key opportunity or risk.
3. Analyst Assessment ends with: Overall Rating: STRONG / MODERATE / WATCH
4. Use ONLY information visible in the [SOURCE:] blocks in the research data.
5. Insufficient data: state what is known, then write "Limited public data available for this section."
6. FINANCIAL FIGURES: Every number (revenue, income, market cap, valuation, funding amount) MUST be followed by (Source: domain.com) matching a [SOURCE:] label in the data. If no matching label: write "Figures not publicly disclosed." — no source label after this phrase, ever. TEMPORAL VALIDITY: If a financial figure in the research data is explicitly associated with a date more than 3 years before today, do NOT use it as a current figure. Write "Figures not publicly disclosed." A sourced figure from 2013 or 2014 is not current data. Only present financial figures from 2023 onwards as current unless the context explicitly frames them as historical comparison data.
7. PROJECTIONS: Label all forecasts, estimates, and guidance explicitly. Write "Analysts project..." or "Guidance indicates..." Never present projections as confirmed historical facts.
8. SOURCE ATTRIBUTION: Append (Source: domain.com) after specific facts, names, and dates. Match only to [SOURCE:] labels present in the research data. Never invent source attributions. Never append a source label to fallback phrases from Rule 6.
8b. EXECUTIVE TITLES: Only use a title that is explicitly stated word-for-word in the source text. Never infer, assume, or assign a title because a role appears to be unfilled or because a name appears near a role description. If a name appears in the source without a clearly stated title, write the name only with no title attached.
8c. FUNDING VS OWNERSHIP: Never describe a public company's institutional shareholders as funders or investors in the startup sense. If a source says a firm "holds shares" or "owns stock" in a public company, write "holds shares in" — not "invested in" or "funded." Only use "invested in" or "funding" when the source explicitly describes a private round, fund commitment, or pre-IPO investment.
9. PROHIBITED WORDS/PHRASES — replace with specific facts or omit: wide range of / strong track record / well-positioned / significant developments / industry-leading / cutting-edge / world-class / best-in-class / empower individuals / achieve more / committed to innovation / transforming the way / continues to innovate.
10. Ignore navigation text, cookie notices, and advertisements found in the research data.

Research quality: {confidence_note}

Research Data (financial sections appear first):

{combined_research[:20000]}
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

        report = response.choices[0].message.content

        missing = [s for s in REQUIRED_SECTIONS if s not in report]

        if missing:
            print(f"Warning: Report missing sections: {missing}")

        return report, confidence

    except Exception as e:

        print(f"Synthesis Error: {e}")

        error_report = (
            "## Report Generation Failed\n\n"
            "Unable to synthesize report due to an API error. "
            "Please try again in a few moments."
        )

        return error_report, confidence