import {
    type ApplicationRequest,
    type LDAPProviderRequest,
    type OAuth2ProviderRequest,
    type PolicyBinding,
    type ProvidersSamlImportMetadataCreateRequest,
    type ProxyProviderRequest,
    type RACProviderRequest,
    type RadiusProviderRequest,
    type SAMLProviderRequest,
    type SCIMProviderRequest,
    type ValidationError,
} from "@goauthentik/api";

export type OneOfProvider =
    | Partial<SCIMProviderRequest>
    | Partial<SAMLProviderRequest>
    | Partial<ProvidersSamlImportMetadataCreateRequest>
    | Partial<RACProviderRequest>
    | Partial<RadiusProviderRequest>
    | Partial<ProxyProviderRequest>
    | Partial<OAuth2ProviderRequest>
    | Partial<LDAPProviderRequest>;

// We use the PolicyBinding instead of the PolicyBindingRequest here, because that gives us a slot
// to preserve the retrieved policy, group, or user object from the SearchSelect used to find it,
// which in turn allows us to create a user-friendly display of bindings on the "List of configured
// bindings" page in the wizard.  The PolicyBinding is converted into a PolicyBindingRequest during
// the submission phase.

export interface ApplicationWizardState {
    providerModel: string;
    app: Partial<ApplicationRequest>;
    provider: OneOfProvider;
    errors: ValidationError;
    bindings: PolicyBinding[];
    currentBinding: number;
}

export interface ApplicationWizardStateUpdate {
    providerModel?: string;
    app?: Partial<ApplicationRequest>;
    provider?: OneOfProvider;
    errors?: ValidationError;
    bindings?: PolicyBinding[];
    currentBinding?: number;
}
