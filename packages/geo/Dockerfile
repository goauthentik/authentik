FROM docker.io/library/golang:1.23-alpine AS builder

RUN apk add --no-cache git
RUN go install github.com/protomaps/go-pmtiles@latest

FROM docker.io/library/alpine:3.21

RUN apk add --no-cache ca-certificates tini \
    && addgroup -S pmtiles \
    && adduser -S -G pmtiles pmtiles

COPY --from=builder /go/bin/go-pmtiles /usr/local/bin/pmtiles

USER pmtiles
WORKDIR /tiles

EXPOSE 8484

ENTRYPOINT ["/sbin/tini", "--", "pmtiles"]
CMD ["serve", ".", "--port", "8484", "--cors", "*"]
