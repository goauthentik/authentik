import "#admin/property-mappings/PropertyMappingNotification";
import "#admin/property-mappings/PropertyMappingProviderGoogleWorkspaceForm";
import "#admin/property-mappings/PropertyMappingProviderMicrosoftEntraForm";
import "#admin/property-mappings/PropertyMappingProviderRACForm";
import "#admin/property-mappings/PropertyMappingProviderRadiusForm";
import "#admin/property-mappings/PropertyMappingProviderSAMLForm";
import "#admin/property-mappings/PropertyMappingProviderSCIMForm";
import "#admin/property-mappings/PropertyMappingProviderScopeForm";
import "#admin/property-mappings/PropertyMappingSourceKerberosForm";
import "#admin/property-mappings/PropertyMappingSourceLDAPForm";
import "#admin/property-mappings/PropertyMappingSourceOAuthForm";
import "#admin/property-mappings/PropertyMappingSourcePlexForm";
import "#admin/property-mappings/PropertyMappingSourceSAMLForm";
import "#admin/property-mappings/PropertyMappingSourceSCIMForm";
import "#admin/property-mappings/PropertyMappingSourceTelegramForm";
import "#admin/property-mappings/PropertyMappingTestForm";
import "#elements/forms/ProxyForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import type { Wizard } from "#elements/wizard/Wizard";

import { PropertymappingsApi, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-property-mapping-wizard")
export class PropertyMappingWizard extends AKElement {
    static styles = [PFBase, PFButton];

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
