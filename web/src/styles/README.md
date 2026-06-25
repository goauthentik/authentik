# `web/src/styles` — The Authentik Design System

The Authentik front-ends design system started with and currently rests on the [Patternfly 4 CSS
Library](https://v4-archive.patternfly.org/v4/).

This folder contains:

- entrypoints and contents for the Authentik front-end's applications and utilities: Flow
  (`flow.global.css`), User/Admin (`interface.global.css`), and the static CSS built for Django
  templates that are not supporting applications (`static.global.css`).
- Overrides for various components where we apply our own design sensibilities to Patternfly
  components.

The file `layers.css` is the top of every entrypoint; it describes the layers we use and the roles
each layer plays in our CSS specificity chain.

The goal of this hierarchy is to make it obvious by path:

- **who** loads it: which bundle it belongs to
- **where** it's used: at the top-level `document`, or in a shadowDOM component
- **layer**: enforced _only and ever_ in an entrypoint file.
- **role**: reset, token, layout, or theme

---

## Note

This is an *intermediate* step.  Our ultimate goals are:

- Provide *our* theme via a separate package.
- Move as much of a component's hard definitions into a CSS file in the same folder as the component
  itself.
- Vendor the CSS we actually use into our components.
- Provide mechanisms to make brand customization as easy and straightforward as possible
- Provide live previews of (token-level) brand customization in the product

To the best extent possible, try not do anything that thwarts these goals.

---

## Bundling The Top-Level CSS

Our CSS is bundled in two different ways: as a top-level CSS document imported into the
`document:root` via the server templates, and compiled into CSSResult objects consumed by web
components for the shadowDOM.

The three files in the current folder marked `.global.css` are the entrypoints for those top-level
CSS documents: they contain the imports and layer declarations for all the CSS resources complied
into the document CSS. These files are matched by declarations in `./web/paths/node.js`, which
describes to the compiler which files to use as entrypoints. The `.global.css` extension is
*required* to trigger the correct referencing behavior in the bundler.

These files are organizational: they should have *only* `@import` statements pointing to other
CSS files.


-  Entry (source)         Output                    Consumers

- `interface.global.css` `dist/styles/interface-*` Admin + User
- `flows.global.css`     `dist/styles/flow-*`      Flow
- `static.global.css`    `dist/styles/static-*`    Django static templates


### The fourth pipeline: shadow scope

Every major web component in our system inherts from our LitElement base component,
`web/src/elements/Base.ts:AKElement`. The base element always adopts two sheets into the shadowroot
of *every* `AKElement`:

- `shadow/patternfly-base.css` (`$PFBase`)
- `shadow/authentik-base.css` (`$AKBase`)

CSS Custom Properties defined in a parent element (native or custom) crosses the shadow boundary and
affects the look and feel of child elements that consume those properties. The `@layer` directive
controls only the specificity of the property declarations at the `document` level; the CSS Custom
Property with the highest specifity when it his the element boundary wins.

---

## Scope: `global/` vs `shadow/`

```
web/src/styles/
  layers.css            # Out @layer order statement — imported first by every entrypoint file
  README.md             # You're reading it!

  interface.global.css  # entrypoint: Admin + User
  flows.global.css      # entrypoint: Flow
  static.global.css     # entrypoint: Django templates

  global/               # Defines the design system for the document
    vendor/             # layer(vendor)  vendored PatternFly — override in `theme` or `components`
      patternfly.css    #   barrel file of stuff we pull from Patternfly
      assets/           #   fonts / icon webfonts used by the Patternfly CSS
    reset/              # layer(reset)   top-level normalization
    theme/              # layer(theme)   Authentik's default design tokens as CSS Custom Properties
    mode/               # layer(mode)    light/dark/contrast/motion overrides
    locales/            # per-locale (ja/ko/zh) document overrides for ideographic languages
    brand/              # layer(brand)   Reserved layer for injecting brand CSS Custom Properties via the server

  shadow/               # definitions used by all web components' shadowroots
    patternfly-base.css #   $PFBase
    authentik-base.css  #   $AKBase

  authentik/            # component CSS
    components/<Name>/  #   Per-component overrides or new, unique components
    login.css           #   login-screen layout + token bridges
  atom/                 # CodeMirror CSS stuff (imported into the CodeMirror component)
```

Note: quite a number of components have embedded CSS of their own (via Lit's `css()` function) or
have a companion file with the CSS bundled automatically and independently of the scheme described
here.  Figuring out why some component CSS is specified *here* rather than with the component is 
a TODO item.

---

## Layers: what each one is for

Declared in `layers.css`, lowest specificity first:

```css
@layer reset, vendor, components, theme, mode, brand;
```

- `reset`: The CSS reset. Currently not much used; most of the CSS reset is mashed into Patternfly
- `vendor` PatternFly. Import as `… layer(vendor)`. Frozen; do not hand-edit.
- `components` Document-scope component rules and the `root{}` blocks that bridge global tokens to
  each component's internal custom properties.
- `theme` The product's default design tokens — CSS Custom Property definitions only, please.
- `mode` Overrides of `theme` for accessibility light/dark, high-contrast, reduced motion.
- `brand` Per-deployment overrides of theme/component tokens. Highest specificity.
  - Database brand overrides: CSS Custom Properties only
  - Path to a custom CSS file: Lets advanced designers use `::part` to do whatever the heck they
    want.

One thing that took forever to understand: Layers are about *selectors*, not *properties*. A CSS
Custom Property with the same property name declared in different selectors (say, `:root` vs
`.some-inner-value`) at the top-level but in different layers may not have the specificity you want.
Continue to be disciplined with specifying CSS Custom Properties in "dictionary" containers: use
`:root` in different layers to ensure they all get the same specificity. As stated earlier: once
they hit the shadow boundary, the CSS Custom Property with the highest specificity *at that moment*
wins.

On the other hand, *import order* only matters within the same layer. Otherwise, later layers always
imbue their selectors with higher specificity over earlier ones.

---

## What is where

What you want to change, and where you can find it:

- The login card's width / padding: `authentik/login.css` (`--ak-c-login--MaxWidth`, ...)
- A default color / spacing / font token: `global/theme/colors.css`, `spacers.css`, `fonts.css`
- Dark-mode color values: `global/mode/mode.css` <sup>1</sup>
- Light/dark/contrast/motion _behavior_: `global/mode/mode.css`, `global/mode/contrast.css` <sup>2</sup>
- Table striping / a component's look: `authentik/components/<Name>/<name>.css`
- Which PatternFly pieces are bundled into the document: `global/vendor/patternfly.css` (the barrel)
- Which sheets every component gets in its shadow: `shadow/patternfly-base.css`, `shadow/authentik-base.css`
- The set of files in a bundle: the matching `*.global.css` entry
- Cascade-layer order: `layers.css` (the only place)
- The code editor's color theme: `atom/one-dark.css`

---

## Component overrides and adjustments

`authentik/components/<Name>/<name>.css` contains definitions for CSS components that appear in
multiple places in our code: both as top-level definitions for static pages, and for some shadowroot
components. Most of them are overrides to the Patternfly settings to establish our own preferred
design or to compensate for the fact that Patternfly is not very friendly to shadowroots.


- Components have their own dark-mode settings, influenced by setting the `dark` tag (and/or
  `high-contrast`, and/or `reduced-motion`).
  - TODO: Make these *rare*.  Ideally, components should get all their dark-mode settings via
    CSS custom properties.  For the time being, when deciding if CSS should go into `mode` or 
    into a component, if it is component-specific, it belongs in the *component*.
    
---

TODO: Figure out why `mode.css` has `:host` rules, and what they enable.  I couldn't figure out why
they were there; they didn't seem to be imported by anything.

TODO: Figure out what to do with `reset/scrollbars.css`.  It's kinda a reset-- it specifies a
specific look for the scrollbar that, in the original design, was even before the theme was 
being set the old-fashioned way, via the cascade, and it was placed with the "reset" code
blocks.

TODO: Find a better home for `patternfly/constants.ts`. 

TODO: What the heck is `authentik/login.css` doing?

TODO: Move `atom` closer to the component.

