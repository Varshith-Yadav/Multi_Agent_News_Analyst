import urllib.request, urllib.parse, json
query = "us iran war"
search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=1&namespace=0&format=json"
print("URL:", search_url)
req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    response = urllib.request.urlopen(req, timeout=5)
    search_data = json.loads(response.read().decode())
    print("Search Data:", search_data)
except Exception as e:
    print("Error:", e)
