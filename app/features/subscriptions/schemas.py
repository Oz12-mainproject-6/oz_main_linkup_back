from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    artist_id: int


class SubscriptionOut(BaseModel):
    id: int
    artist_id: int
    artist_name: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


class SubscriptionWithImageOut(BaseModel):
    id: int
    artist_id: int
    artist_name: str | None = None
    artist_image_url: str | None = None
    is_active: bool

    class Config:
        from_attributes = True
