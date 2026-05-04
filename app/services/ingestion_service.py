from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

try:
    from dateutil import parser as date_parser
except Exception:  # pragma: no cover - optional dependency fallback
    date_parser = None  # type: ignore[assignment]

from app.db.session import SessionLocal
from app.models.article import Article
from app.utils.dedup import remove_duplicates
from app.vector.embeddings import get_embedding
from app.vector.store import add_embeddings


def _to_datetime(value: str | None):
    if not value:
        return None
    try:
        if date_parser is not None:
            parsed = date_parser.parse(value)
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None)
    except Exception:
        return None


def save_articles(articles):
    unique_articles = remove_duplicates(articles)
    embeddings = []
    metadata = []
    db = SessionLocal()

    try:
        for art in unique_articles:
            exists = db.query(Article).filter(Article.url == art["url"]).first()
            if exists:
                continue

            db_article = Article(
                title=art.get("title", "").strip(),
                content=art.get("content", "").strip(),
                source=art.get("source", "Unknown").strip(),
                url=art.get("url", "").strip(),
                published_at=_to_datetime(art.get("published_at")),
                region=art.get("region"),
                topic=art.get("industry"),
            )
            db.add(db_article)

            text = f"{db_article.title} {db_article.content}".strip()
            if text:
                embeddings.append(get_embedding(text))
                metadata.append(
                    {
                        "title": db_article.title,
                        "content": db_article.content,
                        "source": db_article.source,
                        "url": db_article.url,
                        "published_at": art.get("published_at"),
                        "region": db_article.region,
                        "industry": db_article.topic,
                    }
                )

        db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()

    if embeddings:
        add_embeddings(embeddings, metadata)
