import os
import sys
import logging
import traceback

from github import Auth
from github import Github
from github.Repository import Repository

from prometheus_client import CollectorRegistry
from prometheus_client import start_http_server
from prometheus_client import Gauge

# DEBUG_MODE
# HTTP_ADDR
# HTTP_PORT
# GITHUB_ORG
# GITHUB_TOKEN


def get_org_repos_list(client: Github, org_name: str, repo_type: str = "sources") -> list:
    logging.debug("get_org_repos_list({}, {}, {})".format(type(client), org_name, repo_type))
    org = client.get_organization(org_name)
    repos = org.get_repos(type=repo_type)
    return [item for item in repos]


def get_repo_workflow_runs_list(repo: Repository, status: str = "queued") -> list:
    logging.debug("get_repo_workflow_runs_list({}, {})".format(type(repo), status))
    runs = repo.get_workflow_runs(status=status)
    return [item for item in runs]


try:
    log_level = logging.DEBUG if os.environ.get("DEBUG_MODE", "") else logging.INFO
    logging.basicConfig(
        format=r'%(levelname)s [%(asctime)s]: "%(message)s"',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        level=log_level
    )

    # Initialise client...
    github_token = os.environ.get("GITHUB_TOKEN")
    github_org = os.environ.get("GITHUB_ORG")
    client = Github(auth=Auth.Token(github_token))

    # Initialise exporter...
    http_addr = os.environ.get("HTTP_ADDR", "0.0.0.0")
    http_port = os.environ.get("HTTP_PORT", "8080")
    registry = CollectorRegistry()
    # github_repo_workflow_runs = Gauge(name="", documentation="", labelnames={}, registry=registry)
    # start_http_server(port=int(http_port), addr=http_addr, registry=registry)

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
