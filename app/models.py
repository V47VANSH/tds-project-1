from pydantic import BaseModel, Field, ConfigDict
from typing import List


class Attachment(BaseModel):
    """Represents a single attachment passed alongside a task request."""
    model_config = ConfigDict(extra="allow")

    name: str
    url: str


class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: List[str] = Field(default_factory=list)
    evaluation_url: str
    attachments: List[Attachment] = Field(default_factory=list)


class EvaluationResponse(BaseModel):
    email: str
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str


class TaskResponse(BaseModel):
    status: str
    message: str
    task: str
    round: int