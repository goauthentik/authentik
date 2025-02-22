import { LitElement, html } from "lit";
import { customElement } from "lit/decorators.js";

import { globalVariables } from "../components/styles.css";

/**
 * @element sb-dual-select-host-provider
 *
 * A *very simple* wrapper which provides the CSS Custom Properties used by the components when
 * being displayed in Storybook or Vite. Not needed for the parent widget since it provides these by itself.
 */

@customElement("sb-dual-select-host-provider")
export class SbHostProvider extends LitElement {
    static get styles() {
        return globalVariables;
    }

    render() {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "sb-dual-select-host-provider": SbHostProvider;
    }
}
