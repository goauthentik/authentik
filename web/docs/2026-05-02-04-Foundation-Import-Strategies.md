# 01 Foundations: Import Strategies

Date: 2026-05-02 (May 2st, 2026)

## Import Strategies

`package.json` defines a large number of import paths that reach into the `src` folder. We use
NodeJS subpaths prefixed with `#`, such as `#fonts`, `#elements`, or `#flow` to isolate subsections
of the frontend. This strategy is intended to facilitate directory restructuring without having to
do mass search-and-replace ops, and as a precursor to further mono-repo-ifying the codebase.

We recommend using barrel files only to export the intended API of a defined subsection.
