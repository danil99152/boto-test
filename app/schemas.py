from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    url: HttpUrl
    code: str | None = None


class ShortenResponse(BaseModel):
    short_url: str


class UpdateUrlRequest(BaseModel):
    url: HttpUrl

