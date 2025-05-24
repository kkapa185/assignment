from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_EXPIRE_MIN = int(os.getenv("ACCESS_EXPIRE_MIN", 15))
REFRESH_EXPIRE_MIN = int(os.getenv("REFRESH_EXPIRE_MIN", 60 * 24))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in .env file")
if not REFRESH_SECRET_KEY:
    raise ValueError("REFRESH_SECRET_KEY not found in .env file")
if not ALGORITHM:
    raise ValueError("ALGORITHM not found in .env file")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


def create_token(data: dict, expire_minutes: int, secret: str):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() +
                     timedelta(minutes=expire_minutes)})
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str):
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError:
        return None
