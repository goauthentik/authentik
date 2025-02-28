import "@goauthentik/admin/property-mappings/PropertyMappingNotification";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderGoogleWorkspaceForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderMicrosoftEntraForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderRACForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderRadiusForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderSCIMForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderScopeForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceKerberosForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceLDAPForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceOAuthForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourcePlexForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceSCIMForm";
import "@goauthentik/admin/property-mappings/PropertyMappingTestForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import type { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PropertymappingsApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-property-mapping-wizard")
export class PropertyMappingWizard extends AKElement {
    static get styles() {
        return [PFBase, PFButton];
    }

    @property({ attribute: false })
    mappingTypes: TypeCreate[] = [];

    @query("ak-wizard")
    wizard?: Wizard;

    async firstUpdated(): Promise<void> {
        this.mappingTypes = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsAllTypesList();
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${msg("New property mapping")}
                description=${msg("Create a new property mapping.")}
            >
                <ak-wizard-page-type-create
                    slot="initial"
                    .types=${this.mappingTypes}
                    @select=${(ev: CustomEvent<TypeCreate>) => {
                        if (!this.wizard) return;
                        this.wizard.steps = [
                            "initial",
                            `type-${ev.detail.component}-${ev.detail.modelName}`,
                        ];
                        this.wizard.isValid = true;
                    }}
                >
                </ak-wizard-page-type-create>
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-wizard": PropertyMappingWizard;
    }
}
