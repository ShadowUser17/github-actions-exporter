import os
import sys
import boto3
import base64
import logging
import traceback
import subprocess

# DEBUG_MODE
# IMAGE_NAME
# IMAGE_TAG
# AWS_ECR_NAME
# AWS_DEFAULT_REGION
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY


# return ["user", "password"]
def get_auth_token(client: any) -> list:
    responce = client.get_authorization_token()
    tmp = base64.b64decode(responce["authorizationData"][0]["authorizationToken"])
    return tmp.decode().split(":")


def exec_command(args: list) -> None:
    logging.info("Run: {}".format(" ".join(args)))
    cmd = subprocess.Popen(args=args, shell=False)

    status = cmd.wait()
    if status:
        raise Exception("Command exit status: {} != 0".format(status))


def error_if_empty(arg: str) -> str:
    if not arg:
        raise Exception("The required argument is empty!")

    return arg


try:
    log_level = logging.DEBUG if os.environ.get("DEBUG_MODE", "") else logging.INFO
    logging.basicConfig(
        format=r'%(levelname)s [%(asctime)s]: "%(message)s"',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        level=log_level
    )

    aws_ecr_name = error_if_empty(os.environ.get("AWS_ECR_NAME"))
    image_name = error_if_empty(os.environ.get("IMAGE_NAME"))
    image_tag = error_if_empty(os.environ.get("IMAGE_TAG"))

    client = boto3.client("ecr")
    (aws_ecr_login, aws_ecr_passwd) = get_auth_token(client)

    docker_cmd_path = "/usr/bin/docker"
    aws_ecr_dst_name = "{}/{}:{}".format(aws_ecr_name, image_name, image_tag)

    exec_command([docker_cmd_path, "login", "-u", aws_ecr_login, "-p", aws_ecr_passwd, aws_ecr_name])
    exec_command([docker_cmd_path, "build", "-t", aws_ecr_dst_name, "."])
    exec_command([docker_cmd_path, "push", aws_ecr_dst_name])

except Exception:
    logging.error(traceback.format_exc())
    sys.exit(1)
