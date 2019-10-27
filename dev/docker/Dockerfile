ARG arch=library

FROM python:alpine as builder

ARG HOMEPAGE_URL

RUN apk add --no-cache git jq moreutils
COPY . /src
RUN cd /src && \
    ./docs/docker/versioning-build.sh

FROM ${arch}/nginx:alpine

COPY --from=builder /src/build/docs /usr/share/nginx/html/
