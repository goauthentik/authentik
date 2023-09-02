import {
    ApplicationRequest,
    LDAPProviderRequest,
    OAuth2ProviderRequest,
    ProxyProviderRequest,
    RadiusProviderRequest,
    SAMLProviderRequest,
    SCIMProviderRequest,
} from "@goauthentik/api";

export type OneOfProvider =
    | Partial<SCIMProviderRequest>
    | Partial<SAMLProviderRequest>
    | Partial<RadiusProviderRequest>
    | Partial<ProxyProviderRequest>
    | Partial<OAuth2ProviderRequest>
    | Partial<LDAPProviderRequest>;

export interface WizardState {
    providerModel: string;
    app: Partial<ApplicationRequest>;
    provider: OneOfProvider;
}

type StatusType = "invalid" | "valid" | "submitted" | "failed";

export type WizardStateUpdate = {
    update?: Partial<WizardState>,
    status?: StatusType,
};
