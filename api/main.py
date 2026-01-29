from fastapi import FastAPI
from database import SessionLocal
from models import Movie, Link, Rating, Tag

app = FastAPI()

@app.get("/")
def hello():
    return {"hello": "world"}

@app.get("/movies")
def get_movies():
    db = SessionLocal()
    movies = db.query(Movie).all()
    return [m.__dict__ for m in movies]

@app.get("/links")
def get_links():
    db = SessionLocal()
    links = db.query(Link).all()
    return [l.__dict__ for l in links]

@app.get("/ratings")
def get_ratings():
    db = SessionLocal()
    ratings = db.query(Rating).all()
    return [r.__dict__ for r in ratings]

@app.get("/tags")
def get_tags():
    db = SessionLocal()
    tags = db.query(Tag).all()
    return [t.__dict__ for t in tags]
