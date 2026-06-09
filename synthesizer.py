import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def summarize_section(section_name, raw_text):

    prompt = f"""
    You are a professional business analyst.

    Create a concise professional report section.

    Section:
    {section_name}

    Rules:
    - Maximum 150 words
    - Professional tone
    - Do not invent facts
    - Use only provided information
    - Remove website clutter
    - Write as if preparing a company intelligence report

    Research Data:

    {raw_text}
    """

    response = model.generate_content(prompt)

    return response.text


def summarize_all_sections(research_data):

    summaries = {}

    for section_name, documents in research_data.items():

        print(f"\nSummarizing: {section_name}")

        combined_text = ""

        for doc in documents:

            combined_text += doc["text"]
            combined_text += "\n\n"

        if len(combined_text.strip()) == 0:

            summaries[section_name] = "No information available."

            continue

        summary = summarize_section(
            section_name,
            combined_text[:10000]
        )

        summaries[section_name] = summary

    return summaries