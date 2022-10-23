"""git-get script."""

__version__ = "0.1.0"

from dataclasses import dataclass
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


class InvalidURL(Exception):
    pass


def _parse(url: str, delimiters: list[str]) -> tuple[str, str, str]:
    reader = Reader(url)
    try:
        return tuple([reader.to(d) for d in delimiters][-3:])
    except DelimiterNotFound:
        raise InvalidURL


def parse(url: str) -> tuple[str, str, str]:
    try:
        # Fist try to parse SSH
        return _parse(url, ["@", ":", "/", ".git"])
    except InvalidURL:
        # Then other schemes
        return _parse(url, ["://", "/", "/", ".git"])


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

    path = os.path.join(config["GIT_GET_REPOS_DIR"], host, user, repo)
    path = os.path.expanduser(path)

    # Check if should force SSH
    if user in config["GIT_GET_SSH_USERS"].split(","):
        clone_url = f"git@{host}:{user}/{repo}.git"

    print(f"Cloning repo: {clone_url}")
    out = subprocess.run(["git", "clone", clone_url, path])
    sys.exit(out.returncode)


if __name__ == "__main__":
    app()
