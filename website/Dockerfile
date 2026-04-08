FROM --platform=${BUILDPLATFORM} docker.io/library/node:25.9.0-trixie@sha256:f57f0c76da32cc5ea0d50d209cc53fa37fb69954cf61407ec38e8f8591373fdf AS docs-builder

ENV NODE_ENV=production

WORKDIR /work

# TODO: Use setup-corepack.mjs
RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/package-lock.json,src=./package-lock.json \
    npm install --force -g corepack@latest && \
    corepack install -g npm@11.11.0+sha512.f36811c4aae1fde639527368ae44c571d050006a608d67a191f195a801a52637a312d259186254aa3a3799b05335b7390539cf28656d18f0591a1125ba35f973 && \
    corepack enable

WORKDIR /work/website

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/package-lock.json,src=./package-lock.json \
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
    corepack npm ci --workspaces --include-workspace-root

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./lifecycle/container/compose.yml /work/lifecycle/container/
COPY ./SECURITY.md /work/

RUN corepack npm run build

FROM docker.io/library/nginx:1.29-trixie@sha256:e2e661b80dbd37ae1e1562ad0d3050ea8273ffef2da096b97ba0428be20100e8

COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
