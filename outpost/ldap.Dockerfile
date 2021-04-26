FROM golang:1.16.3 AS builder

WORKDIR /work

COPY . .

RUN go build -o /work/ldap ./cmd/ldap

FROM gcr.io/distroless/base-debian10:debug

COPY --from=builder /work/ldap /

ENTRYPOINT ["/ldap"]
