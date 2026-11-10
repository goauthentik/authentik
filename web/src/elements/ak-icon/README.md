# ak-icon

A single-color icon drawn from a CSS catalog. Prototype of "option B" from the icon design review.

```html
<ak-icon name="status.success"></ak-icon> <ak-icon name="status.danger" label="Failed"></ak-icon>
```

The element is a CSS mask filled with `currentColor` and sized at `1em`, so the icon takes its color
and size from the surrounding text. There is nothing inside its shadow root.

## The catalog

`ak-icon.root.css` defines one CSS Custom Property per token: `name="status.success"` reads
`--ak-icon-status-success`. It is loaded document-wide through
`styles/if/authenticated/index.global.css`, and custom properties inherit through shadow roots, so
one definition reaches every component. An unknown token renders `--ak-icon-unknown`.

A brand replaces an icon in its custom CSS:

```css
:root {
    --ak-icon-status-success: url("https://example.com/icons/ok.svg");
}
```

Mask images are treated as images, so scripts in a hostile SVG never run. Cross-origin URLs need
CORS headers; `data:` URLs don't.

## Accessibility

Without `label`, the icon is decorative and `aria-hidden`. With `label`, it is exposed as
`role="img"` with that name. These are set as host attributes rather than through
`ElementInternals`, because Playwright's role queries (and so our tests) only read attributes.

## Not yet done

- The flow interface doesn't load `ak-icon.root.css` yet.
- No consumers have been migrated from `<i class="fa ...">`.
- `fa://` values in application and source icons still use the font.
