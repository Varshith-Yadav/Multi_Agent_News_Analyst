import urllib.request, urllib.parse, json
title = 'US-Iran War'
content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&format=json&titles={urllib.parse.quote(title)}"
print(content_url)
req = urllib.request.Request(content_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    response = urllib.request.urlopen(req, timeout=5)
    data2 = json.loads(response.read().decode())
    print("Content Data:", data2)
    pages = data2['query']['pages']
    for page_id in pages:
        if page_id != "-1":
            print("Extracted text:", pages[page_id]['extract'])
except Exception as e:
    print("Error:", e)
