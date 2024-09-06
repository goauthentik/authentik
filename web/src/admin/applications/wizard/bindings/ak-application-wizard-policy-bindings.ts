import { PFSize } from "@goauthentik/common/enums.js";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-slug-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { WizardStep } from "@goauthentik/components/ak-wizard-main/AkWizardStep.js";
import { WizardNavigationEvent } from "@goauthentik/components/ak-wizard-main/events.js";
import { WizardButton } from "@goauthentik/components/ak-wizard-main/types";
import { Toolbar } from "@goauthentik/elements/ak-table/Toolbar.js";
import "@goauthentik/elements/ak-table/ak-select-table.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

// import { ifDefined } from "lit/directives/if-defined.js";
import BasePanel from "../BasePanel";

export class BindingTableStep implements WizardStep {
    id = "bindings";
    label = msg("Policy / User / Group Bindings");

    // Always valid; it's just a list of bindings
    valid = true;

    get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "submit" },
            { kind: "back", destination: "provider-details" },
            { kind: "cancel" },
        ];
    }

    render() {
        return html`<ak-application-wizard-policy-bindings
            .step=${this}
        ></ak-application-wizard-policy-bindings>`;
    }
}

const COLUMNS = [
    [msg("Order"), "order"],
    [msg("Binding")],
    [msg("Enabled"), "enabled"],
    [msg("Timeout"), "timeout"],
    [msg("Actions")],
];

@customElement("ak-application-wizard-policy-bindings-toolbar")
export class ApplicationWizardPolicyBindingsToolbar extends Toolbar {
    static get styles() {
        return [...Toolbar.styles, PFButton];
    }

    public override renderToolbar() {
        return html`<button
            slot="trigger"
            @click=${() => this.dispatchEvent(new WizardNavigationEvent("binding-form"))}
            class="pf-c-button pf-m-primary"
        >
            ${msg("Bind existing policy/group/user")}
        </button>`;
    }
}

@customElement("ak-application-wizard-policy-bindings")
export class ApplicationWizardPolicyBindings extends BasePanel {
    renderEmptyCollection() {
        return html` <ak-select-table
                multiple
                order="order"
                .columns=${COLUMNS}
                .content=${this.wizard.bindings}
            ></ak-select-table>
            <ak-empty-state header=${msg("No bound policies.")} icon="pf-icon-module">
                <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                <div slot="primary">
                    <button
                        @click=${() =>
                            this.dispatchEvent(new WizardNavigationEvent("binding-form"))}
                        class="pf-c-button pf-m-primary"
                    >
                        ${msg("Bind existing policy/group/user")}
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
                .content=${[]}
            ></ak-select-table> `;
    }

    render() {
        if (this.wizard.bindings.length === 0) {
            return this.renderEmptyCollection();
        }

        return this.renderCollection();
    }
}

export default ApplicationWizardPolicyBindings;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-policy-bindings": ApplicationWizardPolicyBindings;
    }
}
