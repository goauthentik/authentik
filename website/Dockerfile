FROM --platform=${BUILDPLATFORM} docker.io/library/node:24 AS website-builder

ENV NODE_ENV=production

WORKDIR /work/website

RUN --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=cache,id=npm-website,sharing=shared,target=/root/.npm \
    npm ci --include=dev

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./SECURITY.md /work/

RUN npm run build-bundled

FROM docker.io/library/nginx:1.27.5

COPY --from=website-builder /work/website/build /usr/share/nginx/html
