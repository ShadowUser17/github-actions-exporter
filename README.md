### GitHub Actions Prometheus Exporter

#### Configure environment:
```bash
python3 -m venv --upgrade-deps env && \
./env/bin/pip3 install -r requirements_dev.txt
```

#### Scan project dependencies:
```bash
./env/bin/pip-audit -f json | python3 -m json.tool
```

#### Validate project files:
```bash
./env/bin/flake8 --ignore="E501" *.py
```

#### Run exporter manually:
```bash
export DEBUG_MODE=""
export HTTP_ADDR="127.0.0.1"
export HTTP_PORT="8080"
```
- Authentication with PAT:
```bash
export GITHUB_ORG=""
export GITHUB_TOKEN=""
```
- Authentication with APP:
```bash
export GITHUB_ORG=""
export GITHUB_APP_ID=""
export GITHUB_APP_KEY=""
```
```bash
./env/bin/python3 main.py
```

#### Build docker image:
- Prune build cache:
```bash
earthly prune
```
- Build stable version:
```bash
earthly +all --tag="latest"
```
- Build testing version:
```bash
earthly +all --tag="testing"
```

#### Scan docker image:
```bash
dockle "shadowuser17/github-actions-exporter:testing"
```
```bash
trivy image "shadowuser17/github-actions-exporter:testing"
```

#### Publish docker image:
```bash
docker login -u "${DOCKERHUB_LOGIN}" -p "${DOCKERHUB_TOKEN}"
```
```bash
earthly --push +all --tag="latest"
```
```bash
earthly --push +all --tag="testing"
```

#### Publish docker image to AWS/ECR:
```bash
export IMAGE_NAME=""
export IMAGE_TAG=""
export AWS_ECR_NAME=""
export AWS_DEFAULT_REGION=""
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
```
```bash
./env/bin/python3 push_aws_ecr.py
```
```bash
docker logout "${AWS_ECR_NAME}"
```

#### Deploy to K8S:
```bash
kubectl create ns testing
```
```bash
kubectl apply -f deploy/config.yml -n testing
```
```bash
kubectl apply -f deploy/deploy.yml -n testing
```
```bash
kubectl apply -f deploy/monitoring.yml -n testing
```

#### Dependencies:
- [PyGithub](https://github.com/PyGithub/PyGithub)
- [prometheus-client](https://github.com/prometheus/client_python)
