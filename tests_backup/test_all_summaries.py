from researcher import collect_research
from synthesizer import summarize_all_sections

company = "Zepto"

print("\nCollecting Research...\n")

research_data = collect_research(company)

print("\nGenerating Summaries...\n")

summaries = summarize_all_sections(
    research_data
)

print("\n")
print("=" * 80)
print("FINAL REPORT SECTIONS")
print("=" * 80)

for section, summary in summaries.items():

    print("\n")
    print("=" * 80)

    print(section.upper())

    print("=" * 80)

    print(summary)