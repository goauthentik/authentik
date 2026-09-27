# Third-party notices

This package is MIT licensed (see `LICENSE.txt`), but it redistributes font
files that are not. The bundled licenses are recorded in the package's SPDX
expression, `MIT AND OFL-1.1 AND CC-BY-4.0`.

Nothing here is modified. Every font file is byte-identical to the upstream it
came from.

## Red Hat Text, Red Hat Display, Red Hat Mono

Declared in `faces.css`; the six `RedHat*VF.woff2` files.

- Copyright 2021 The Red Hat Project Authors, <https://github.com/RedHatOfficial/RedHatFont>
- SIL Open Font License 1.1 — full text in `licenses/RedHat-OFL-1.1.txt`
- Reserved Font Name: none declared

## pficon

Declared in `icons.css`; `pficon.woff2` and `pficon.woff`.

- Copyright Red Hat, Inc.
- MIT — text in `licenses/PatternFly-MIT.txt`
- Taken from `@patternfly/patternfly@4.224.5`, which declares MIT in its
  `package.json` but ships no license file. The MIT text reproduced here is Red
  Hat's own, copied from the sibling `@patternfly/icons` package. The canonical
  text is at <https://github.com/patternfly/patternfly/blob/main/LICENSE>.

## Font Awesome 5 Free (Solid)

Declared in `icons.css`; `fa-solid-900.woff2` and `fa-solid-900.woff`.

- Copyright Fonticons, Inc., <https://fontawesome.com>
- Font files: SIL Open Font License 1.1. Reserved Font Name: "Font Awesome"
- The icons the fonts encode: CC BY 4.0, <https://creativecommons.org/licenses/by/4.0/>
- Full text in `licenses/FontAwesome-Free.txt`

Vendored through `@patternfly/patternfly@4.224.5`, which bundles the Solid
weight of Font Awesome 5 Free. The license text reproduced here is Font
Awesome Free's as published by Fonticons; note its copyright line tracks the
current release rather than the 5.x release these files are from. Font Awesome
Free's terms have been CC BY 4.0 for icons, SIL OFL 1.1 for fonts, and MIT for
code across both versions.

CC BY 4.0 requires attribution when the icons are displayed. This file, shipped
in the published package, carries it.
