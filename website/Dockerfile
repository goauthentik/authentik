FROM --platform=${BUILDPLATFORM} docker.io/library/node:26.3.1-trixie@sha256:15797fbed0f20a0c17c6f00e42b8ebe1574971f986fd8ae15be77acf8c30e185 AS docs-builder

ENV NODE_ENV=production

WORKDIR /work

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/package-lock.json,src=./package-lock.json \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    --mount=type=bind,target=/work/packages/tsconfig/,src=./packages/tsconfig/ \
    --mount=type=bind,target=/work/packages/eslint-config/,src=./packages/eslint-config/ \
    --mount=type=bind,target=/work/packages/prettier-config/,src=./packages/prettier-config/ \
    --mount=type=bind,target=/work/packages/docusaurus-config/,src=./packages/docusaurus-config/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    node ./scripts/node/setup-corepack.mjs --force && \
    node ./scripts/node/lint-runtime.mjs ./website

RUN --mount=type=bind,target=/work/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/package-lock.json,src=./package-lock.json \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    --mount=type=bind,target=/work/packages/tsconfig/,src=./packages/tsconfig/ \
    --mount=type=bind,target=/work/packages/eslint-config/,src=./packages/eslint-config/ \
    --mount=type=bind,target=/work/packages/prettier-config/,src=./packages/prettier-config/ \
    --mount=type=bind,target=/work/packages/docusaurus-config/,src=./packages/docusaurus-config/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=bind,target=/work/website/vendored/detect-package-manager,src=./website/vendored/detect-package-manager \
    --mount=type=bind,target=/work/website/docusaurus-theme/package.json,src=./website/docusaurus-theme/package.json \
    --mount=type=bind,target=/work/website/api/package.json,src=./website/api/package.json \
    --mount=type=bind,target=/work/website/integrations/package.json,src=./website/integrations/package.json \
    --mount=type=bind,target=/work/website/docs/package.json,src=./website/docs/package.json \
    --mount=type=cache,id=npm-website,sharing=shared,target=/root/.npm \
    corepack npm ci && \
    corepack npm ci --workspaces --include-workspace-root --prefix ./website

WORKDIR /work/website

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./lifecycle/container/compose.yml /work/lifecycle/container/
COPY ./SECURITY.md /work/

RUN  --mount=type=bind,target=/work/packages/docusaurus-config/,src=./packages/docusaurus-config/ \
    corepack npm run build -w docs

FROM docker.io/library/nginx:1.31.2-trixie@sha256:ec4ed8b5299e5e90694af7750eb6dffd2627317d30544d056b0371f8082f7bce
LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="authentik product documentation" \
    org.opencontainers.image.documentation="https://docs.goauthentik.io" \
    org.opencontainers.image.licenses="https://github.com/goauthentik/authentik/blob/main/LICENSE" \
    org.opencontainers.image.title="authentik docs image" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc."


COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
