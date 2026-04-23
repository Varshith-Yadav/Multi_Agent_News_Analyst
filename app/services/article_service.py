from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.article import Article


def _as_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_articles_by_query(
    query: str,
    *,
    limit: int = 25,
    region: str | None = None,
    industry: str | None = None,
    time_window_hours: int = 72,
) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        since = datetime.now(UTC) - timedelta(hours=time_window_hours)
        db_query = db.query(Article).filter(
            Article.published_at >= since.replace(tzinfo=None),
            (Article.title.ilike(f"%{query}%")) | (Article.content.ilike(f"%{query}%")),
        )

        if region:
            db_query = db_query.filter(Article.region.ilike(f"%{region}%"))
        if industry:
            db_query = db_query.filter(Article.topic.ilike(f"%{industry}%"))

        articles = db_query.order_by(Article.published_at.desc()).limit(limit).all()
        return [
            {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "source": article.source,
                "url": article.url,
                "published_at": _as_utc(article.published_at).isoformat(),
                "region": article.region,
                "industry": article.topic,
            }
            for article in articles
        ]
    except SQLAlchemyError:
        return []
    finally:
        db.close()


def get_all_articles(limit: int = 200) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        articles = db.query(Article).order_by(Article.published_at.desc()).limit(limit).all()
        return [
            {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "source": article.source,
                "url": article.url,
                "published_at": _as_utc(article.published_at).isoformat(),
                "region": article.region,
                "industry": article.topic,
            }
            for article in articles
            if article.content
        ]
    except SQLAlchemyError:
        return []
    finally:
        db.close()


def get_historical_articles(
    *,
    query: str,
    baseline_days: int,
    exclude_hours: int,
    limit: int = 400,
) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        now = datetime.now(UTC)
        newer_than = now - timedelta(days=baseline_days)
        older_than = now - timedelta(hours=exclude_hours)
        rows = (
            db.query(Article)
            .filter(
                Article.published_at >= newer_than.replace(tzinfo=None),
                Article.published_at < older_than.replace(tzinfo=None),
                (Article.title.ilike(f"%{query}%")) | (Article.content.ilike(f"%{query}%")),
            )
            .order_by(Article.published_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "title": row.title,
                "content": row.content,
                "source": row.source,
                "url": row.url,
                "published_at": _as_utc(row.published_at).isoformat(),
            }
            for row in rows
            if row.content
        ]
    except SQLAlchemyError:
        return []
    finally:
        db.close()
