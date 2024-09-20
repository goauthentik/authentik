import { ApplicationWizardStep } from "@goauthentik/admin/applications/wizard/ApplicationWizardStep.js";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-slug-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { type WizardButton } from "@goauthentik/components/ak-wizard/types";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

const COLUMNS = [
    [msg("Order"), "order"],
    [msg("Binding")],
    [msg("Enabled"), "enabled"],
    [msg("Timeout"), "timeout"],
    [msg("Actions")],
];

@customElement("ak-application-wizard-bindings-step")
export class ApplicationWizardBindingsStep extends ApplicationWizardStep {
    label = msg("Configure Bindings");

    get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "submit" },
            { kind: "back", destination: "provider" },
            { kind: "cancel" },
        ];
    }

    // TODO Fix those dispatches so that we handle them here, in this component, and *choose* how to
    // forward them.
    onBindingEvent(binding?: number) {
        this.handleUpdate({ currentBinding: binding ?? -1 }, "edit-binding", {
            enable: "edit-binding",
        });
    }

    renderEmptyCollection() {
        return html` <ak-select-table
                multiple
                order="order"
                .columns=${COLUMNS}
                .content=${[]}
            ></ak-select-table>
            <ak-empty-state header=${msg("No bound policies.")} icon="pf-icon-module">
                <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                <div slot="primary">
                    <button @click=${() => this.onBindingEvent()} class="pf-c-button pf-m-primary">
                        ${msg("Bind policy/group/user")}
                    </button>
                </div>
            </ak-empty-state>`;
    }

    renderCollection() {
        return html`<ak-application-wizard-policy-bindings-toolbar></ak-application-wizard-policy-bindings-toolbar>
            <ak-select-table
                multiple
                order="order"
                .columns=${COLUMNS}
                .content=${this.wizard.bindings}
            ></ak-select-table>
            <div slot="primary">
                <button @click=${() => this.onBindingEvent()} class="pf-c-button pf-m-primary">
                    ${msg("Bind policy/group/user")}
                </button>
            </div> `;
    }

    renderMain() {
        if ((this.wizard.bindings ?? []).length === 0) {
            return this.renderEmptyCollection();
        }
        return this.renderCollection();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-applications-step": ApplicationWizardBindingsStep;
    }
}
