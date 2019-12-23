# Docker

## Use the image

!!! Warning "Quick start guide..."
    It is recommended to have a look to the [Quick Start](./quick-start.md) if you did not do it yet...

!!! Info "Docker Hub page for images"
    The images are uploaded to [Docker Hub](https://hub.docker.com/repository/docker/majorcadevs/mdbackup) on each release and can be downloaded using `majorcadevs/mdbackup:slim` or `majorcadevs/mdbackup:alpine` images.

    Specific version tags are available and follows these format `majorcadevs/mdbackup:${VERSION}-slim` and `majorcadevs/mdbackup:${VERSION}-alpine`.

    Images target to linux/amd64, linux/arm and linux/arm64.

*To be done...*

## Build image

There are two flavours for the `mdbackup` image: one based on Alpine Linux and the other based on Debian (slim).

To build the Debian version, run:

```sh
docker image build -t majorcadevs/mdbackup:slim -f docker/Dockerfile-slim .
```

To build the Alpine Linux version, then run:

```sh
docker image build -t majorcadevs/mdbackup:alpine -f docker/Dockerfile-alpine .
```