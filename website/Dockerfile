# Tag must track the root package.json `packageManager` version. ${BUILDPLATFORM}
# keeps the binary's arch aligned with the builder stage on cross-arch builds.
FROM --platform=${BUILDPLATFORM} ghcr.io/pnpm/pnpm:12.4.0@sha256:4fcb6db39468ecafef34f3e866730df106f7639ba4512e42885d80f868ccb257 AS pnpm

FROM --platform=${BUILDPLATFORM} docker.io/library/node:26.8.2-trixie@sha256:fb192b8ad31841aadc4bb79c44ae0f59d193a798ffbc9fdce37ba6ecb20c2236 AS docs-builder

ENV NODE_ENV=production

WORKDIR /work

COPY --from=pnpm /opt/pnpm /opt/pnpm
ENV PATH="/opt/pnpm:${PATH}"

RUN --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/scripts/node/,src=./scripts/node/ \
    --mount=type=bind,target=/work/packages/logger-js/,src=./packages/logger-js/ \
    --mount=type=bind,target=/work/website/package.json,src=./website/package.json \
    --mount=type=bind,target=/work/website/pnpm-lock.yaml,src=./website/pnpm-lock.yaml \
    node ./scripts/node/lint-runtime.ts ./website

# Hoisted root install so `@goauthentik/docusaurus-config` resolves its own deps
# (e.g. `deepmerge-ts`) during the docs build. Its source and `@goauthentik/fonts`
# are copied rather than bind-mounted, so pnpm can write the per-package
# node_modules it places workspace links in.
COPY ./packages/docusaurus-config /work/packages/docusaurus-config/
COPY ./packages/fonts /work/packages/fonts/

RUN --mount=type=bind,target=/work/.npmrc,src=./.npmrc \
    --mount=type=bind,target=/work/package.json,src=./package.json \
    --mount=type=bind,target=/work/pnpm-lock.yaml,src=./pnpm-lock.yaml \
    --mount=type=bind,target=/work/pnpm-workspace.yaml,src=./pnpm-workspace.yaml \
    --mount=type=bind,target=/work/packages/esbuild-plugin-live-reload/package.json,src=./packages/esbuild-plugin-live-reload/package.json \
    --mount=type=bind,target=/work/packages/oxlint-config/package.json,src=./packages/oxlint-config/package.json \
    --mount=type=bind,target=/work/packages/logger-js/package.json,src=./packages/logger-js/package.json \
    --mount=type=bind,target=/work/packages/oxfmt-config/package.json,src=./packages/oxfmt-config/package.json \
    --mount=type=bind,target=/work/packages/tsconfig/package.json,src=./packages/tsconfig/package.json \
    --mount=type=bind,target=/work/lifecycle/aws/package.json,src=./lifecycle/aws/package.json \
    --mount=type=cache,id=pnpm-root,sharing=shared,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --config.node-linker=hoisted \
    --filter "@goauthentik/docusaurus-config"

RUN --mount=type=bind,target=/work/.npmrc,src=./.npmrc \
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

RUN pnpm run build

FROM docker.io/library/nginx:1.31.6-trixie@sha256:908dc23e643a1447dbfb2e189ed268bfde6a51a5bf9a34d3dd3440a24f58ccf7
LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="authentik product documentation" \
    org.opencontainers.image.documentation="https://docs.goauthentik.io" \
    org.opencontainers.image.licenses="https://github.com/goauthentik/authentik/blob/main/LICENSE" \
    org.opencontainers.image.title="authentik docs image" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc."


COPY --from=docs-builder /work/website/docs/build /usr/share/nginx/html
