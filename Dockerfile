# Dockerfile
FROM python:3.11-slim

# Avoid cache busting
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install necessary packages and clean up.
# Ignore hadolint check for version specific apt-get install
# hadolint ignore=DL3008
RUN apt-get update && apt-get -y --no-install-recommends install \
    tzdata git \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*'

COPY entrypoint.sh /entrypoint
ENTRYPOINT ["/entrypoint"]
