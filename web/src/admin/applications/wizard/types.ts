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
    step: number;
    providerModel: string;
    app: Partial<ApplicationRequest>;
    provider: OneOfProvider;
}

export type WizardStateEvent = { update: Partial<WizardState> };
