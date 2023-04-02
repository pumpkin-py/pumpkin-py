FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends install \
    tzdata git \
    && apt-get autoremove && apt-get clean all -y \
    && git config --global --add safe.directory '*'

COPY entrypoint.sh /entrypoint
ENTRYPOINT ["/entrypoint"]