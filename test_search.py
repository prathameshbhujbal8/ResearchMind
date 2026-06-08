from duckduckgo_search import DDGS

try:
    with DDGS() as ddgs:
        results = list(ddgs.text("Tesla company overview", max_results=5))

    print("Number of results:", len(results))

    for result in results:
        print("\nTITLE:", result.get("title"))
        print("URL:", result.get("href"))

except Exception as e:
    print("ERROR:")
    print(e)