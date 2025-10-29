FROM --platform=${BUILDPLATFORM} docker.io/library/node:25-trixie-slim@sha256:03270bd4f57818948e681a7fbdc1e08ae177490e406f31b10976c32da2b52d69 AS docs-builder

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

FROM docker.io/library/nginx:1.29-trixie@sha256:b619c34a163ac12f68c1982568a122c4953dbf3126b8dbf0cc2f6fdbfd85de27

COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
