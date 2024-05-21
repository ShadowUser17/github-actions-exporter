import os
import sys
import argparse
import traceback

from github import Auth
from github import Github
from github.Repository import Repository
from github.WorkflowRun import WorkflowRun
from github.Organization import Organization

# DEBUG_MODE
# GITHUB_ORG
# GITHUB_TOKEN


def get_github_client(token: str = "") -> Github:
    return Github(auth=Auth.Token(os.environ.get("GITHUB_TOKEN", token)))


def get_github_org(client: Github, org: str = "") -> Organization:
    return client.get_organization(os.environ.get("GITHUB_ORG", org))


def get_github_repos(org: Organization, repos_type: str = "") -> list[Repository]:
    return list(org.get_repos(type=repos_type))


def get_github_repo_workflow_runs(repo: Repository, status: str = "") -> list[WorkflowRun]:
    return list(repo.get_workflow_runs(status=status))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    repo_type = ('all', 'public', 'private', 'forks', 'sources', 'member')
    run_status = ('queued', 'in_progress', 'completed', 'success', 'failure', 'neutral', 'cancelled', 'skipped', 'timed_out', 'action_required')
    parser.add_argument("-t", "--token", dest="token", default="", help="Set GitHub personal token.")
    parser.add_argument("-o", "--org", dest="org", default="", help="Set GitHub organization.")
    parser.add_argument("-r", "--type", dest="type", default="sources", choices=repo_type, help="Select type of repositories.")
    parser.add_argument("-s", "--status", dest="status", default="", choices=run_status, help="Select status of workflow runners.")
    return parser.parse_args()


try:
    args = parse_args()
    org = get_github_org(client=get_github_client(token=args.token), org=args.org)

    for repo in get_github_repos(org=org, repos_type=args.type):
        for run in get_github_repo_workflow_runs(repo=repo, status=args.status):
            print("{}: ({}: {}/{})".format(repo.name, run.name, run.status, run.conclusion))

except Exception:
    traceback.print_exc()
    sys.exit(1)
