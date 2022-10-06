FROM alpine as builder

WORKDIR /temp
COPY modules modules
RUN find /temp/modules/*/ -type f -name requirements.txt -exec grep -h "" {} \; | sort | uniq > /temp/requirements.txt


FROM python:3.10.7-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends install \
    make>=4.3-4.1 automake>=1:1.16.3-2 gcc>=4:10.2.1-1 g++>=4:10.2.1-1 \
    tzdata>=2021a-1+deb11u5 git>=1:2.30.2-1

ARG TZ=Europe/Prague
ENV TZ=${TZ}

WORKDIR /pumpkin-py

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt --user --no-warn-script-location --no-cache-dir

COPY --from=builder /temp/requirements.txt /temp/requirements.txt
RUN python3 -m pip install -r /temp/requirements.txt --user --no-warn-script-location --no-cache-dir

RUN apt-get -y remove make automake gcc g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
