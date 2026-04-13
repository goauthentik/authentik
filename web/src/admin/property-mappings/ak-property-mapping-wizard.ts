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
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CreateWizard } from "#elements/wizard/CreateWizard";

import { PropertymappingsApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize/init/install";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

@customElement("ak-property-mapping-wizard")
export class AKPropertyMappingWizard extends CreateWizard {
    #api = new PropertymappingsApi(DEFAULT_CONFIG);

    protected override apiEndpoint(requestInit?: RequestInit): Promise<TypeCreate[]> {
        return this.#api.propertymappingsAllTypesList(requestInit);
    }

    public static override verboseName = msg("Property Mapping");
    public static override verboseNamePlural = msg("Property Mappings");
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-wizard": AKPropertyMappingWizard;
    }
}
