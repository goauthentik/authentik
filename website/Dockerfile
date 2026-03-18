FROM --platform=${BUILDPLATFORM} docker.io/library/node:25.8.1-trixie@sha256:394048fb359d02efc485852ab638cac322a35af228c2cef83d23fc7dd01f4a36 AS docs-builder

ENV NODE_ENV=production

WORKDIR /work

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/package-lock.json,src=./package-lock.json \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    --mount=type=bind,target=/work/packages/tsconfig/,src=./packages/tsconfig/ \
    --mount=type=bind,target=/work/packages/eslint-config/,src=./packages/eslint-config/ \
    --mount=type=bind,target=/work/packages/prettier-config/,src=./packages/prettier-config/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    node ./scripts/node/setup-corepack.mjs --force && \
    corepack npm ci \
    node ./scripts/node/lint-runtime.mjs ./website

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/package-lock.json,src=./package-lock.json \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    --mount=type=bind,target=/work/packages/tsconfig/,src=./packages/tsconfig/ \
    --mount=type=bind,target=/work/packages/eslint-config/,src=./packages/eslint-config/ \
    --mount=type=bind,target=/work/packages/prettier-config/,src=./packages/prettier-config/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/package-lock.json,src=./website/package-lock.json \
    --mount=type=bind,target=/work/website/vendored/detect-package-manager,src=./website/vendored/detect-package-manager \
    --mount=type=bind,target=/work/website/docusaurus-theme/package.json,src=./website/docusaurus-theme/package.json \
    --mount=type=bind,target=/work/website/api/package.json,src=./website/api/package.json \
    --mount=type=bind,target=/work/website/integrations/package.json,src=./website/integrations/package.json \
    --mount=type=bind,target=/work/website/docs/package.json,src=./website/docs/package.json \
    --mount=type=cache,id=npm-website,sharing=shared,target=/root/.npm \
    corepack npm ci --workspaces --include-workspace-root --prefix ./website

WORKDIR /work/website

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./lifecycle/container/compose.yml /work/lifecycle/container/
COPY ./SECURITY.md /work/

RUN corepack npm run build -w docs

FROM docker.io/library/nginx:1.29-trixie@sha256:dec7a90bd0973b076832dc56933fe876bc014929e14b4ec49923951405370112

COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
