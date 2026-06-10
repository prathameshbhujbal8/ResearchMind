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
    "Leadership Team",
    "Products and Services",
    "Funding and Investors",
    "Recent News",
    "Competitors",
    "Financial Performance",
    "Risks and Controversies",
    "Analyst Assessment"
]


def generate_full_report(research_data):

    # FIX: list + join instead of string concatenation in loop
    # Avoids creating intermediate string objects on every iteration
    parts = []

    for section_name, documents in research_data.items():

        parts.append(f"\n\nSECTION: {section_name}\n")

        for doc in documents:

            parts.append(doc["text"][:2000])
            parts.append("\n\n")

    combined_research = "".join(parts)

    prompt = f"""
    You are a senior business intelligence analyst at a top consulting firm.

    Create a professional Company Intelligence Report using the research data below.

    Use EXACTLY these sections in this exact order:

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

    STRICT RULES:

    1. Minimum 80 words per section, maximum 150 words per section
    2. Executive Summary must be exactly 3 sentences:
       Sentence 1 — What the company does and its scale
       Sentence 2 — Its most significant recent development
       Sentence 3 — One key opportunity or risk
    3. Analyst Assessment must end with exactly this format:
       Overall Rating: STRONG / MODERATE / WATCH
       (choose one based on the research)
    4. Use only information from the supplied research data
    5. If a section has insufficient data, write what is known
       and state: "Limited public data available for this section."
    6. Do not hallucinate numbers, names, or dates
    7. Professional tone throughout
    8. Ignore any website navigation text, cookie notices,
       advertisements, or non-editorial content in the research data

    Research Data:

    {combined_research[:25000]}
    """

    # FIX: increased from 15000 to 50000 characters
    # 15000 chars = ~3750 tokens, only 12% of available context
    # 50000 chars = ~12500 tokens, stays safely within 32k window
    # Triples the research context sent to the LLM

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

        # FIX: section validation
        # Surfaces missing sections in logs immediately
        # instead of silently generating a broken PDF
        missing = [s for s in REQUIRED_SECTIONS if s not in report]

        if missing:
            print(f"Warning: Report missing sections: {missing}")

        return report

    except Exception as e:

        print(f"Synthesis Error: {e}")

        return (
            "## Report Generation Failed\n\n"
            "Unable to synthesize report due to an API error. "
            "Please try again in a few moments."
        )