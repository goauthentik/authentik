FROM --platform=${BUILDPLATFORM} docker.io/library/node:24-slim AS docs-builder

ENV NODE_ENV=production

WORKDIR /work/website

RUN --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=bind,target=/work/website/docusaurus-theme/package.json,src=./website/docusaurus-theme/package.json \
    --mount=type=bind,target=/work/website/api/package.json,src=./website/api/package.json \
    --mount=type=bind,target=/work/website/integrations/package.json,src=./website/integrations/package.json \
    --mount=type=bind,target=/work/website/docs/package.json,src=./website/docs/package.json \
    --mount=type=cache,id=npm-website,sharing=shared,target=/root/.npm \
    npm ci --workspaces --include-workspace-root

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./docker-compose.yml /work/
COPY ./SECURITY.md /work/

RUN npm run build

FROM docker.io/library/nginx:1.29.0

COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
