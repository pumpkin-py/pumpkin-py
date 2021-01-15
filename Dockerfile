FROM python:3.8.3-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends \
    install git=1:2.20.1-2+deb10u3 tzdata=2020a-0+deb10u1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Europe/Prague

VOLUME /Amadeus
WORKDIR /Amadeus

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user --no-warn-script-location
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
