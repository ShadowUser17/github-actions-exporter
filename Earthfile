VERSION 0.8
FROM python:3-alpine
WORKDIR /root

deps:
    COPY requirements.txt .
    RUN python3 -m venv env
    RUN ./env/bin/pip3 install --no-cache -r requirements.txt
    SAVE ARTIFACT env

docker:
    ARG tag="latest"
    COPY +deps/env env
    COPY main.py .
    ENTRYPOINT ["./env/bin/python3", "main.py"]
    EXPOSE 8080/tcp
    SAVE IMAGE --push "shadowuser17/github-actions-exporter:$tag"

all:
    BUILD +deps
    BUILD +docker
