import os
import sys
import time
import logging
import traceback

from github import Auth
from github import Github
from github.Repository import Repository
from github.WorkflowRun import WorkflowRun
from github.Organization import Organization

from prometheus_client import Gauge
from prometheus_client import start_http_server

# DEBUG_MODE
# HTTP_ADDR
# HTTP_PORT
# GITHUB_ORG
# GITHUB_TOKEN
# SCRAPE_INTERVAL


def get_github_client(token: str = "") -> Github:
    logging.debug("get_github_client({})".format(token))
    return Github(auth=Auth.Token(os.environ.get("GITHUB_TOKEN", token)))


def get_github_org(client: Github, org: str = "") -> Organization:
    logging.debug("get_github_org({}, {})".format(type(client), org))
    return client.get_organization(os.environ.get("GITHUB_ORG", org))


def get_github_repo_list(org: Organization, repos_type: str = "") -> list[Repository]:
    logging.debug("get_github_repo_list({}, {})".format(type(org), repos_type))
    return list(org.get_repos(type=repos_type))


def get_repo_workflow_runs_list(repo: Repository, status: str = "") -> list[WorkflowRun]:
    logging.debug("get_repo_workflow_runs_list({}, {})".format(type(repo), status))
    return list(repo.get_workflow_runs(status=status))


def configure_logger() -> None:
    log_level = logging.DEBUG if os.environ.get("DEBUG_MODE", "") else logging.INFO
    logging.basicConfig(
        format=r'%(levelname)s [%(asctime)s]: "%(message)s"',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        level=log_level
    )


def start_http_endpoint() -> None:
    logging.debug("start_http_endpoint()")
    http_addr = os.environ.get("HTTP_ADDR", "127.0.0.1")
    http_port = int(os.environ.get("HTTP_PORT", "8080"))

    logging.info("Start HTTP server: {}:{}".format(http_addr, http_port))
    start_http_server(addr=http_addr, port=http_port)


def start_main_worker(org: Organization) -> None:
    logging.debug("start_main_worker({})".format(type(org)))
    scrape_int = float(os.environ.get("SCRAPE_INTERVAL", "120"))

    github_repo_workflow_runs = Gauge(
        name="github_repo_workflow_runs",
        labelnames=["repo", "status", "conclusion"],
        documentation="Information of repository workflow jobs."
    )

    logging.debug("Start main loop...")
    while True:
        github_repo_workflow_runs.clear()
        for repo in get_github_repo_list(org=org, repos_type="sources"):
            for job in get_repo_workflow_runs_list(repo=repo, status=""):
                github_repo_workflow_runs.labels(
                    repo=repo.name,
                    status=job.status,
                    conclusion=job.conclusion
                ).inc()

        logging.debug("Sleep {}s...".format(scrape_int))
        time.sleep(scrape_int)


try:
    configure_logger()
    org = get_github_org(client=get_github_client())
    start_http_endpoint()
    start_main_worker(org=org)

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
