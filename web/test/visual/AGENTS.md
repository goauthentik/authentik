# Visual Comparisons

Capture screenshots from your working tree and compare them to the merge-base of a base branch (default: `origin/main`).

```bash
pnpm run test:visual                         # Storybook: every story, light + dark
pnpm run test:visual -- --base origin/foo    # Compare against another branch
pnpm run test:visual -- pages --record       # Record a running instance as HEAD's baseline
pnpm run test:visual -- -- --grep Drawer     # Pass arguments through to Playwright
pnpm exec playwright show-report .visual/report/storybook   # or .visual/report/pages
```

- **Nothing is committed.** Screenshots are stored in the git-ignored path `web/.visual/<commit>/<platform>-<arch>/<suite>/`. Each suite also writes a report to `web/.visual/report/<suite>/`.
- **Baselines are created on demand.** If no baseline exists at the merge-base, `scripts/visual.ts` checks out that commit in a temporary worktree, builds Storybook, and records a baseline using the _current_ specs. Any change in this directory triggers re-recording.
- **Storybook is strict; `pages` allows 1%** subpixel drift (`MaxDiffPixelRatio`). Prefer masking unstable regions instead of increasing the threshold.
- **Stories can opt out** with `tags: ["!test"]`. Any story that throws fails the run.
- **`pages` is only for screens without generated data** (for example: login, forms, wizards). Layouts that depend on e2e data are not stably maskable. `pages` baselines are not auto-built: record them on the base commit with `--record`.
