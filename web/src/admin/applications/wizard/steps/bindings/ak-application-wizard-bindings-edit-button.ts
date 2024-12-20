import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-application-wizard-binding-step-edit-button")
export class ApplicationWizardBindingStepEditButton extends AKElement {
    static get styles() {
        return [PFButton];
    }

    @property({ type: Number })
    value = -1;

    @bound
    onClick(ev: Event) {
        ev.stopPropagation();
        this.dispatchEvent(
            new CustomEvent<number>("click-edit", {
                bubbles: true,
                composed: true,
                detail: this.value,
            }),
        );
    }

    render() {
        return html`<button class="pf-c-button pf-c-secondary" @click=${this.onClick}>
            ${msg("Edit")}
        </button>`;
    }
}

export function makeEditButton(
    label: string,
    value: number,
    handler: (_: CustomEvent<number>) => void,
) {
    return html`<ak-application-wizard-binding-step-edit-button
        class="pf-c-button pf-m-secondary"
        .value=${value}
        @click-edit=${handler}
    >
        ${label}
    </ak-application-wizard-binding-step-edit-button>`;
}
