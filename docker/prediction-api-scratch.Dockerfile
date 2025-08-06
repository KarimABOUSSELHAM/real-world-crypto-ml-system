# This Dockerfile created an image with a size of 19 MB instead of 135 MB
####################################################################################################
## Build
####################################################################################################
# rust:alpine3.21
FROM rust@sha256:fa7c28576553c431224a85c897c38f3a6443bd831be37061ab3560d9e797dc82 AS build

RUN apk update && \
    apk upgrade --no-cache && \
    apk add --no-cache lld mold musl musl-dev libc-dev cmake perl clang clang-dev openssl file \
        libressl-dev git make build-base bash curl wget zip gnupg coreutils gcc g++  zstd binutils ca-certificates upx

WORKDIR /myproject
COPY . ./
# or make build
RUN cargo build --release


####################################################################################################
## This stage is used to get the correct files into the final image
####################################################################################################
# alpine:3.21
FROM alpine@sha256:a8560b36e8b8210634f77d9f7f9efd7ffa463e380b75e2e74aff4511df3ef88c AS files

# mailcap is used for content type (MIME type) detection
# tzdata is used for timezones info
RUN apk update && \
    apk upgrade --no-cache && \
    apk add --no-cache ca-certificates mailcap tzdata

RUN update-ca-certificates

ENV USER=myproject
ENV UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    "${USER}"


####################################################################################################
## Final image
####################################################################################################
FROM scratch

# /etc/nsswitch.conf may be used by some DNS resolvers
# /etc/mime.types may be used to detect the MIME type of files
COPY --from=files --chmod=444 \
    /etc/passwd \
    /etc/group \
    /etc/nsswitch.conf \
    /etc/mime.types \
    /etc/

COPY --from=files --chmod=444 /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=files --chmod=444 /usr/share/zoneinfo /usr/share/zoneinfo

# Copy our build
COPY --from=build /myproject/target/release/prediction-api /bin/prediction-api


# Use an unprivileged user.
USER myproject:myproject

# the scratch image doesn't have a /tmp folder, you may need it
WORKDIR /tmp

WORKDIR /myproject

ENTRYPOINT ["/bin/prediction-api"]