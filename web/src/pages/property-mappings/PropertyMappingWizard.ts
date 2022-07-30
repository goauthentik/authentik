import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/forms/ProxyForm";
import "@goauthentik/web/elements/wizard/FormWizardPage";
import "@goauthentik/web/elements/wizard/Wizard";
import { WizardPage } from "@goauthentik/web/elements/wizard/WizardPage";
import "@goauthentik/web/pages/property-mappings/PropertyMappingLDAPForm";
import "@goauthentik/web/pages/property-mappings/PropertyMappingNotification";
import "@goauthentik/web/pages/property-mappings/PropertyMappingSAMLForm";
import "@goauthentik/web/pages/property-mappings/PropertyMappingScopeForm";
import "@goauthentik/web/pages/property-mappings/PropertyMappingTestForm";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PropertymappingsApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-property-mapping-wizard-initial")
export class InitialPropertyMappingWizardPage extends WizardPage {
    @property({ attribute: false })
    mappingTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }
    sidebarLabel = () => t`Select type`;

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
