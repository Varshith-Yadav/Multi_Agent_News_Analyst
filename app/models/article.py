from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, index=True)
    content = Column(Text)

    source = Column(String, index=True)
    url = Column(String, unique=True)

    published_at = Column(DateTime, default=datetime.utcnow)

    # metadata
    region = Column(String, nullable=True)
    topic = Column(String, nullable=True)