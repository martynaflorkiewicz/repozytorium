from sqlalchemy import Column, Integer, String, Float
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    roles = Column(String(255), default="ROLE_USER")


class Movie(Base):
    __tablename__ = "movies"

    movieId = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    genres = Column(String)


class Link(Base):
    __tablename__ = "links"

    movieId = Column(Integer, primary_key=True)
    imdbId = Column(String)
    tmdbId = Column(String)


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer)
    movieId = Column(Integer)
    rating = Column(Float)
    timestamp = Column(Integer)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer)
    movieId = Column(Integer)
    tag = Column(String)
    timestamp = Column(Integer)
