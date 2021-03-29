"""Defines a hook and pydantic models to respond to GitHub's webhook
requests."""
import yaml
from mlflow_webhook.pipeline import Pipeline
from pydantic import BaseModel
from termcolor import cprint


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
    cprint(f"[Hook] New event at ref {event.ref} from {event.pusher.name}", "green")
    print(
        f"[Hook] Message: \"{event.head_commit.message}\", "
        f"hash: {event.head_commit.id}"
    )
    if event.ref == f"refs/heads/{pipeline.branch}":
        cprint(f"[Hook] Running pipeline for hash {event.before}", "green")
        try:
            pipeline.run_pipeline(event.before)
        except Exception as e:
            cprint(f"Unexpected error while processing pipeline: {e}", "red")
    return {}
