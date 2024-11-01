import {
    type ApplicationRequest,
    type LDAPProviderRequest,
    type OAuth2ProviderRequest,
    type PolicyBinding,
    type ProvidersSamlImportMetadataCreateRequest,
    type ProxyMode,
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

export type ValidationRecord = { [key: string]: string[] };

// TODO: Elf, extend this type and apply it to every object in the wizard.  Then run
// the type-checker again.

export type ExtendedValidationError = ValidationError & {
    app?: ValidationRecord;
    provider?: ValidationRecord;
    bindings?: ValidationRecord;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    detail?: any;
};

// We use the PolicyBinding instead of the PolicyBindingRequest here, because that gives us a slot
// in which to preserve the retrieved policy, group, or user object from the SearchSelect used to
// find it, which in turn allows us to create a user-friendly display of bindings on the "List of
// configured bindings" page in the wizard. The PolicyBinding is converted into a
// PolicyBindingRequest during the submission phase.

export interface ApplicationWizardState {
    app: Partial<ApplicationRequest>;
    providerModel: string;
    provider: OneOfProvider;
    proxyMode: ProxyMode;
    bindings: PolicyBinding[];
    currentBinding: number;
    errors: ExtendedValidationError;
}

export interface ApplicationWizardStateUpdate {
    app?: Partial<ApplicationRequest>;
    providerModel?: string;
    provider?: OneOfProvider;
    proxyMode?: ProxyMode;
    bindings?: PolicyBinding[];
    currentBinding?: number;
    errors?: ValidationError;
}
