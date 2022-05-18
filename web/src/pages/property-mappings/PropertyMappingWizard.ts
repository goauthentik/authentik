import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PropertymappingsApi, TypeCreate } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ProxyForm";
import "../../elements/wizard/FormWizardPage";
import "../../elements/wizard/Wizard";
import { WizardPage } from "../../elements/wizard/WizardPage";
import "./PropertyMappingLDAPForm";
import "./PropertyMappingNotification";
import "./PropertyMappingSAMLForm";
import "./PropertyMappingScopeForm";
import "./PropertyMappingTestForm";

@customElement("ak-property-mapping-wizard-initial")
export class InitialPropertyMappingWizardPage extends WizardPage {
    @property({ attribute: false })
    mappingTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.mappingTypes.map((type) => {
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

@customElement("ak-property-mapping-wizard")
export class PropertyMappingWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property({ attribute: false })
    mappingTypes: TypeCreate[] = [];

    firstUpdated(): void {
        new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllTypesList().then((types) => {
            this.mappingTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${t`New property mapping`}
                description=${t`Create a new property mapping.`}
            >
                <ak-property-mapping-wizard-initial
                    slot="initial"
                    .sidebarLabel=${() => t`Select type`}
                    .mappingTypes=${this.mappingTypes}
                >
                </ak-property-mapping-wizard-initial>
                ${this.mappingTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-wizard>
        `;
    }
}
