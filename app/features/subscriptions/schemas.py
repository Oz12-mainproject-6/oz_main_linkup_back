from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    artist_id: int


class SubscriptionOut(BaseModel):
    id: int
    artist_id: int
    is_active: bool

    class Config:
        from_attributes = True
