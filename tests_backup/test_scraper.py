from researcher import scrape_article

url = "https://en.wikipedia.org/wiki/Tesla,_Inc."

text = scrape_article(url)

print("\nTEXT LENGTH:")
print(len(text))

print("\nFIRST 1500 CHARACTERS:\n")

print(text[:1500])