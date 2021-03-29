from pathlib import Path

import git
import pytest

from pipeline import Pipeline

TEST_REPO = "https://github.com/Roj/test.git"
FOLDER_REPO = "test"
CONDA_NAME = "test"
BRANCH = "mlflow"
TOP_BRANCH_COMMIT = "ebc13055cdcc846d4eddd71e7708d459136e427e"
OLDER_BRANCH_COMMIT = "784c41edcac60ec8358466fc3c02a4f0a267b588"
CONFIG = {"branch": BRANCH, "repo": FOLDER_REPO}


@pytest.fixture
def repo():
    """Pull repo"""
    if not Path(FOLDER_REPO).exists():
        git.Repo.clone_from(
            TEST_REPO, FOLDER_REPO,
        )
    repo = git.Repo(FOLDER_REPO)
    repo.git.checkout(BRANCH)
    return repo


def test_entrypoint_changed(repo):
    p = Pipeline(**CONFIG)
    returned = p.get_changed_entrypoints(OLDER_BRANCH_COMMIT)
    assert returned == ["main"]


def test_entrypoint_did_not_change(repo):
    p = Pipeline(**CONFIG)
    returned = p.get_changed_entrypoints(TOP_BRANCH_COMMIT)  # []
    assert len(returned) == 0


def test_pull_checkout_changes(repo):
    repo = git.Repo(FOLDER_REPO)
    assert repo.head.commit.hexsha == TOP_BRANCH_COMMIT
    repo.git.checkout(OLDER_BRANCH_COMMIT)
    assert repo.head.commit.hexsha == OLDER_BRANCH_COMMIT

    p = Pipeline(**CONFIG)
    p.pull_changes()

    assert repo.head.commit.hexsha == TOP_BRANCH_COMMIT
