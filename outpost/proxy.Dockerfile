FROM golang:1.15 AS builder

WORKDIR /work

COPY . .

RUN go build -o /work/proxy ./cmd/proxy

# Copy binary to alpine
FROM gcr.io/distroless/base-debian10:debug

COPY --from=builder /work/proxy /

HEALTHCHECK CMD [ "wget", "--spider", "http://localhost:4180/akprox/ping" ]

ENTRYPOINT ["/proxy"]
