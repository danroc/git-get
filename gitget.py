"""Automatically clone Git repos."""

from __future__ import annotations

import enum
import os
import re
import subprocess  # noqa: S404
import sys
from dataclasses import dataclass

import typer

__version__ = "0.1.3"

app = typer.Typer()


class Options(str, enum.Enum):
    REPOS_DIR = "GIT_GET_REPOS_DIR"
    SSH_USERS = "GIT_GET_SSH_USERS"
    DEFAULT_PREFIX = "GIT_GET_DEFAULT_PREFIX"


# Default configuration, which can be overridden by environment variables.
config = {
    Options.REPOS_DIR: "~/repos",
    Options.SSH_USERS: "danroc,metamask",
    Options.DEFAULT_PREFIX: "https://github.com/",
}

config = {k: os.getenv(k, config[k]) for k in config}


class InvalidURL(Exception):
    pass


class Schema(enum.Enum):
    SSH = enum.auto()
    HTTP = enum.auto()


FORMATS = {
    Schema.SSH: re.compile(
        r"^(.*?)@(?P<host>.*?):(?P<user>.*?)/(?P<repo>.*?)\.git$",
    ),
    Schema.HTTP: re.compile(
        r"^https?://(?P<host>.*?)(?P<port>:\d+)?/(?P<user>.*?)/(?P<repo>.*?)\.git$",
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
def main(repo_url: str) -> None:
    clone_url = repo_url.strip()
    if not clone_url.endswith(".git"):
        clone_url += ".git"

    try:
        # Try to parse the URL
        repo = parse(clone_url)
    except InvalidURL:
        # Retry with the prefix
        clone_url = config[Options.DEFAULT_PREFIX] + clone_url
        repo = parse(clone_url)

        # Check if should force SSH
        use_ssh_on = config[Options.SSH_USERS].lower().split(",")
        if repo.user.lower() in use_ssh_on:
            clone_url = f"git@{repo.host}:{repo.user}/{repo.name}.git"

    path = os.path.join(config[Options.REPOS_DIR], repo.host, repo.user, repo.name)
    path = os.path.expanduser(path)

    print(f"Cloning repo '{clone_url}'...")
    out = subprocess.run(["git", "clone", clone_url, path])  # noqa: S603,S607
    sys.exit(out.returncode)


if __name__ == "__main__":
    app()
