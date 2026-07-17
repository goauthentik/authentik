# Tag must track the root package.json `packageManager` version. ${BUILDPLATFORM}
# keeps the binary's arch aligned with the builder stage on cross-arch builds.
FROM --platform=${BUILDPLATFORM} ghcr.io/pnpm/pnpm:11.13.0@sha256:cd8efe9bf47d8e4ea97c3fdc9a42650dc28619a11b486ade5d547fd2182eb98f AS pnpm

FROM --platform=${BUILDPLATFORM} docker.io/library/node:26.5.0-trixie@sha256:926d6cafec97f338577041890465522f70fe74aa6fe4b021a4fd7f87a5996b25 AS docs-builder

ENV NODE_ENV=production

WORKDIR /work

COPY --from=pnpm /opt/pnpm /opt/pnpm
ENV PATH="/opt/pnpm:${PATH}"

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/pnpm-lock.yaml,src=./website/pnpm-lock.yaml \
    node ./scripts/node/lint-runtime.mjs ./website

# Hoisted root install so `@goauthentik/docusaurus-config` resolves its own deps
# (e.g. `deepmerge-ts`) from /work/node_modules during the docs build; its source
# is bind-mounted read-only, so a per-package node_modules can't be written.
RUN --mount=type=bind,target=/work/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/pnpm-lock.yaml,src=./pnpm-lock.yaml \
    --mount=type=bind,target=/work/pnpm-workspace.yaml,src=./pnpm-workspace.yaml \
    --mount=type=bind,target=/work/packages/docusaurus-config/package.json,src=./packages/docusaurus-config/package.json \
    --mount=type=bind,target=/work/packages/esbuild-plugin-live-reload/package.json,src=./packages/esbuild-plugin-live-reload/package.json \
    --mount=type=bind,target=/work/packages/eslint-config/package.json,src=./packages/eslint-config/package.json \
    --mount=type=bind,target=/work/packages/logger-js/package.json,src=./packages/logger-js/package.json \
    --mount=type=bind,target=/work/packages/prettier-config/package.json,src=./packages/prettier-config/package.json \
    --mount=type=bind,target=/work/packages/tsconfig/package.json,src=./packages/tsconfig/package.json \
    --mount=type=bind,target=/work/lifecycle/aws/package.json,src=./lifecycle/aws/package.json \
    --mount=type=cache,id=pnpm-root,sharing=shared,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --config.node-linker=hoisted \
    --filter "@goauthentik/docusaurus-config"

RUN --mount=type=bind,target=/work/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/work/packages/docusaurus-config/,src=./packages/docusaurus-config/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/pnpm-lock.yaml,src=./website/pnpm-lock.yaml \
    --mount=type=bind,target=/work/website/pnpm-workspace.yaml,src=./website/pnpm-workspace.yaml \
    --mount=type=bind,target=/work/website/vendored/detect-package-manager,src=./website/vendored/detect-package-manager \
    --mount=type=bind,target=/work/website/docusaurus-theme/package.json,src=./website/docusaurus-theme/package.json \
    --mount=type=bind,target=/work/website/api/package.json,src=./website/api/package.json \
    --mount=type=bind,target=/work/website/integrations/package.json,src=./website/integrations/package.json \
    --mount=type=bind,target=/work/website/docs/package.json,src=./website/docs/package.json \
    --mount=type=cache,id=pnpm-website,sharing=shared,target=/root/.local/share/pnpm/store \
    pnpm --dir website install --frozen-lockfile

WORKDIR /work/website

COPY ./website /work/website/
COPY ./blueprints /work/blueprints/
COPY ./schema.yml /work/
COPY ./lifecycle/container/compose.yml /work/lifecycle/container/
COPY ./SECURITY.md /work/

RUN  --mount=type=bind,target=/work/packages/docusaurus-config/,src=./packages/docusaurus-config/ \
    pnpm run build

FROM docker.io/library/nginx:1.31.2-trixie@sha256:b5a9a3cfc86b81dd6f1458d53f2ad2b559cc255653d2efd6cacee5636bf2066f
LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="authentik product documentation" \
    org.opencontainers.image.documentation="https://docs.goauthentik.io" \
    org.opencontainers.image.licenses="https://github.com/goauthentik/authentik/blob/main/LICENSE" \
    org.opencontainers.image.title="authentik docs image" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc."


COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
