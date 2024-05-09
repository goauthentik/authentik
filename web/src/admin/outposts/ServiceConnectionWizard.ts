import "@goauthentik/admin/outposts/ServiceConnectionDockerForm";
import "@goauthentik/admin/outposts/ServiceConnectionKubernetesForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import { TypeCreateWizardPage } from "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostsApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-service-connection-wizard-initial")
export class InitialServiceConnectionWizardPage extends TypeCreateWizardPage {
    onSelect(type: TypeCreate): void {
        this.host.steps = ["initial", `type-${type.component}-${type.modelName}`];
        this.host.isValid = true;
    }
}

@customElement("ak-service-connection-wizard")
export class ServiceConnectionWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    @property()
    createText = msg("Create");

    @property({ attribute: false })
    connectionTypes: TypeCreate[] = [];

    firstUpdated(): void {
        new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllTypesList().then((types) => {
            this.connectionTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${msg("New outpost integration")}
                description=${msg("Create a new outpost integration.")}
            >
                <ak-service-connection-wizard-initial slot="initial" .types=${this.connectionTypes}>
                </ak-service-connection-wizard-initial>
                ${this.connectionTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => msg(str`Create ${type.name}`)}
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
