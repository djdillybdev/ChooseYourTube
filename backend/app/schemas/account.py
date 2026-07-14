from pydantic import BaseModel, Field


class AccountDeleteRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
