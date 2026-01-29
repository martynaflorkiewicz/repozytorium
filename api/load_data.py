import csv
from database import engine, SessionLocal
from models import Base, Movie, Link, Rating, Tag

Base.metadata.create_all(bind=engine)

session = SessionLocal()

with open("data/movies.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        session.add(Movie(**row))

with open("data/links.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        session.add(Link(**row))

with open("data/ratings.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        session.add(Rating(**row))

with open("data/tags.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        session.add(Tag(**row))

session.commit()
session.close()

print("Dane załadowane do bazy")
