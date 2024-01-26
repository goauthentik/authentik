import "@goauthentik/admin/property-mappings/PropertyMappingLDAPForm.js";
import "@goauthentik/admin/property-mappings/PropertyMappingNotification.js";
import "@goauthentik/admin/property-mappings/PropertyMappingRACForm.js";
import "@goauthentik/admin/property-mappings/PropertyMappingSAMLForm.js";
import "@goauthentik/admin/property-mappings/PropertyMappingScopeForm.js";
import "@goauthentik/admin/property-mappings/PropertyMappingTestForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import "@goauthentik/elements/Alert.js";
import { AKElement } from "@goauthentik/elements/Base.js";
import "@goauthentik/elements/forms/ProxyForm.js";
import "@goauthentik/elements/wizard/FormWizardPage.js";
import "@goauthentik/elements/wizard/Wizard.js";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage.js";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EnterpriseApi, LicenseSummary, PropertymappingsApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-property-mapping-wizard-initial")
export class InitialPropertyMappingWizardPage extends WizardPage {
    @property({ attribute: false })
    mappingTypes: TypeCreate[] = [];

    @property({ attribute: false })
    enterprise?: LicenseSummary;

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
                        ?disabled=${type.requiresEnterprise ? this.enterprise?.hasLicense : false}
                    />
                    <label class="pf-c-radio__label" for=${`${type.component}-${type.modelName}`}
                        >${type.name}</label
                    >
                    <span class="pf-c-radio__description">${type.description}</span>
                    ${type.requiresEnterprise && !this.enterprise?.hasLicense
                        ? html`
                              <ak-alert class="pf-c-radio__description" ?inline=${true}>
                                  ${msg("Provider require enterprise.")}
                                  <a href="#/enterprise/licenses">${msg("Learn more")}</a>
                              </ak-alert>
                          `
                        : nothing}
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

    @state()
    enterprise?: LicenseSummary;

    async firstUpdated(): Promise<void> {
        this.mappingTypes = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsAllTypesList();
        this.enterprise = await new EnterpriseApi(
            DEFAULT_CONFIG,
        ).enterpriseLicenseSummaryRetrieve();
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
                    .enterprise=${this.enterprise}
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
