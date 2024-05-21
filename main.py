import os
import sys
import time
import queue
import logging
import threading
import traceback

from github import Auth
from github import Github
from github.Workflow import Workflow
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
    logging.debug("get_github_org({}, {})".format(client, org))
    return client.get_organization(os.environ.get("GITHUB_ORG", org))


def get_github_repos(org: Organization, repos_type: str = "") -> list[Repository]:
    logging.debug("get_github_repo_list({}, {})".format(org, repos_type))
    return list(org.get_repos(type=repos_type))


def get_github_repo_workflows(repo: Repository) -> list[Workflow]:
    logging.debug("get_repo_workflow_list({})".format(repo))
    return list(repo.get_workflows())


def get_github_workflow_runs(workflow: Workflow, status: str = "") -> list[WorkflowRun]:
    logging.debug("get_github_workflow_runs({}, {})".format(workflow, status))
    return list(workflow.get_runs(status=status))


def configure_logger() -> None:
    log_level = logging.DEBUG if os.environ.get("DEBUG_MODE", "") else logging.INFO
    logging.basicConfig(
        format=r'%(levelname)s [%(asctime)s]: "%(message)s"',
        datefmt=r'%Y-%m-%d %H:%M:%S', level=log_level
    )


def start_http_endpoint(http_addr: str = "127.0.0.1", http_port: str = "8080") -> None:
    logging.debug("start_http_endpoint({}, {})".format(http_addr, http_port))
    http_addr = os.environ.get("HTTP_ADDR", http_addr)
    http_port = os.environ.get("HTTP_PORT", http_port)

    logging.info("Start HTTP server: {}:{}".format(http_addr, http_port))
    start_http_server(addr=http_addr, port=int(http_port))


def start_repos_worker(org: Organization, repos: queue.Queue, scrape_int: float) -> None:
    logging.debug("start_repos_worker({}, {}, {})".format(org, repos, scrape_int))
    while True:
        for repo in get_github_repos(org, "sources"):
            repos.put(repo)

        time.sleep(scrape_int)


def start_workflows_worker(repos: queue.Queue, workflows: queue.Queue) -> None:
    logging.debug("start_workflows_worker({})".format(repos))
    github_repo_workflows = Gauge(
        name="github_repo_workflows",
        labelnames=["workflow_id", "repo", "name", "state"],
        documentation="Information of repository workflows."
    )

    while True:
        repo = repos.get()
        for workflow in get_github_repo_workflows(repo):
            workflows.put(workflow)

            github_repo_workflows.labels(
                workflow_id=workflow.id,
                repo=repo.name,
                name=workflow.name,
                state=workflow.state
            ).set(1)

        repos.task_done()
        time.sleep(1)


def start_workflow_runs_worker(workflows: queue.Queue) -> None:
    logging.debug("start_workflow_runs_worker({})".format(workflows))
    github_repo_workflow_runs = Gauge(
        name="github_repo_workflow_runs",
        labelnames=["run_id", "name", "status", "conclusion", "workflow_id"],
        documentation="Information of workflow runs."
    )

    while True:
        workflow = workflows.get()
        for run in get_github_workflow_runs(workflow):
            github_repo_workflow_runs.labels(
                run_id=run.id,
                name=run.name,
                status=run.status,
                conclusion=run.conclusion,
                workflow_id=run.workflow_id
            ).set(1)

        workflows.task_done()
        time.sleep(1)


try:
    configure_logger()
    org = get_github_org(client=get_github_client())
    scrape_int = float(os.environ.get("SCRAPE_INTERVAL", "120"))

    workers = []
    repos = queue.Queue()
    workflows = queue.Queue()

    start_http_endpoint()
    workers.append(threading.Thread(target=start_repos_worker, args=(org, repos, scrape_int,)))
    workers.append(threading.Thread(target=start_workflows_worker, args=(repos, workflows,)))
    workers.append(threading.Thread(target=start_workflow_runs_worker, args=(workflows,)))

    for thr in workers:
        thr.start()

    for thr in workers:
        thr.join()

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
