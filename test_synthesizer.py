from researcher import collect_research
from synthesizer import summarize_section

company = "Zepto"

research_data = collect_research(company)

first_query = list(research_data.keys())[0]

documents = research_data[first_query]

combined_text = ""

for doc in documents:
    combined_text += doc["text"]
    combined_text += "\n\n"

summary = summarize_section(
    first_query,
    combined_text[:10000]
)

print("\n")
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(summary)