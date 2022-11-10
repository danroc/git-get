"""git-get script."""

__version__ = "0.1.1"

from dataclasses import dataclass
import enum
import os
import subprocess
import sys
import typer


app = typer.Typer()


# Default configuration, which can be overridden by environment variables.
config = {
    "GIT_GET_REPOS_DIR": "~/repos",
    "GIT_GET_SSH_USERS": "danroc,LedgerHQ",
    "GIT_GET_DEFAULT_PREFIX": "https://github.com/",
}

config = {k: os.getenv(k, config[k]) for k in config}


class DelimiterNotFound(Exception):
    pass


class InvalidURL(Exception):
    pass


class Schema(enum.Enum):
    SSH = enum.auto()
    HTTP = enum.auto()


DELIMITERS = {
    Schema.SSH: ["@", ":", "/", ".git"],
    Schema.HTTP: ["://", "/", "/", ".git"],
}


@dataclass
class Reader:
    s: str
    i: int = 0

    def to(self, delimiter: str) -> str:
        j = self.s.find(delimiter, self.i)
        if j == -1:
            raise DelimiterNotFound

        k = self.i
        self.i = j + len(delimiter)
        return self.s[k:j]


def parse(url: str) -> list[str]:
    for delimiters in DELIMITERS.values():
        try:
            reader = Reader(url)
            return [reader.to(d) for d in delimiters][-3:]
        except DelimiterNotFound:
            pass
    raise InvalidURL


@app.command()
def main(repo_url: str):
    clone_url = repo_url.strip()
    if not clone_url.endswith(".git"):
        clone_url += ".git"

    try:
        # Try to parse the URL
        host, user, repo = parse(clone_url)
    except InvalidURL:
        # Retry with the prefix
        clone_url = config["GIT_GET_DEFAULT_PREFIX"] + clone_url
        host, user, repo = parse(clone_url)

        # Check if should force SSH
        if user in config["GIT_GET_SSH_USERS"].split(","):
            clone_url = f"git@{host}:{user}/{repo}.git"

    path = os.path.join(config["GIT_GET_REPOS_DIR"], host, user, repo)
    path = os.path.expanduser(path)

    print(f"Cloning repo '{clone_url}'...")
    out = subprocess.run(["git", "clone", clone_url, path])
    sys.exit(out.returncode)


if __name__ == "__main__":
    app()
