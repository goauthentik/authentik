import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostsApi, TypeCreate } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ProxyForm";
import "../../elements/wizard/FormWizardPage";
import "../../elements/wizard/Wizard";
import { WizardPage } from "../../elements/wizard/WizardPage";
import "./ServiceConnectionDockerForm";
import "./ServiceConnectionKubernetesForm";

@customElement("ak-service-connection-wizard-initial")
export class InitialServiceConnectionWizardPage extends WizardPage {
    @property({ attribute: false })
    connectionTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }

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
                            this.host.setSteps(
                                "initial",
                                `type-${type.component}-${type.modelName}`,
                            );
                            this._isValid = true;
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
export class ServiceConnectionWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property()
    createText = t`Create`;

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
                header=${t`New outpost integration`}
                description=${t`Create a new outpost integration.`}
            >
                <ak-service-connection-wizard-initial
                    slot="initial"
                    .sidebarLabel=${() => t`Select type`}
                    .connectionTypes=${this.connectionTypes}
                >
                </ak-service-connection-wizard-initial>
                ${this.connectionTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
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
