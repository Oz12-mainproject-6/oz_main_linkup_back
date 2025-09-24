from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class ScheduleBase(BaseModel):
    artist: str
    date: date
    time: Optional[time] = None
    event: str
    location: Optional[str] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleRead(ScheduleBase):
    id: int

    class Config:
        orm_mode = True   # SQLAlchemy 모델 → Pydantic 변환 허용
