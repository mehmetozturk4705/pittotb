# pull official base image
FROM python:3.8.0-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKERIZED 1

# install dependencies
RUN apk update &&\
    apk add libgcc py3-pip gcc python3 python3-dev openssl-dev musl-dev libffi libffi-dev &&\
    pip install cython

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8000

# copy project
COPY . /usr/src/app/
