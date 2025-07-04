FROM --platform=${BUILDPLATFORM} docker.io/library/node:24-slim AS docs-builder

ENV NODE_ENV=production

WORKDIR /work/docs

COPY ./website/package.json ./website/package-lock.json /work/docs/

RUN npm ci

COPY ./website /work/docs/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./docker-compose.yml /work/
COPY ./SECURITY.md /work/

RUN npm run build

FROM docker.io/library/nginx:1.29.0

COPY --from=docs-builder /work/docs/build /usr/share/nginx/html
