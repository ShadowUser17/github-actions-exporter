import os
import sys
import time
import logging
import threading
import traceback

from flask import Flask
# from queue import Queue

from github import Auth
from github import Github
from github.Repository import Repository
from github.Organization import Organization

from prometheus_client import Gauge
from prometheus_client.exposition import generate_latest

# DEBUG_MODE
# HTTP_ADDR
# HTTP_PORT
# GITHUB_ORG
# GITHUB_TOKEN
# SCRAPE_INTERVAL


def get_org_repos_list(org: Organization, repo_type: str = "sources") -> list:
    logging.debug("get_org_repos_list({}, {})".format(type(client), repo_type))
    repos = org.get_repos(type=repo_type)
    return [item for item in repos]


def get_repo_workflow_runs_list(repo: Repository, status: str = "queued") -> list:
    logging.debug("get_repo_workflow_runs_list({}, {})".format(type(repo), status))
    # runs = repo.get_workflow_runs(status=status)
    runs = repo.get_workflow_runs()
    return [item for item in runs]


def data_handler(org: Organization) -> None:
    scrape_int = float(os.environ.get("SCRAPE_INTERVAL", "30"))
    github_repo_workflow_runs = Gauge(
        name="github_repo_workflow_runs",
        labelnames=["repo", "status", "conclusion"],
        documentation="Information of repository workflow jobs."
    )

    while True:
        for repo in get_org_repos_list(org):
            for job in get_repo_workflow_runs_list(repo):
                github_repo_workflow_runs.labels(
                    repo=repo.name,
                    status=job.status,
                    conclusion=job.conclusion
                ).inc()

        time.sleep(30)


def http_handler(app: Flask) -> None:
    http_addr = os.environ.get("HTTP_ADDR", "127.0.0.1")
    http_port = int(os.environ.get("HTTP_PORT", "8080"))
    app.run(host=http_addr, port=http_port, debug=False)


try:
    log_level = logging.DEBUG if os.environ.get("DEBUG_MODE", "") else logging.INFO
    logging.basicConfig(
        format=r'%(levelname)s [%(asctime)s]: "%(message)s"',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        level=log_level
    )

    github_token = os.environ.get("GITHUB_TOKEN")
    github_org = os.environ.get("GITHUB_ORG")
    client = Github(auth=Auth.Token(github_token))
    org = client.get_organization(github_org)

    app = Flask(__name__)
    @app.route("/metrics")
    def get_metrics() -> str:
        return generate_latest().decode()

    threading.Thread(target=data_handler, args=(org,)).start()
    threading.Thread(target=http_handler, args=(app,)).start()

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
