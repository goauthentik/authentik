import { type WizardStep } from "@goauthentik/components/ak-wizard-main/types";

import {
    type ApplicationRequest,
    type LDAPProviderRequest,
    type OAuth2ProviderRequest,
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

export interface ApplicationWizardState {
    providerModel: string;
    app: Partial<ApplicationRequest>;
    provider: OneOfProvider;
    errors: ValidationError;
}

type StatusType = "invalid" | "valid" | "submitted" | "failed";

export type ApplicationWizardStateUpdate = {
    update?: ApplicationWizardState;
    status?: StatusType;
};

export type ApplicationStep = WizardStep & {
    id: string;
    valid: boolean;
};
