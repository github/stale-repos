FROM python:3.13-slim@sha256:21e39cf1815802d4c6f89a0d3a166cc67ce58f95b6d1639e68a394c99310d2e5
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
COPY requirements.txt stale_repos.py /action/workspace/

RUN python3 -m pip install --no-cache-dir -r requirements.txt \
    && apt-get -y update \
    && apt-get -y install --no-install-recommends git=1:2.39.5-0+deb12u2 \
    && rm -rf /var/lib/apt/lists/*

CMD ["/action/workspace/stale_repos.py"]
ENTRYPOINT ["python3", "-u"]
