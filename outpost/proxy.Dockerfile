FROM golang:1.16.4 AS builder
ARG GIT_BUILD_HASH
ENV GIT_BUILD_HASH=$GIT_BUILD_HASH

WORKDIR /work

COPY . .

RUN go build -o /work/proxy ./cmd/proxy

FROM gcr.io/distroless/base-debian10:debug

COPY --from=builder /work/proxy /

HEALTHCHECK CMD [ "wget", "--spider", "http://localhost:4180/akprox/ping" ]

ENTRYPOINT ["/proxy"]
