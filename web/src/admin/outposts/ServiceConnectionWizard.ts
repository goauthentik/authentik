import "@goauthentik/admin/outposts/ServiceConnectionDockerForm";
import "@goauthentik/admin/outposts/ServiceConnectionKubernetesForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostsApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-service-connection-wizard-initial")
export class InitialServiceConnectionWizardPage extends WizardPage {
    @property({ attribute: false })
    connectionTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }
    sidebarLabel = () => msg("Select type");

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.connectionTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${`${type.component}-${type.modelName}`}
                        @change=${() => {
                            this.host.steps = [
                                "initial",
                                `type-${type.component}-${type.modelName}`,
                            ];
                            this.host.isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${`${type.component}-${type.modelName}`}
                        >${type.name}</label
                    >
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form>`;
    }
}

@customElement("ak-service-connection-wizard")
export class ServiceConnectionWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
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
                <ak-service-connection-wizard-initial
                    slot="initial"
                    .connectionTypes=${this.connectionTypes}
                >
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
