from researcher import collect_research
from synthesizer import generate_full_report
from report_builder import create_company_report

company = "Zepto"

print("Collecting research...")

research_data = collect_research(company)

print("Generating report...")

report = generate_full_report(
    research_data
)

print("Building PDF...")

pdf_file = create_company_report(
    company,
    report
)

print("\nPDF CREATED:")
print(pdf_file)