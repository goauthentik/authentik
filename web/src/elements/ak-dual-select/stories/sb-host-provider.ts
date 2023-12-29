import { html, LitElement } from "lit";
import { globalVariables } from "../components/styles.css";
import { customElement } from "lit/decorators.js";

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
