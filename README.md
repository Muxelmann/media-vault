# Media Vault

A simple media library display service.

Built using:

```
docker buildx build \
    --push \
    --platform linux/arm64/v8,linux/arm/v7,linux/amd64 \
    --tag muxelmann/media-vault \
    .
```

Run using:

```
docker run \
    -v <HOST_DATA_PATH>:/data:r \
    -e FLASK_SECRET=<SOME_SECRET> \
    -p 80:5000 \
    muxelmann/media-vault
```