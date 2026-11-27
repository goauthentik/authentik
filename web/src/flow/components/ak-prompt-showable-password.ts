import { MessageFormatter } from "#common/ui/locale/format";

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
    label: MessageFormatter<string>;
}

/**
 * Enum (sortof) for the visibility states of the password input. Labels are functions resolved at
 * run-time to make sure locale changes are picked up.
 */
const Visibility = {
    Reveal: {
        kind: "password",
        icon: "fa-eye-slash",
        label: () => msg("View password", { id: "showable-password.show-password" }),
    },
    Mask: {
        kind: "text",
        icon: "fa-eye",
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

/**
 * @element ShowablePassword
 *
 * @summary A password field with "showable" options, specifically made to interact with the
 * PromptStage.
 */

@customElement("ak-prompt-showable-password")
export class ShowablePassword extends AKElement {
    @property({ type: String, attribute: "fieldid" })
    public fieldId: string | null = null;

    @property({ type: String, attribute: "fieldkey" })
    public fieldKey: string | null = null;

    @property({ type: String })
    public placeholder = "";

    @property({ type: Boolean })
    public required = false;

    @state()
    public revealed = false;

    /* Light DOM */
    protected createRenderRoot() {
        return this;
    }

    get fieldKeys() {
        // Shouldn't happen in the field; this is a check that the developer got it right.
        if (!this.fieldId) {
            throw new Error("ShowablePassword field missing `fieldId`");
        }

        if (!this.fieldKey) {
            throw new Error("ShowablePassword field missing `fieldKey`");
        }

        return { id: this.fieldId, key: this.fieldKey };
    }

    render() {
        const { kind, label, icon } = this.revealed ? Visibility.Mask : Visibility.Reveal;
        const { placeholder, required } = this;
        const { id, key } = this.fieldKeys;

        const onClick = () => {
            this.revealed = !this.revealed;
        };

        return html`<div class="ak-c-visible-password">
            <input
                type=${kind}
                id=${id}
                name="${key}"
                placeholder="${placeholder}"
                autocomplete="new-password"
                class="pf-c-form-control"
                ?required=${required}
            /><button
                aria-label=${label()}
                @click=${onClick}
                class="pf-c-button pf-m-plain"
                type="button"
            >
                <i class="ak-c-visible-password--icon fas ${icon}" aria-hidden="true"></i>
            </button>
        </div>`;
    }
}
