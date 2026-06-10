import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_full_report(research_data):

    combined_research = ""

    for section_name, documents in research_data.items():

        combined_research += f"\n\nSECTION: {section_name}\n"

        for doc in documents:

            combined_research += doc["text"][:1500]
            combined_research += "\n\n"

    prompt = f"""
    You are a professional business analyst.

    Create a Company Intelligence Report.

    Use EXACTLY these sections:

    ## Company Overview

    ## Leadership Team

    ## Products and Services

    ## Funding and Investors

    ## Recent News

    ## Competitors

    ## Financial Performance

    ## Risks and Controversies

    Rules:

    - Professional tone
    - No hallucinations
    - Use only supplied information
    - Maximum 120 words per section
    - Remove website clutter

    Research Data:

    {combined_research[:15000]}
    """

    # Error handling added — prevents raw exception reaching Streamlit UI
    # Returns a readable failure message instead of crashing the pipeline
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

        return response.choices[0].message.content

    except Exception as e:

        print(f"Synthesis Error: {e}")

        return (
            "## Report Generation Failed\n\n"
            "Unable to synthesize report due to an API error. "
            "Please try again in a few moments."
        )