from typing import List
from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

from . import models, schemas, database
from .token_utils import decode_token, SECRET_KEY

# =======================================================================================================================
# Events Main
# =======================================================================================================================


def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_token(token, SECRET_KEY)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(
        models.User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def create_event_logic(event: schemas.EventCreate, db: Session, current_user: models.User):
    new_event = models.Event(**event.dict(), owner_id=current_user.id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # Add event permission for owner
    permission = models.EventPermission(
        event_id=new_event.id, user_id=current_user.id, role="Owner")
    db.add(permission)
    db.commit()

    # Create initial version
    version = models.EventVersion(
        event_id=new_event.id, data=event.json(), timestamp=datetime.utcnow())
    db.add(version)
    db.commit()

    return new_event


def list_events_logic(skip: int, limit: int, db: Session, current_user: models.User):
    permissions = db.query(models.EventPermission).filter(
        models.EventPermission.user_id == current_user.id).all()
    event_ids = [p.event_id for p in permissions]
    return db.query(models.Event).filter(models.Event.id.in_(event_ids)).offset(skip).limit(limit).all()


def get_event_logic(event_id: int, db: Session, current_user: models.User):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=current_user.id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def update_event_logic(event_id: int, event_data: schemas.EventCreate, db: Session, current_user: models.User):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=current_user.id).first()
    if not permission or permission.role not in ["Owner", "Editor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient permissions")

    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    for field, value in event_data.dict().items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)

    # Create version
    version = models.EventVersion(
        event_id=event_id, data=event_data.json(), timestamp=datetime.utcnow())
    db.add(version)
    db.commit()

    return event


def delete_event_logic(event_id: int, db: Session, current_user: models.User):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=current_user.id).first()
    if not permission or permission.role != "Owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only owner can delete the event")

    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    db.delete(event)
    db.commit()
    return {"msg": "Event deleted successfully"}


def create_batch_events_logic(events: List[schemas.EventCreate], db: Session, current_user: models.User):
    new_events = []
    for event in events:
        new_event = models.Event(**event.dict(), owner_id=current_user.id)
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        # Add event permission
        permission = models.EventPermission(
            event_id=new_event.id, user_id=current_user.id, role="Owner")
        db.add(permission)

        # Create initial version
        version = models.EventVersion(
            event_id=new_event.id, data=event.model_dump_json(), timestamp=datetime.utcnow())
        db.add(version)

        db.commit()
        new_events.append(new_event)

    return new_events

# =======================================================================================================================
# Events Collaboration
# =======================================================================================================================


def share_event(event_id: int, owner_id: int, users: List[schemas.ShareUser], db: Session):
    owner_permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=owner_id).first()
    if not owner_permission or owner_permission.role != "Owner":
        raise HTTPException(
            status_code=403, detail="Only owners can share the event.")

    for user in users:
        existing = db.query(models.EventPermission).filter_by(
            event_id=event_id, user_id=user.user_id).first()
        if existing:
            existing.role = user.role
        else:
            db.add(models.EventPermission(event_id=event_id,
                   user_id=user.user_id, role=user.role))
    db.commit()
    return {"message": "Permissions updated"}


def get_event_permissions(event_id: int, user_id: int, db: Session):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=user_id).first()
    if not permission:
        raise HTTPException(status_code=403, detail="Permission denied")

    permissions = db.query(models.EventPermission).filter_by(
        event_id=event_id).all()
    return [{"user_id": p.user_id, "role": p.role} for p in permissions]


def update_event_permission(event_id: int, requester_id: int, target_user_id: int, role: str, db: Session):
    requester_permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=requester_id).first()
    if not requester_permission or requester_permission.role != "Owner":
        raise HTTPException(
            status_code=403, detail="Only owners can update permissions")

    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=target_user_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    permission.role = role
    db.commit()
    return {"message": "Permission updated"}


def remove_event_permission(event_id: int, requester_id: int, target_user_id: int, db: Session):
    requester_permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=requester_id).first()
    if not requester_permission or requester_permission.role != "Owner":
        raise HTTPException(
            status_code=403, detail="Only owners can remove permissions")

    deleted = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=target_user_id).delete()
    db.commit()
    return {"message": "Permission removed" if deleted else "Permission not found"}


# =======================================================================================================================
# Events Version History
# =======================================================================================================================

def get_event_version(event_id: int, version_id: int, user_id: int, db: Session):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=user_id).first()
    if not permission:
        raise HTTPException(status_code=403, detail="Access denied")

    version = db.query(models.EventVersion).filter_by(
        event_id=event_id, id=version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return {
        "version_id": version.id,
        "event_id": version.event_id,
        "data": version.data,
        "timestamp": version.timestamp
    }


def rollback_event_to_version(event_id: int, version_id: int, user_id: int, db: Session):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=user_id).first()
    if not permission or permission.role != "Owner":
        raise HTTPException(status_code=403, detail="Only owners can rollback")

    version = db.query(models.EventVersion).filter_by(
        event_id=event_id, id=version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    version_data = json.loads(version.data)
    for key, value in version_data.items():
        setattr(event, key, value)

    new_version = models.EventVersion(event_id=event_id, data=json.dumps(
        version_data), timestamp=datetime.utcnow())
    db.add(new_version)
    db.commit()
    return {"message": "Rolled back successfully"}


# =======================================================================================================================
# Events Changelog & Diff
# =======================================================================================================================

def get_event_changelog(event_id: int, user_id: int, db: Session):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=user_id).first()
    if not permission:
        raise HTTPException(status_code=403, detail="Access denied")

    versions = db.query(models.EventVersion).filter_by(
        event_id=event_id).order_by(models.EventVersion.timestamp.desc()).all()
    return [{"version_id": v.id, "timestamp": v.timestamp} for v in versions]


def get_event_diff(event_id: int, v1: int, v2: int, user_id: int, db: Session):
    permission = db.query(models.EventPermission).filter_by(
        event_id=event_id, user_id=user_id).first()
    if not permission:
        raise HTTPException(status_code=403, detail="Access denied")

    ver1 = db.query(models.EventVersion).filter_by(
        event_id=event_id, id=v1).first()
    ver2 = db.query(models.EventVersion).filter_by(
        event_id=event_id, id=v2).first()

    if not ver1 or not ver2:
        raise HTTPException(
            status_code=404, detail="One or both versions not found")

    if isinstance(ver1.data, dict):
        data1 = ver1.data
    else:
        data1 = json.loads(ver1.data)
    if isinstance(ver2.data, dict):
        data2 = ver2.data
    else:
        data2 = json.loads(ver2.data)

    diff = {}
    for key in data1.keys():
        if data1.get(key) != data2.get(key):
            diff[key] = {"from": data1.get(key), "to": data2.get(key)}

    return diff
