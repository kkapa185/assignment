from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models, token_utils
from .schemas import UserCreate


def register_user(user: UserCreate, db: Session):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = token_utils.hash_password(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered"}


def login_user(username: str, password: str, db: Session):
    user = db.query(models.User).filter(
        models.User.username == username).first()
    if not user or not token_utils.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = token_utils.create_token({"sub": user.username}, token_utils.ACCESS_EXPIRE_MIN,
                                            token_utils.SECRET_KEY)
    refresh_token = token_utils.create_token({"sub": user.username}, token_utils.REFRESH_EXPIRE_MIN,
                                             token_utils.REFRESH_SECRET_KEY)

    db_token = models.RefreshToken(token=refresh_token, user_id=user.id)
    db.add(db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_user_token(refresh_token: str, db: Session):
    payload = token_utils.decode_token(
        refresh_token, token_utils.REFRESH_SECRET_KEY)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = payload.get("sub")
    user = db.query(models.User).filter(
        models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == refresh_token,
                                                        models.RefreshToken.user_id == user.id).first()
    if not stored_token:
        raise HTTPException(
            status_code=401, detail="Refresh token expired or already used")

    # Rotate token: delete old, issue new
    db.delete(stored_token)
    db.commit()

    new_refresh_token = token_utils.create_token({"sub": user.username}, token_utils.REFRESH_EXPIRE_MIN,
                                                 token_utils.REFRESH_SECRET_KEY)
    db.add(models.RefreshToken(token=new_refresh_token, user_id=user.id))
    db.commit()

    access_token = token_utils.create_token(
        {"sub": user.username}, token_utils.ACCESS_EXPIRE_MIN, token_utils.SECRET_KEY)
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


def logout_user(refresh_token: str, db: Session):
    stored_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_token).first()
    if not stored_token:
        raise HTTPException(
            status_code=400, detail="Token already invalidated or not found")
    db.delete(stored_token)
    db.commit()
    return {"msg": "Logged out"}
