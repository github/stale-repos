FROM python:3.12-slim
LABEL org.opencontainers.image.source https://github.com/github/stale-repos

WORKDIR /action/workspace
COPY requirements.txt stale_repos.py /action/workspace/

RUN python3 -m pip install --no-cache-dir -r requirements.txt \
    && apt-get -y update \
    && apt-get -y install --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

CMD ["/action/workspace/stale_repos.py"]
ENTRYPOINT ["python3", "-u"]
