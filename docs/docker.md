# Docker

## Use the image

 > It is recommended to have a look to the [Quick Start](./quick-start.md) if you did not do it yet...

*To be done...*

## Build image

There are two flavours for the `mdbackup` image: one based on Alpine Linux and the other based on Debian (slim).

To build the Debian version, run:

```sh
docker image build -t mdbackup:slim -f docker/Dockerfile-slim .
```

To build the Alpine Linux version, then run:

```sh
docker image build -t mdbackup:slim -f docker/Dockerfile-alpine .
```