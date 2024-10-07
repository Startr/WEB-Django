# syntax=docker/dockerfile:1
FROM ubuntu:24.04

# install app dependencies

RUN apt-get update && apt-get install -y python3 python3-pip
RUN apt-get install -y pipenv curl git
RUN curl https://pyenv.run | bash

# set work directory
WORKDIR /app
# pipenv install in /app
COPY Pipfile Pipfile.lock /app/

# RUN pip install django==3.10.*

# copy app source code to container
COPY . /app
