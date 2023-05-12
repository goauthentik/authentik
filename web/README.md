# The Authentk.io Front-End

# Project Layout:

- authentik/: Graphic Assets related to services
- icons/: Application-specific graphic assets
- src/: The application source
- lingui.config.js: Lingui[^1] is an internationalization tool, using po/gettext format
- rollup.config.js: This project uses rollup. That makes it an excellent target for vite.
- tsconfig.js: Looks straightforward, although it does have paths, which means ts-alias will be
  needed.

---
[^1] [Lingui](https://lingui.dev/)

