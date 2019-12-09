FROM python:3.7-slim-buster as builder

WORKDIR /mkdocs

RUN apt-get update && apt-get install -y git && \
    pip install mkdocs && \
    pip install git+https://github.com/BeryJu/mkdocs-bootstrap4.git

COPY docs/ docs
COPY mkdocs.yml .

RUN mkdocs build

FROM nginx

COPY --from=builder /mkdocs/site /usr/share/nginx/html
