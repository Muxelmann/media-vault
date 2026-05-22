# Media Vault

A simple media library display service.

Built using:

```
docker buildx create --use default
docker buildx build \
    --push \
    --platform linux/arm64/v8,linux/arm/v7,linux/amd64 \
    --tag muxelmann/media-vault \
    .
```

Run using:

```
docker buildx create --use default
docker run \
    -v <HOST_DATA_PATH>:/data:ro \
    -e FLASK_SECRET=<SOME_SECRET> \
    -p 8080:80 \
    muxelmann/media-vault
```

The layout is inspired by that of [Synology Photos](https://www.synology.com/en-en/dsm/feature/photos). But several features are missing and this service is no way near as nice looking.

For debugging use:

```
docker build -t muxelmann/media-vault .
docker run --rm -it -p 5002:80 -v ${PWD}/data:/data -v ${PWD}/tmp:/tmp -e FLASK_SECRET=12345678 muxelmann/media-vault
```