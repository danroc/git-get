"""git-get script."""

from __future__ import annotations

import enum
import os
import re
import subprocess
import sys
from dataclasses import dataclass

import typer

__version__ = "0.1.2"

app = typer.Typer()


# Default configuration, which can be overridden by environment variables.
config = {
    "GIT_GET_REPOS_DIR": "~/repos",
    "GIT_GET_SSH_USERS": "danroc,MetaMask",
    "GIT_GET_DEFAULT_PREFIX": "https://github.com/",
}

config = {k: os.getenv(k, config[k]) for k in config}


class InvalidURL(Exception):
    pass


class Schema(enum.Enum):
    SSH = enum.auto()
    HTTP = enum.auto()


FORMATS = {
    Schema.SSH: re.compile(r"^(.*?)@(?P<host>.*?):(?P<user>.*?)/(?P<repo>.*?)\.git$"),
    Schema.HTTP: re.compile(
        r"^https?://(?P<host>.*?)/(?P<user>.*?)/(?P<repo>.*?)\.git$"
    ),
}


@dataclass(frozen=True)
class Repo:
    host: str
    user: str
    name: str


def parse(url: str) -> Repo:
    for format in FORMATS.values():
        m = format.match(url)
        if m:
            return Repo(
                host=m.group("host"),
                user=m.group("user"),
                name=m.group("repo"),
            )
    raise InvalidURL


@app.command()
def main(repo_url: str):
    clone_url = repo_url.strip()
    if not clone_url.endswith(".git"):
        clone_url += ".git"

    try:
        # Try to parse the URL
        repo = parse(clone_url)
    except InvalidURL:
        # Retry with the prefix
        clone_url = config["GIT_GET_DEFAULT_PREFIX"] + clone_url
        repo = parse(clone_url)

        # Check if should force SSH
        if repo.user in config["GIT_GET_SSH_USERS"].split(","):
            clone_url = f"git@{repo.host}:{repo.user}/{repo.name}.git"

    path = os.path.join(config["GIT_GET_REPOS_DIR"], repo.host, repo.user, repo.name)
    path = os.path.expanduser(path)

    print(f"Cloning repo '{clone_url}'...")
    out = subprocess.run(["git", "clone", clone_url, path])
    sys.exit(out.returncode)


if __name__ == "__main__":
    app()
