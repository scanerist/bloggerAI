FROM python:3.12.1-alpine

WORKDIR /code/src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /code/src/requirements.txt

RUN set -eux \
    && apk add --no-cache --virtual .build-deps python3 py3-pip \
    && pip install --upgrade pip setuptools wheel \
    && pip install fastapi uvicorn \
    && pip install -r /code/src/requirements.txt \
    && rm -rf /root/.cache/pip

COPY . /code/src

CMD python -m services.database.main; sleep infinity