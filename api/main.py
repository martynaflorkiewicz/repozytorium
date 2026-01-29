from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

from database import SessionLocal
from models import Movie, Link, Rating, Tag, User

app = FastAPI()

SECRET_KEY = "super_secret_key"  
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 1

security = HTTPBearer()

class UserCreate(BaseModel):
    username: str
    password: str
    roles: list[str] = ["ROLE_USER"]


class LoginData(BaseModel):
    username: str
    password: str


class MovieCreate(BaseModel):
    movieId: int
    title: str
    genres: str


class MovieUpdate(BaseModel):
    title: str
    genres: str


class TagCreate(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: int


class TagUpdate(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: int


def movie_to_dict(m: Movie):
    return {"movieId": m.movieId, "title": m.title, "genres": m.genres}


def link_to_dict(l: Link):
    return {"movieId": l.movieId, "imdbId": l.imdbId, "tmdbId": l.tmdbId}


def rating_to_dict(r: Rating):
    return {
        "id": r.id,
        "userId": r.userId,
        "movieId": r.movieId,
        "rating": r.rating,
        "timestamp": r.timestamp,
    }


def tag_to_dict(t: Tag):
    return {
        "id": t.id,
        "userId": t.userId,
        "movieId": t.movieId,
        "tag": t.tag,
        "timestamp": t.timestamp,
    }


def get_current_payload(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(payload=Depends(get_current_payload)):
    roles = payload.get("roles", [])
    if "ROLE_ADMIN" not in roles:
        raise HTTPException(status_code=403, detail="Admin only")
    return payload


@app.get("/")
def hello():
    return {"hello": "world"}


@app.post("/login")
def login(data: LoginData):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == data.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        ok = bcrypt.checkpw(
            data.password.encode("utf-8"),
            user.password_hash.encode("utf-8"),
        )
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.username,
            "roles": user.roles.split(",") if user.roles else [],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=TOKEN_EXPIRE_HOURS)).timestamp()),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()


@app.post("/users")
def create_user(data: UserCreate, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.username == data.username).first()
        if exists:
            raise HTTPException(status_code=409, detail="Username already exists")

        pw_hash = bcrypt.hashpw(
            data.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        user = User(
            username=data.username,
            password_hash=pw_hash,
            roles=",".join(data.roles),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "username": user.username, "roles": data.roles}
    finally:
        db.close()


@app.get("/user_details")
def user_details(payload=Depends(get_current_payload)):
    return {
        "username": payload.get("sub"),
        "roles": payload.get("roles", []),
        "iat": payload.get("iat"),
        "exp": payload.get("exp"),
    }


@app.get("/movies")
def get_movies(_=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        movies = db.query(Movie).all()
        return [movie_to_dict(m) for m in movies]
    finally:
        db.close()


@app.get("/links")
def get_links(_=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        links = db.query(Link).all()
        return [link_to_dict(l) for l in links]
    finally:
        db.close()


@app.get("/ratings")
def get_ratings(_=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        ratings = db.query(Rating).all()
        return [rating_to_dict(r) for r in ratings]
    finally:
        db.close()


@app.get("/tags")
def get_tags(_=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        return [tag_to_dict(t) for t in tags]
    finally:
        db.close()


@app.post("/movies", status_code=201)
def create_movie(movie: MovieCreate, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        exists = db.query(Movie).filter(Movie.movieId == movie.movieId).first()
        if exists:
            raise HTTPException(status_code=409, detail="Movie already exists")

        m = Movie(**movie.model_dump())
        db.add(m)
        db.commit()
        db.refresh(m)
        return movie_to_dict(m)
    finally:
        db.close()


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, _=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(Movie.movieId == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie_to_dict(movie)
    finally:
        db.close()


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, data: MovieUpdate, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(Movie.movieId == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        movie.title = data.title
        movie.genres = data.genres
        db.commit()
        db.refresh(movie)
        return movie_to_dict(movie)
    finally:
        db.close()


@app.delete("/movies/{movie_id}", status_code=204)
def delete_movie(movie_id: int, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(Movie.movieId == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        db.delete(movie)
        db.commit()
    finally:
        db.close()


@app.post("/tags", status_code=201)
def create_tag(data: TagCreate, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        t = Tag(**data.model_dump())
        db.add(t)
        db.commit()
        db.refresh(t)
        return tag_to_dict(t)
    finally:
        db.close()


@app.get("/tags/{tag_id}")
def get_tag(tag_id: int, _=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        t = db.query(Tag).filter(Tag.id == tag_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag_to_dict(t)
    finally:
        db.close()


@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, data: TagUpdate, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        t = db.query(Tag).filter(Tag.id == tag_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tag not found")

        t.userId = data.userId
        t.movieId = data.movieId
        t.tag = data.tag
        t.timestamp = data.timestamp
        db.commit()
        db.refresh(t)
        return tag_to_dict(t)
    finally:
        db.close()


@app.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int, _=Depends(require_admin)):
    db = SessionLocal()
    try:
        t = db.query(Tag).filter(Tag.id == tag_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Tag not found")
        db.delete(t)
        db.commit()
    finally:
        db.close()



@app.get("/debug_users", openapi_extra={"security": []})
def debug_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [{"id": u.id, "username": u.username, "roles": u.roles} for u in users]
    finally:
        db.close()
