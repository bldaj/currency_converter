FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN mkdir /src
WORKDIR /src