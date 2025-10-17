from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: Optional[List[str]] = []
    evaluation_url: str
    attachments: Optional[Dict[str, Any]] = {}


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