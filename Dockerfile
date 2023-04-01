FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends install \
    make automake gcc g++ tzdata git \
    && apt-get autoremove && apt-get clean all -y

COPY entrypoint.sh /entrypoint
ENTRYPOINT ["/entrypoint"]