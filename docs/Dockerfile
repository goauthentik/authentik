FROM python:3.8-slim-buster as builder

WORKDIR /mkdocs

RUN pip install mkdocs mkdocs-material

COPY docs/ docs
COPY mkdocs.yml .

RUN mkdocs build

FROM nginx

COPY --from=builder /mkdocs/site /usr/share/nginx/html
