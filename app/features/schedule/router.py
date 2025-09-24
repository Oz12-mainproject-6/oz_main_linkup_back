from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from . import crud, schemas

router = APIRouter()

@router.get("/schedules", response_model=List[schemas.ScheduleRead])
def read_schedules(artist: str = None, db: Session = Depends(get_db)):
    return crud.get_schedules(db, artist)

@router.post("/schedules", response_model=schemas.ScheduleRead)
def create_schedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    return crud.create_schedule(db, schedule)
