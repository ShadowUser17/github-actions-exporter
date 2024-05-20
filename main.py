import os
import sys
import time
import logging
import traceback

from github import Auth
from github import Github
from github.Repository import Repository
from github.Organization import Organization

from prometheus_client import Gauge
from prometheus_client import start_http_server

# DEBUG_MODE
# HTTP_ADDR
# HTTP_PORT
# GITHUB_ORG
# GITHUB_TOKEN
# SCRAPE_INTERVAL
# GITHUB_REPOS_TYPE
# GITHUB_RUNS_STATUS


def get_org_repos_list(org: Organization, repos_type: str = "sources") -> list:
    logging.debug("get_org_repos_list({}, {})".format(type(client), repos_type))
    repos = org.get_repos(type=repos_type)
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

    github_token = os.environ.get("GITHUB_TOKEN")
    github_org = os.environ.get("GITHUB_ORG")
    github_repos_type = os.environ.get("GITHUB_REPOS_TYPE", "sources")
    github_runs_status = os.environ.get("GITHUB_RUNS_STATUS", "queued")
    client = Github(auth=Auth.Token(github_token))
    org = client.get_organization(github_org)

    http_addr = os.environ.get("HTTP_ADDR", "127.0.0.1")
    http_port = int(os.environ.get("HTTP_PORT", "8080"))
    start_http_server(addr=http_addr, port=http_port)
    logging.debug("Start HTTP server: {}:{}".format(http_addr, http_port))

    scrape_int = float(os.environ.get("SCRAPE_INTERVAL", "60"))
    github_repo_workflow_runs = Gauge(
        name="github_repo_workflow_runs",
        labelnames=["repo", "status", "conclusion"],
        documentation="Information of repository workflow jobs."
    )

    logging.debug("Start main loop...")
    while True:
        for repo in get_org_repos_list(org=org, repos_type=github_repos_type):
            for job in get_repo_workflow_runs_list(repo=repo, status=github_runs_status):
                github_repo_workflow_runs.labels(
                    repo=repo.name,
                    status=job.status,
                    conclusion=job.conclusion
                ).inc()

        time.sleep(scrape_int)

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
