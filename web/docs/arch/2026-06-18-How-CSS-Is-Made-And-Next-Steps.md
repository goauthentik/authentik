# CSS Build Pipeline

- Date: 2026-06-18

This document describes how the CSS is built in our current system, and what we can do to make that
process less challenging and fraught with difficulties:

## styleLoaderPlugin (./bundler/style-loader-pluging/node.js)

All of our CSS is complied together by this ESBuild plug.

## ./scripts/build-web.mjs

Calls `ESBuild` internally, passes it the `styleLoaderPlugin` configuration, and the paths to three
*endpoint* files ending in `.global.css`. Each of these represents a single product that will be
loaded by Django into a document's global stylesheet.

This script is a top-level run via `npm run build`.

## The endpoint files:

- `interface.global.css`: The top-level stylesheet that is used by the User and Admin applications.
- `flows.global.css`: The top-level stylesheet that is used by the Flow application
- `static.global.css`: The top-level stylesheet used by a handful of Django static pages

Each endpoint file consists of a collection of imports and overrides.  `static` is not a huge
concern at the moment, but `interface` and `flows` matter:

## Interface load pattern:

The `interface.global.css` file is almost entirely imports:

1. @patternfly/patternfly/base/patternfly-common.css — PF reset + base element rules + utilities
2. @patternfly/.../patternfly-globals.css — the --pf-global--* custom properties at :root
3. @patternfly/.../patternfly-themes.css — dark-theme token reassignments
4. @patternfly/.../patternfly-fa-icons.css, patternfly-pf-icons.css — icon @font-face + classes
5. @patternfly/.../components/Spinner/spinner.css
6. #fonts/RedHat/faces.css — RedHat @font-face
7. ./base/fonts.css
8. ./base/variables.css, which in turn loads:
   - colors 
   - colors-dark 
   - spacers 
   - icons 
   - shadows 
   - z-indexes 
   - borders
   - miscellaneous overrides of Patternfly
   - --ak-*
   - --ak-v2-global-*
9. ./base/scrollbars.css
10. ./base/globals.css
11. ./base/common.css
12. ./base/placeholder.css
13. #styles/locales/{ja,ko,zh}/globals.css

## Flow load pattern:

The `flow.global.css` file duplicates (not imports!) the exact same files as `interface`, then adds:

14. #elements/ak-drawer/ak-drawer.root.css (after the base block)
15. @patternfly/.../components/BackgroundImage/background-image.css
16. #elements/locale/ak-locale-select.css — imported twice (flows.global.css:24-25)
17. #flow/FlowExecutor.css — which is also bundled into the shadow root via FlowExecutor.ts:11
19. A large block of inline rules: the --ak-c-login--* token system, the PF4 .pf-c-login overrides
    (with !important on container padding, flows.global.css:139-140), and the [name="flow-links"]
    grid.

## Layering (not with `@layers`):

We use the old-school mechanism of:

1. source order
2. selector specificity
3. `!important`. 

This is known to be fragile, and our discipline around it has not been fantastic, mostly because
we're trying to improve something that wasn't built with improvability at the design layer in mind.

## Solutions

Using layers to raise the specificity of CSS Custom Properties enables us to get away with a cleaner
and clearer idea of how our CSS is used:

### On the Document:

`@layer reset, legacy, theme, brand, components`:

- reset: A CSS Reset for the global document
- legacy: Patternfly 4's global CSS Custom Properties and assets such as fonts & icons
- theme: Inject Authentik's CSS Custom Properties for its design system here, overriding the P4 names
- brand: Inject any customer overrides of the global properties
- components: downstream Document-scoped look and feel for web components

### Inside a component:

`@layer reset, local`:

Only the inheritable resets are inherited! If you want `border-box` to work inside a component, you
need to say so explicitly!

## Action plan:

1. De-duplicate: The exact same code is cut-and-pasted into interface, static, global, and base!
   Let's move all that into its own file.
2. Write a top-level `document-layers.css` file that describes the layers we're going to use.
3. Vendor the Patternfly stuff that we're keeping.
4. Include our overrides.
5. Integrate the *design-system* `theme` branch into this, replacing the overrides.
6. Fix the way `brand` css is injected, so that it comes in the right place in the cascade. Note
   that as long as it has the `@layer brand;` declaration at the top, it actually doesn't matter
   **when** it's added to the global `adoptedStylesheet` collection; its specificity will allow its
   CSS Custom Properties to override those of the the layers that preceede in the
   `document-layers.css` declaration.
7. Continue the work of vendoring *Elements*
