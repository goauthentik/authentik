import { css, LitElement, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

/** Token names are dotted kebab-case, e.g. `status.success` or `action.close`. */
const TOKEN_PATTERN = /^[a-z0-9]+(?:[.-][a-z0-9]+)*$/;

/**
 * The icon is a CSS mask filled with `currentColor` and sized at `1em`, so it takes its color and
 * size from the surrounding text. The `name` token selects the CSS Custom Property
 * `--ak-icon-<name>`, with dots replaced by dashes. See `ak-icon.root.css` for the catalog. An
 * unknown or invalid name renders `--ak-icon-unknown`.
 * Without a `label` the icon is decorative and hidden from assistive technology. With a `label`
 * it is exposed as an image with that accessible name.
 *
 * @element ak-icon
 *
 * @summary A single-color icon drawn from the CSS icon catalog.
 *
 * @attr {string} name - Icon token, e.g. "status.success"
 * @attr {string} label - Accessible name; omit for decorative icons
 */
export class Icon extends LitElement {
    static override readonly styles = css`
        :host {
            display: inline-block;
            flex-shrink: 0;
            width: 1em;
            height: 1em;
            vertical-align: -0.125em;
            background-color: currentColor;
            mask: var(--ak-icon-image, var(--ak-icon-unknown)) center / contain no-repeat;
        }

        @media (forced-colors: active) {
            :host {
                background-color: CanvasText;
            }
        }
    `;

    @property({ reflect: true })
    public name?: string;

    @property()
    public label?: string;

    public override willUpdate(changed: PropertyValues<this>) {
        if (changed.has("name")) {
            if (this.name && TOKEN_PATTERN.test(this.name)) {
                const token = this.name.replaceAll(".", "-");
                this.style.setProperty("--ak-icon-image", `var(--ak-icon-${token})`);
            } else {
                // Clear it, or an invalid value would leave the previous icon showing.
                this.style.removeProperty("--ak-icon-image");
            }
        }

        // An unset label is never "changed", so the first update must apply the decorative default.
        if (changed.has("label") || !this.hasUpdated) {
            if (this.label) {
                this.setAttribute("role", "img");
                this.setAttribute("aria-label", this.label);
                this.removeAttribute("aria-hidden");
            } else {
                this.removeAttribute("role");
                this.removeAttribute("aria-label");
                this.setAttribute("aria-hidden", "true");
            }
        }
    }

    // The host element is the icon; there is nothing to render inside it.
    protected override render() {
        return null;
    }
}
