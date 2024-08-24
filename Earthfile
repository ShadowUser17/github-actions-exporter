VERSION 0.8
FROM python:3-alpine
WORKDIR /root

docker:
    ARG tag="latest"
    COPY requirements.txt main.py .
    RUN python3 -m venv env
    RUN ./env/bin/pip3 install --no-cache -r requirements.txt
    EXPOSE 8080/tcp
    ENTRYPOINT ["./env/bin/python3", "main.py"]
    SAVE IMAGE --push "shadowuser17/github-actions-exporter:$tag"

all:
    BUILD +docker
