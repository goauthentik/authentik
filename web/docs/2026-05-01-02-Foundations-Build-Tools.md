# 02 Foundations: Build Tools

Date: 2026-05-01 (May 1st, 2026)

## Esbuild and TSGo

In 2024, the web UI used Rollup and TSC as its primary build tools. Building the entire UI for
release took as many as three minutes.

ESBuild can both produce running Javascript from Typescript, and perform all of the bundling
required to support the authentik WebUI. Switching to ESBuild reduced build time to 5 _seconds_. TSC
has been relegated to the `no-emit` strategy of type-checking but not code-producing.

One complication in our code is that our web component foundation, Lit, has an awkward
CSS-in-Javascript format incompatible with the build tools intended to support React, and the
ESBuild plug-in to handle it is custom.

As of this writing, Typescript 7.0, aka "TSGo," is currently in beta. When it is released, we expect
to both reassess this strategy and examine alternative build strategies. We prefer to hew as close
to the Typescript standard as possible, and the standard is set by the Typescript team.

## Wireit

We have chosen to use Wireit because it provides a finer degree of control over build order and
provides a caching strategy. This significantly speeds up rebuilding during development versus using
NPM's own builds. Use Wireit _only_ when you need the cache or dependency order to be strict; for
baseline builds, prefer writing directly into the `scripts` section of `package.json`.
