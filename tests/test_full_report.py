from researcher import collect_research
from synthesizer import generate_full_report

company = "Zepto"

print("Collecting research...")

research_data = collect_research(company)

print("Generating full report...")

report = generate_full_report(
    research_data
)

print("\n")
print("=" * 80)
print("FULL REPORT")
print("=" * 80)

print(report)