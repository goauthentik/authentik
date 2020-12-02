FROM python:3.9-slim-buster as locker

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/

WORKDIR /app/

RUN pip install pipenv && \
    pipenv lock -r > requirements.txt && \
    pipenv lock -rd > requirements-dev.txt

FROM node as npm-builder

COPY ./web /static/

RUN cd /static && npm i && npm run build

FROM nginx

COPY --from=npm-builder /static/robots.txt /usr/share/nginx/html/robots.txt
COPY --from=npm-builder /static/node_modules /usr/share/nginx/html/static/node_modules
COPY --from=npm-builder /static/dist/ /usr/share/nginx/html/static/dist/
