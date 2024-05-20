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

#### Build docker image:
- Stable version:
```bash
docker build -t "shadowuser17/github-actions-exporter:latest" .
```
- Testing version:
```bash
docker build -t "shadowuser17/github-actions-exporter:testing" .
```

#### Scan docker image:
```bash
dockle "shadowuser17/github-actions-exporter:latest"
```
```bash
trivy image "shadowuser17/github-actions-exporter:latest"
```

#### Publish docker image:
```bash
docker login -u "${DOCKERHUB_LOGIN}" -p "${DOCKERHUB_TOKEN}"
```
```bash
docker push "shadowuser17/github-actions-exporter:latest"
```

#### Dependencies:
- [PyGithub](https://github.com/PyGithub/PyGithub)
- [prometheus-client](https://github.com/prometheus/client_python)
