from pydantic import BaseModel


class ScraperParams(BaseModel):
    param1: str
    param2: str


class MatcherParams(BaseModel):
    job_id: str
