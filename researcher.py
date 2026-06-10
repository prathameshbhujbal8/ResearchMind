import os
import time
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_search_queries(company_name):

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

    Return ONLY a valid JSON array.

    Do not add explanations.
    Do not add markdown.
    Do not add ```json blocks.

    Example:

    [
        "Tesla company overview",
        "Tesla leadership team",
        "Tesla products and services"
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
            return json.loads(content)

        except Exception:

            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

            return json.loads(content)

    except Exception as e:

        print(f"Query Generation Error: {e}")

        return []


def search_query(query, max_results=3):

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

    all_results = {}

    for query in queries:

        print(f"\nSearching: {query}")

        all_results[query] = search_query(query)

        time.sleep(1.5)

    return all_results


def scrape_article(url):

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

    for query, urls in search_results.items():

        research_data[query] = []

        for item in urls:

            try:

                url = item["url"]

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