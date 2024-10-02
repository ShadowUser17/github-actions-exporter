import os
import sys
import time
import queue
import base64
import logging
import datetime
import threading
import traceback

from github import Auth
from github import Github
from github import GithubIntegration
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
# GITHUB_APP_ID
# GITHUB_APP_KEY
# THREAD_COUNT
# SCRAPE_PERIOD
# SCRAPE_INTERVAL


def get_github_client(access_token: str = "", app_id: int = 0, app_key: str = "") -> Github:
    logging.debug("get_github_client(..., ..., ...)")

    access_token = os.environ.get("GITHUB_TOKEN", access_token)
    if access_token:
        logging.debug("Authenticate with GITHUB_TOKEN")
        return Github(auth=Auth.Token(access_token))

    else:
        app_id = int(os.environ.get("GITHUB_APP_ID", app_id))
        app_key = base64.b64decode(os.environ.get("GITHUB_APP_KEY", app_key))
        logging.debug("Authenticate with GITHUB_APP_ID and GITHUB_APP_KEY")

        auth = Auth.AppAuth(app_id, app_key.decode())
        git_integration = GithubIntegration(auth=auth)
        git_install_id = git_integration.get_installations()[0].id
        return Github(auth=auth.get_installation_auth(git_install_id))


def get_github_org(client: Github, org: str = "") -> Organization:
    logging.debug("get_github_org({}, {})".format(client, org))
    return client.get_organization(os.environ.get("GITHUB_ORG", org))


def get_github_repos(org: Organization, repos_type: str = "") -> list[Repository]:
    logging.debug("get_github_repo_list({}, {})".format(org, repos_type))
    return list(org.get_repos(type=repos_type))


def get_github_repo_workflows(repo: Repository) -> list[Workflow]:
    logging.debug("get_repo_workflow_list({})".format(repo))
    return list(repo.get_workflows())


def get_github_workflow_runs(workflow: Workflow, status: str = "", created: str = "") -> list[WorkflowRun]:
    logging.debug("get_github_workflow_runs({}, {})".format(workflow, status))
    return list(workflow.get_runs(status=status, created=created))


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


def start_repos_worker(org: Organization, repos: queue.Queue, metrics: dict, scrape_int: float) -> None:
    logging.debug("start_repos_worker({}, {}, {})".format(org, repos, scrape_int))

    try:
        while True:
            for key in metrics:
                metrics[key].clear()

            for repo in get_github_repos(org, "sources"):
                repos.put(repo)

            repos.join()
            time.sleep(scrape_int)

    except Exception:
        logging.debug("try/except block of the start_repos_worker")
        logging.error(traceback.format_exc())
        sys.exit(1)


def start_workflows_worker(repos: queue.Queue, workflows: queue.Queue, metrics: dict) -> None:
    logging.debug("start_workflows_worker({})".format(repos))

    try:
        github_repo_workflows = metrics.get("github_repo_workflows")

        while True:
            repo = repos.get()
            for workflow in get_github_repo_workflows(repo):
                if workflow.state == "active":
                    workflows.put(workflow)

                github_repo_workflows.labels(
                    workflow_id=workflow.id,
                    repo=repo.name,
                    name=workflow.name,
                    state=workflow.state
                ).set(1)

            repos.task_done()

    except Exception:
        logging.debug("try/except block of the start_workflows_worker")
        logging.error(traceback.format_exc())
        sys.exit(1)


def start_workflow_runs_worker(workflows: queue.Queue, metrics: dict, scrape_period: int) -> None:
    logging.debug("start_workflow_runs_worker({})".format(workflows))

    try:
        github_repo_workflow_runs = metrics.get("github_repo_workflow_runs")
        github_repo_workflow_run_created = metrics.get("github_repo_workflow_run_created")

        while True:
            workflow = workflows.get()
            created_after = datetime.datetime.now() - datetime.timedelta(days=scrape_period)

            # https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax#query-for-dates
            for run in get_github_workflow_runs(workflow, created=created_after.strftime(r">=%Y-%m-%d")):
                github_repo_workflow_runs.labels(
                    run_id=run.id,
                    name=run.name,
                    repo=run.repository.name,
                    status=run.status,
                    conclusion=run.conclusion,
                    workflow_id=run.workflow_id
                ).set(1)

                github_repo_workflow_run_created.labels(
                    run_id=run.id,
                    name=run.name,
                    repo=run.repository.name,
                    workflow_id=run.workflow_id
                ).set(run.created_at.timestamp())

            workflows.task_done()

    except Exception:
        logging.debug("try/except block of the start_workflow_runs_worker")
        logging.error(traceback.format_exc())
        sys.exit(1)


try:
    configure_logger()
    org = get_github_org(client=get_github_client())
    thread_count = int(os.environ.get("THREAD_COUNT", 2))
    scrape_period = int(os.environ.get("SCRAPE_PERIOD", 3))
    scrape_interval = float(os.environ.get("SCRAPE_INTERVAL", 300))

    metrics = {
        "github_repo_workflows": Gauge(
            name="github_repo_workflows",
            labelnames=["workflow_id", "repo", "name", "state"],
            documentation="Information of repository workflows."
        ),
        "github_repo_workflow_runs": Gauge(
            name="github_repo_workflow_runs",
            labelnames=["run_id", "name", "repo", "status", "conclusion", "workflow_id"],
            documentation="Information of workflow runs."
        ),
        "github_repo_workflow_run_created": Gauge(
            name="github_repo_workflow_run_created",
            labelnames=["run_id", "name", "repo", "workflow_id"],
            documentation="Information of workflow run creation."
        )
    }

    workers = []
    repos = queue.Queue()
    workflows = queue.Queue()

    start_http_endpoint()
    workers.append(threading.Thread(target=start_repos_worker, args=(org, repos, metrics, scrape_interval,)))

    for _ in range(0, thread_count):
        workers.append(threading.Thread(target=start_workflows_worker, args=(repos, workflows, metrics,)))

    for _ in range(0, thread_count):
        workers.append(threading.Thread(target=start_workflow_runs_worker, args=(workflows, metrics, scrape_period,)))

    for thr in workers:
        thr.start()

    for thr in workers:
        thr.join()

except Exception:
    logging.debug("try/except block of the main")
    logging.error(traceback.format_exc())
    sys.exit(1)
