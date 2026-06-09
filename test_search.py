from ddgs import DDGS

results = DDGS().text(
    "Tesla Inc official company profile",
    max_results=5
)

results = list(results)

print("Number of results:", len(results))

for r in results:
    print("\nTITLE:", r.get("title"))
    print("URL:", r.get("href"))