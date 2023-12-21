import "@goauthentik/admin/property-mappings/PropertyMappingLDAPForm";
import "@goauthentik/admin/property-mappings/PropertyMappingNotification";
import "@goauthentik/admin/property-mappings/PropertyMappingSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingScopeForm";
import "@goauthentik/admin/property-mappings/PropertyMappingTestForm";
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
        return [PFBase, PFForm, PFButton, PFRadio];
    }
    sidebarLabel = () => msg("Select type");

    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
        this.shadowRoot
            ?.querySelectorAll<HTMLInputElement>("input[type=radio]")
            .forEach((radio) => {
                if (radio.checked) {
                    radio.dispatchEvent(new CustomEvent("change"));
                }
            });
    };

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
export class PropertyMappingWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
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
                header=${msg("New property mapping")}
                description=${msg("Create a new property mapping.")}
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
                            .sidebarLabel=${() => msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-wizard>
        `;
    }
}
