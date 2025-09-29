from pydantic import BaseModel

from app.features.notifications.models import SubscriptionType


class SubscriptionCreate(BaseModel):
    artist_id: int


class SubscriptionOut(BaseModel):
    id: int
    artist_id: int
    group_name: str | None = None
    stage_name: str | None = None
    is_active: bool
    subscription_type: SubscriptionType

    class Config:
        from_attributes = True


class SubscriptionWithImageOut(BaseModel):
    id: int
    artist_id: int
    group_name: str | None = None
    stage_name: str | None = None
    artist_image_url: str | None = None
    is_active: bool
    subscription_type: SubscriptionType

    class Config:
        from_attributes = True
