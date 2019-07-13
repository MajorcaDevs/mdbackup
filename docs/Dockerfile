ARG arch=library

FROM python:alpine as builder

COPY . /src
RUN cd /src && \
    pip install -r docs/requirements.txt && \
    mkdocs build --config-file=mkdocs.yaml


FROM ${arch}/nginx:alpine

COPY --from=builder /src/build/docs /usr/share/nginx/html/
