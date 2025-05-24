from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from . import models, auth, schemas, database, events

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

# =======================================================================================================================
# Authentcation APIs
# =======================================================================================================================


@app.post("/api/auth/register", tags=["Auth"])
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    return auth.register_user(user, db)


@app.post("/api/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    return auth.login_user(form_data.username, form_data.password, db)


@app.post("/api/auth/refresh", response_model=schemas.Token, tags=["Auth"])
def refresh(request: Request, db: Session = Depends(database.get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    refresh_token = auth_header.split(" ")[1]
    return auth.refresh_user_token(refresh_token, db)


@app.post("/api/auth/logout", tags=["Auth"])
def logout(request: Request, db: Session = Depends(database.get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    refresh_token = auth_header.split(" ")[1]
    return auth.logout_user(refresh_token, db)

# =======================================================================================================================
# Events Main APIs
# =======================================================================================================================


@app.post("/api/events", response_model=schemas.EventOut, tags=["Events"])
def create_event(event: schemas.EventCreate, db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(events.get_current_user)):
    return events.create_event_logic(event=event, db=db, current_user=current_user)


@app.get("/api/events", response_model=List[schemas.EventOut], tags=["Events"])
def list_events(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db),
                current_user: models.User = Depends(events.get_current_user)):
    return events.list_events_logic(skip=skip, limit=limit, db=db, current_user=current_user)


@app.get("/api/events/{event_id}", response_model=schemas.EventOut, tags=["Events"])
def get_event(event_id: int, db: Session = Depends(database.get_db),
              current_user: models.User = Depends(events.get_current_user)):
    return events.get_event_logic(event_id=event_id, db=db, current_user=current_user)


@app.put("/api/events/{event_id}", response_model=schemas.EventOut, tags=["Events"])
def update_event(event_id: int, event_data: schemas.EventCreate, db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(events.get_current_user)):
    return events.update_event_logic(event_id=event_id, event_data=event_data, db=db, current_user=current_user)


@app.delete("/api/events/{event_id}", tags=["Events"])
def delete_event(event_id: int, db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(events.get_current_user)):
    return events.delete_event_logic(event_id=event_id, db=db, current_user=current_user)


@app.post("/api/events/batch", response_model=List[schemas.EventOut], tags=["Events"])
def create_batch_events(events_list: List[schemas.EventCreate], db: Session = Depends(database.get_db),
                        current_user: models.User = Depends(events.get_current_user)):
    print(events_list)
    return events.create_batch_events_logic(events=events_list, db=db, current_user=current_user)

# =======================================================================================================================
# Collaboration APIs
# =======================================================================================================================


@app.post("/api/events/{id}/share", tags=["Collaboration"])
def share_event(id: int, request: schemas.ShareRequest, db: Session = Depends(database.get_db),
                current_user: models.User = Depends(events.get_current_user)):
    return events.share_event(id, current_user.id, request.users, db)


@app.get("/api/events/{id}/permissions", tags=["Collaboration"])
def list_permissions(id: int, db: Session = Depends(database.get_db),
                     current_user: models.User = Depends(events.get_current_user)):
    return events.get_event_permissions(id, current_user.id, db)


@app.put("/api/events/{id}/permissions/{userId}", tags=["Collaboration"])
def update_permission(id: int, userId: int, role: str, db: Session = Depends(database.get_db),
                      current_user: models.User = Depends(events.get_current_user)):
    return events.update_event_permission(id, current_user.id, userId, role, db)


@app.delete("/api/events/{id}/permissions/{userId}", tags=["Collaboration"])
def remove_permission(id: int, userId: int, db: Session = Depends(database.get_db),
                      current_user: models.User = Depends(events.get_current_user)):
    return events.remove_event_permission(id, current_user.id, userId, db)

# =======================================================================================================================
# Versioning APIs
# =======================================================================================================================


@app.get("/api/events/{id}/history/{versionId}", tags=["Version History"])
def get_version(id: int, versionId: int, db: Session = Depends(database.get_db),
                current_user: models.User = Depends(events.get_current_user)):
    return events.get_event_version(id, versionId, current_user.id, db)


@app.post("/api/events/{id}/rollback/{versionId}", tags=["Version History"])
def rollback_version(id: int, versionId: int, db: Session = Depends(database.get_db),
                     current_user: models.User = Depends(events.get_current_user)):
    return events.rollback_event_to_version(id, versionId, current_user.id, db)

# =======================================================================================================================
# ChangeLogs APIs
# =======================================================================================================================


@app.get("/api/events/{id}/changelog", tags=["Changelog"])
def get_event_changelog(id: int, db: Session = Depends(database.get_db),
                        current_user: models.User = Depends(events.get_current_user)):
    return events.get_event_changelog(id, current_user.id, db)


@app.get("/api/events/{id}/diff/{versionId1}/{versionId2}", tags=["Changelog"])
def get_event_diff(id: int, versionId1: int, versionId2: int, db: Session = Depends(database.get_db),
                   current_user: models.User = Depends(events.get_current_user)):
    return events.get_event_diff(id, versionId1, versionId2, current_user.id, db)
