# muxelmann/media-vault:2.0.0 (and :xxx-dev and :latest)
# docker buildx build \
#     --push \
#     --platform linux/arm64/v8,linux/arm/v7,linux/amd64 \
#     --tag muxelmann/media-vault:2.0.0-dev \
#     .
FROM muxelmann/media-vault:2.x-base

COPY ./src /app
