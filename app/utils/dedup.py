def remove_duplicates(articles):
    seen_urls = set()
    seen_title_fingerprints = set()
    unique = []

    for article in articles:
        url = (article.get("url") or "").strip().lower()
        title_fp = " ".join((article.get("title") or "").strip().lower().split())

        if url and url in seen_urls:
            continue
        if title_fp and title_fp in seen_title_fingerprints:
            continue

        if url:
            seen_urls.add(url)
        if title_fp:
            seen_title_fingerprints.add(title_fp)
        unique.append(article)

    return unique
