FROM python:3.13.7-slim@sha256:27f90d79cc85e9b7b2560063ef44fa0e9eaae7a7c3f5a9f74563065c5477cc24
LABEL com.github.actions.name="stale-repos" \
    com.github.actions.description="Find stale repositories in a GitHub organization." \
    com.github.actions.icon="check-square" \
    com.github.actions.color="white" \
    maintainer="@zkoppert" \
    org.opencontainers.image.url="https://github.com/github/stale-repos" \
    org.opencontainers.image.source="https://github.com/github/stale-repos" \
    org.opencontainers.image.documentation="https://github.com/github/stale-repos" \
    org.opencontainers.image.vendor="GitHub" \
    org.opencontainers.image.description="Find stale repositories in a GitHub organization."

WORKDIR /action/workspace
COPY requirements.txt *.py /action/workspace/

RUN python3 -m pip install --no-cache-dir -r requirements.txt \
    && apt-get -y update \
    && apt-get -y install --no-install-recommends git=1:2.47.3-0+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

CMD ["/action/workspace/stale_repos.py"]
ENTRYPOINT ["python3", "-u"]
