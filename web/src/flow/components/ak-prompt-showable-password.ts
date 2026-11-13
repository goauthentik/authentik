import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

/**
 * A configuration object for the visibility states of the password input.
 */
interface VisibilityProps {
    kind: "password" | "text";
    icon: string;
    label: () => string;
}

/**
 * Enum (sortof) for the visibility states of the password input. Labels are functions resolved at
 * run-time to make sure locale changes are picked up.
 */
const Visibility = {
    Reveal: {
        kind: "password",
        icon: "fa-eye",
        label: () => msg("View password", { id: "showable-password.show-password" }),
    },
    Mask: {
        kind: "text",
        icon: "fa-eye-slash",
        label: () => msg("Hide password", { id: "showable-password.hide-password" }),
    },
} as const satisfies Record<string, VisibilityProps>;

export const ShowablePasswordStyles = css`
    ak-prompt-showable-password {
        border-bottom-width: 0px !important;
        display: inline-block;
        width: 100%;
    }
    .ak-c-visible-password {
        display: grid;
        gap: 0;
        grid-template-columns: [input] 1fr [icon] 1.25em;
    }
    .ak-c-visible-password button {
        display: flex;
        justify-content: center;
        align-items: center;
    }
`;

@customElement("ak-prompt-showable-password")
export class ShowablePassword extends AKElement {
    @property({ type: String, attribute: "fieldid" })
    public fieldId!: string;

    @property({ type: String, attribute: "fieldkey" })
    public fieldKey!: string;

    @property({ type: String })
    public placeholder = "";

    @property({ type: Boolean })
    public required = false;

    @state()
    public passwordVisible = false;

    /* Light DOM */
    protected createRenderRoot() {
        return this;
    }

    willUpdate() {
        // Shouldn't happen in the field; this is a check that the developer got it right.
        if (!(this.fieldId && this.fieldKey)) {
            throw new Error("ShowablePassword field missing fieldId or fieldKey");
        }
    }

    render() {
        const { kind, label, icon } = this.passwordVisible ? Visibility.Mask : Visibility.Reveal;

        return html`<div class="ak-c-visible-password">
            <input
                type=${kind}
                id=${this.fieldId}
                name="${this.fieldKey}"
                placeholder="${this.placeholder}"
                autocomplete="new-password"
                class="pf-c-form-control"
                ?required=${this.required}
            /><button
                aria-label=${label()}
                @click=${() => {
                    this.passwordVisible = !this.passwordVisible;
                }}
                class="pf-c-button pf-m-plain"
                type="button"
            >
                <i class="ak-c-visible-password--icon fas ${icon}" aria-hidden="true"></i>
            </button>
        </div>`;
    }
}
