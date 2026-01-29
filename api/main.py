from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

from database import SessionLocal
from models import Movie, Link, Rating, Tag, User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

app = FastAPI()




SECRET_KEY = "super_secret_key"  # docelowo .env
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 1



class UserCreate(BaseModel):
    username: str
    password: str
    roles: list[str] = ["ROLE_USER"]


class LoginData(BaseModel):
    username: str
    password: str


def get_current_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
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
def create_user(data: UserCreate, _payload=Depends(require_admin)):
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
def get_movies(_payload=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        movies = db.query(Movie).all()
        return [m.__dict__ for m in movies]
    finally:
        db.close()


@app.get("/links")
def get_links(_payload=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        links = db.query(Link).all()
        return [l.__dict__ for l in links]
    finally:
        db.close()


@app.get("/ratings")
def get_ratings(_payload=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        ratings = db.query(Rating).all()
        return [r.__dict__ for r in ratings]
    finally:
        db.close()


@app.get("/tags")
def get_tags(_payload=Depends(get_current_payload)):
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        return [t.__dict__ for t in tags]
    finally:
        db.close()
@app.get("/debug_users", openapi_extra={"security": []})
def debug_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "roles": u.roles
            }
            for u in users
        ]
    finally:
        db.close()

