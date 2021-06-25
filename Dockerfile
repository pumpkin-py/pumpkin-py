FROM python:3.9.5-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends install \
    make=4.2.1-1.2 automake=1:1.16.1-4 gcc=4:8.3.0-1 g++=4:8.3.0-1 \
    tzdata=2021a-0+deb10u1 git=1:2.20.1-2+deb10u3

ENV TZ=Europe/Prague

VOLUME /Pumpkin
WORKDIR /Pumpkin

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user --no-warn-script-location

RUN apt-get -y remove make automake gcc g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
