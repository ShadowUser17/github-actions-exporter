import os
import sys
import github
import logging
import traceback

# DEBUG_MODE
# GITHUB_ORG
# GITHUB_TOKEN


try:
    log_level = logging.DEBUG if os.environ.get("DEBUG_MODE", "") else logging.INFO
    logging.basicConfig(
        format=r'%(levelname)s [%(asctime)s]: "%(message)s"',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        level=log_level
    )

    github_token = os.environ.get("GITHUB_TOKEN")
    github_org = os.environ.get("GITHUB_ORG")
    client = github.Github(auth=github.Auth.Token(github_token))

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
