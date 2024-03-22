# Dockerfile
FROM python:3.11-slim

# Avoid cache busting
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user
RUN useradd -m myuser

# Install necessary packages and clean up
RUN apt-get update && apt-get -y --no-install-recommends install \
    tzdata git \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set git config
RUN git config --global --add safe.directory '*'

# Switch to non-root user
USER myuser

COPY entrypoint.sh /entrypoint
ENTRYPOINT ["/entrypoint"]
