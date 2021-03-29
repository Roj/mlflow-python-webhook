"""Defines a hook and pydantic models to respond to GitHub's webhook
requests."""
import yaml
from mlflow_webhook.pipeline import Pipeline
from pydantic import BaseModel


class Repository(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str


class User(BaseModel):
    name: str
    email: str


class Commit(BaseModel):
    id: str
    message: str
    url: str
    timestamp: str
    committer: User


class Event(BaseModel):
    ref: str
    before: str
    after: str
    created: bool
    deleted: bool
    forced: bool
    pusher: User
    repository: Repository
    head_commit: Commit


def hook(event, pipeline):
    print(f"New event for ref {event.ref}")
    print(f"Pusher is {event.pusher}")
    print(f"Commit is {event.head_commit}")
    if event.ref == f"refs/head/{pipeline.branch}":
        pipeline.run_pipeline(event.before)
    return {}
