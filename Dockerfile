# syntax=docker/dockerfile:1
FROM python:slim-bookworm

# install app dependencies
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip install django==3.10.*
