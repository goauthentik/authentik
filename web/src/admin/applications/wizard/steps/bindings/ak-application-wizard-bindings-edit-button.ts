import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-application-wizard-binding-step-edit-button")
export class ApplicationWizardBindingStepEditButton extends AKElement {
    public static override styles = [PFButton];

    @property({ type: Number })
    public value = -1;

    #clickListener = (ev: Event) => {
        ev.stopPropagation();
        this.dispatchEvent(
            new CustomEvent<number>("click-edit", {
                bubbles: true,
                composed: true,
                detail: this.value,
            }),
        );
    };

    public override render() {
        return html`<button class="pf-c-button pf-c-secondary" @click=${this.#clickListener}>
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
