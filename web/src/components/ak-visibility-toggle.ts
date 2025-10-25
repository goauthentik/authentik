import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface VisibilityToggleProps {
    open: boolean;
    disabled: boolean;
    showMessage: string;
    hideMessage: string;
}

/**
 * @component ak-visibility-toggle
 * @class VisibilityToggle
 *
 * A straightforward two-state iconic button we use in a few places as way of telling users to hide
 * or show something secret, such as a password or private key. Expects the client to manage its
 * state.
 *
 * @events
 * - click: when the toggle is clicked.
 */
@customElement("ak-visibility-toggle")
export class VisibilityToggle extends AKElement implements VisibilityToggleProps {
    static styles = [PFBase, PFButton];

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    open = false;

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    disabled = false;

    /**
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "show-message" })
    showMessage = msg("Show field content");

    /**
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "hide-message" })
    hideMessage = msg("Hide field content");

    render() {
        const [label, icon] = this.open
            ? [this.hideMessage, "fa-eye"]
            : [this.showMessage, "fa-eye-slash"];

        const onClick = (ev: PointerEvent) => {
            ev.stopPropagation();
            this.dispatchEvent(new PointerEvent(ev.type, ev));
        };

        return html`<button
            aria-label=${label}
            title=${label}
            @click=${onClick}
            ?disabled=${this.disabled}
            class="pf-c-button pf-m-control"
            type="button"
        >
            <i class="fas ${icon}" aria-hidden="true"></i>
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-visibility-toggle": VisibilityToggle;
    }
}
