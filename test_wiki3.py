import urllib.request, urllib.parse, json

def test_wiki(query):
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=1&namespace=0&format=json"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            search_data = json.loads(response.read().decode())
            if len(search_data) > 1 and search_data[1]:
                title = search_data[1][0]
                content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&format=json&titles={urllib.parse.quote(title)}"
                req2 = urllib.request.Request(content_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req2, timeout=5) as response2:
                    data2 = json.loads(response2.read().decode())
                    pages = data2['query']['pages']
                    for page_id in pages:
                        if page_id != "-1":
                            print(f"[{query}] Extract length:", len(pages[page_id]['extract']))
                            print(f"[{query}] Extract:", pages[page_id]['extract'])
                            return
    except Exception as e:
        print("Error:", e)

test_wiki("AI regulation")
test_wiki("us iran war")
test_wiki("artificial intelligence")
