from pydantic import BaseModel

from app.auth.schemas import UserRead
from app.schemas.channel import ChannelOut
from app.schemas.folder import FolderOut
from app.schemas.playlist import PlaylistDetailOut
from app.schemas.tag import TagOut


class RuntimeFeaturesOut(BaseModel):
    registration: bool
    background_jobs: bool
    youtube_oauth: bool
    demo_login: bool
    subscription_imports: bool


class RuntimeMetadataOut(BaseModel):
    name: str
    version: str
    mode: str
    features: RuntimeFeaturesOut


class AppBootstrapOut(BaseModel):
    current_user: UserRead
    folders: list[FolderOut]
    channels: list[ChannelOut]
    tags: list[TagOut]
    watch_later: PlaylistDetailOut
    runtime: RuntimeMetadataOut
