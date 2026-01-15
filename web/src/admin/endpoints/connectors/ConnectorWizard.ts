import "#admin/common/ak-license-notice";
import "#admin/endpoints/connectors/agent/AgentConnectorForm";
import "#admin/endpoints/connectors/fleet/FleetConnectorForm";
import "#elements/forms/ProxyForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";
import { Wizard } from "#elements/wizard/Wizard";

import { EndpointsApi, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, html, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-endpoint-connector-wizard")
export class EndpointConnectorWizard extends AKElement {
    static styles: CSSResult[] = [PFBase, PFButton];

    @property()
    createText = msg("Create");

    @property({ attribute: false })
    connectorTypes: TypeCreate[] = [];

    @query("ak-wizard")
    wizard?: Wizard;

    firstUpdated(): void {
        new EndpointsApi(DEFAULT_CONFIG).endpointsConnectorsTypesList().then((types) => {
            this.connectorTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${msg("New connector")}
                description=${msg("Create a new connector.")}
            >
                <ak-wizard-page-type-create
                    slot="initial"
                    .types=${this.connectorTypes}
                    layout=${TypeCreateWizardPageLayouts.grid}
                    @select=${(ev: CustomEvent<TypeCreate>) => {
                        if (!this.wizard) return;
                        const idx = this.wizard.steps.indexOf("initial") + 1;
                        // Exclude all current steps starting with type-,
                        // this happens when the user selects a type and then goes back
                        this.wizard.steps = this.wizard.steps.filter(
                            (step) => !step.startsWith("type-"),
                        );
                        this.wizard.steps.splice(
                            idx,
                            0,
                            `type-${ev.detail.component}-${ev.detail.modelName}`,
                        );
                        this.wizard.isValid = true;
                    }}
                >
                    <div slot="above-form">
                        <p>
                            ${msg(
                                "Connectors are required to create devices. Depending on connector type, agents either directly talk to them or they talk to and external API to create devices.",
                            )}
                        </p>
                    </div>
                </ak-wizard-page-type-create>
                ${this.connectorTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            label=${msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoint-connector-wizard": EndpointConnectorWizard;
    }
}
