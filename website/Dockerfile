FROM --platform=${BUILDPLATFORM} docker.io/library/node:25.6.0-trixie@sha256:3b6ef8bf8ea0d849a07b3a24b0f64f25381ba2c9abb8825bc424e92a87b5e797 AS docs-builder

ENV NODE_ENV=production

WORKDIR /work/website

RUN --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=bind,target=/work/website/vendored/detect-package-manager,src=./website/vendored/detect-package-manager \
    --mount=type=bind,target=/work/website/docusaurus-theme/package.json,src=./website/docusaurus-theme/package.json \
    --mount=type=bind,target=/work/website/api/package.json,src=./website/api/package.json \
    --mount=type=bind,target=/work/website/integrations/package.json,src=./website/integrations/package.json \
    --mount=type=bind,target=/work/website/docs/package.json,src=./website/docs/package.json \
    --mount=type=cache,id=npm-website,sharing=shared,target=/root/.npm \
    npm ci --workspaces --include-workspace-root

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./lifecycle/container/compose.yml /work/lifecycle/container/
COPY ./SECURITY.md /work/

RUN npm run build

FROM docker.io/library/nginx:1.29-trixie@sha256:7fe5dda25bce8a7753f15e9800a6e894b87e9fd3013d3c40d2332575854bc9d0

COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
