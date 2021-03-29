"""Mounts a FastAPI server that listens to github webhooks and runs MLFlow
pipelines on modified entrypoints."""
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel

from pipeline import Pipeline

CONFIG_FILE = "config.yaml"


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


def load_config():
    with open(CONFIG_FILE) as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


app = FastAPI()
pipeline = Pipeline(load_config())


@app.post("/webhook")
async def webhook(event: Event):
    # TODO: secret
    print(f"New event for ref {event.ref}")
    print(f"Pusher is {event.pusher}")
    print(f"Commit is {event.head_commit}")
    if event.ref == f"refs/head/{config.branch}":
        pipeline.run_mlflow_on_changed(event.before)
    return {}


if __name__ == "__main__":
    uvicorn.run("server:app", port=8888, host="0.0.0.0")
