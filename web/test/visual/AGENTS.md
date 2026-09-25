# Visual Comparisons

Screenshots of the working tree, compared against the merge-base with a base branch (default `origin/main`).

```bash
pnpm run test:visual                         # Storybook: every story, light + dark
pnpm run test:visual -- --base origin/foo    # Compare against another branch
pnpm run test:visual -- pages --record       # Record a running instance as HEAD's baseline
pnpm run test:visual -- -- --grep Drawer     # Pass arguments through to Playwright
pnpm exec playwright show-report .visual/report
```

- **Nothing is committed.** Screenshots live in the git-ignored `web/.visual/<commit>/<platform>-<arch>/<suite>/`.
- **Baselines are built on demand.** If the merge-base has none, `scripts/visual.ts` checks it out into a temporary worktree, builds its Storybook, and records it with the _current_ specs. Changing anything in this directory re-records.
- **Storybook is exact; `pages` allows 1%** for subpixel drift (`MaxDiffPixelRatio`). Mask regions that vary rather than raising it.
- **Stories opt out** with `tags: ["!test"]`. A story that throws fails the run.
- **`pages` only covers screens without generated data** (login, forms, wizards). Layout that depends on e2e data can't be masked stable. Its baseline can't be built automatically: record it on the base commit with `--record`.
