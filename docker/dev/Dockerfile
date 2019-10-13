FROM python:3.7-alpine

COPY ./docker/dev/requirements.dev.txt /r1.txt
COPY ./docker/requirements.txt /r2.txt
RUN pip install -r r1.txt && pip install -r r2.txt
