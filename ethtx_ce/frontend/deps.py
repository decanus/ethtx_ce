#  Copyright 2021 DAI Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import os
import re
from typing import Tuple

import pkg_resources
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from git import Repo

from ethtx_ce.config import Config

log = logging.getLogger(__name__)

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username: str, password: str) -> bool:
    """Verify user, return bool."""
    return (
        username == Config.ETHTX_ADMIN_USERNAME
        and password == Config.ETHTX_ADMIN_PASSWORD
    )


def read_ethtx_versions(app: Flask) -> None:
    """Read ethtx and ethtx_ce versions."""
    ethtx_version = pkg_resources.get_distribution("ethtx").version

    try:
        remote_url, sha = _get_version_from_git()
    except Exception:
        remote_url, sha = _get_version_from_docker()

    ethtx_ce_version = f"{_clean_up_git_link(remote_url)}/tree/{sha}"

    log.info("EthTx version: %s. EthTx CE version: %s", ethtx_version, ethtx_ce_version)

    app.config["ethtx_version"] = ethtx_version
    app.config["ethtx_ce_version"] = ethtx_ce_version


def _get_version_from_git() -> Tuple[str, str]:
    """Get EthTx CE version from .git"""
    repo = Repo(__file__, search_parent_directories=True)

    remote_url = repo.remote("origin").url
    sha = repo.head.commit.hexsha
    short_sha = repo.git.rev_parse(sha, short=True)

    return remote_url, short_sha


def _get_version_from_docker() -> Tuple[str, str]:
    """Get EthTx CE version from env."""
    return os.getenv("GIT_URL", ""), os.getenv("GIT_SHA", "")


def _clean_up_git_link(git_link: str) -> str:
    """Clean up git link, delete .git extension, make https url."""
    if "@" in git_link:
        git_link.replace(":", "/").replace("git@", "https://")

    if git_link.endswith(".git"):
        git_link = git_link[:-4]

    return git_link


def extract_tx_hash_from_req() -> str:
    """Extract tx hash from request url."""
    hash_match = re.search(r"(0x)?([A-Fa-f0-9]{64})", request.url)

    return (
        f"{hash_match.group(0) or ''}{hash_match.group(1)}"
        if hash_match and len(hash_match.groups()) == 2
        else ""
    )
