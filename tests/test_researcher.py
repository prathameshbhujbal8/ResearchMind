from researcher import search_all_queries

company = "Tesla"

results = search_all_queries(company)

for query, urls in results.items():

    print("\n" + "=" * 60)

    print(f"\nQUERY: {query}")

    if not urls:

        print("No results found")

        continue

    for i, result in enumerate(urls, start=1):

        print(f"\nResult {i}")

        print("Title:", result["title"])

        print("URL:", result["url"])