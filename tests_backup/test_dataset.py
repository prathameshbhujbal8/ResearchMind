from researcher import collect_research

company = "Zepto"

research_data = collect_research(company)

print("\n")
print("=" * 80)
print("RESEARCH DATASET CREATED")
print("=" * 80)

for query, documents in research_data.items():

    print("\n")
    print("=" * 60)

    print("QUERY:")
    print(query)

    print(f"\nDOCUMENTS FOUND: {len(documents)}")

    if documents:

        first_doc = documents[0]

        print("\nFIRST DOCUMENT TITLE:")
        print(first_doc["title"])

        print("\nSOURCE URL:")
        print(first_doc["url"])

        print("\nTEXT LENGTH:")
        print(len(first_doc["text"]))

        print("\nTEXT PREVIEW:")
        print(first_doc["text"][:300])