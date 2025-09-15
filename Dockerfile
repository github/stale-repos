FROM python:3.13.7-slim@sha256:58c30f5bfaa718b5803a53393190b9c68bd517c44c6c94c1b6c8c172bcfad040
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
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appuser \
    && adduser --system --ingroup appuser --home /action/workspace --disabled-login appuser \
    && chown -R appuser:appuser /action/workspace

# Run the action as a non-root user
USER appuser

# Add a simple healthcheck to satisfy container scanners
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python3 -c "import os,sys; sys.exit(0 if os.path.exists('/action/workspace/stale_repos.py') else 1)"

CMD ["/action/workspace/stale_repos.py"]
ENTRYPOINT ["python3", "-u"]
