import "@goauthentik/admin/property-mappings/PropertyMappingLDAPForm";
import "@goauthentik/admin/property-mappings/PropertyMappingNotification";
import "@goauthentik/admin/property-mappings/PropertyMappingRACForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingScopeForm";
import "@goauthentik/admin/property-mappings/PropertyMappingTestForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import { TypeCreateWizardPage } from "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PropertymappingsApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-property-mapping-wizard-initial")
export class InitialPropertyMappingWizardPage extends TypeCreateWizardPage {
    onSelect(type: TypeCreate): void {
        this.host.steps = ["initial", `type-${type.component}-${type.modelName}`];
        this.host.isValid = true;
    }
}

@customElement("ak-property-mapping-wizard")
export class PropertyMappingWizard extends AKElement {
    static get styles() {
        return [PFBase, PFButton];
    }

    @property({ attribute: false })
    mappingTypes: TypeCreate[] = [];

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
                <ak-property-mapping-wizard-initial slot="initial" .types=${this.mappingTypes}>
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
