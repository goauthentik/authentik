FROM golang:1.15 AS builder

WORKDIR /work

COPY . .

RUN go build -o /work/proxy .

# Copy binary to alpine
FROM gcr.io/distroless/base-debian10
COPY --from=builder /work/proxy /
ENTRYPOINT ["/proxy"]
