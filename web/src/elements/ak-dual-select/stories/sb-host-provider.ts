import { globalVariables } from "../components/styles.js";

import { html, LitElement } from "lit";
import { customElement } from "lit/decorators.js";

/**
 * @element sb-dual-select-host-provider
 *
 * A *very simple* wrapper which provides the CSS Custom Properties used by the components when
 * being displayed in Storybook or Vite. Not needed for the parent widget since it provides these by itself.
 */

@customElement("sb-dual-select-host-provider")
export class SbHostProvider extends LitElement {
    static styles = globalVariables;

    render() {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "sb-dual-select-host-provider": SbHostProvider;
    }
}
