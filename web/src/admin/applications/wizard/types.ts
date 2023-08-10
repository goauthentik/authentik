import {
    Application,
    LDAPProvider,
    OAuth2Provider,
    ProxyProvider,
    RadiusProvider,
    SAMLProvider,
    SCIMProvider,
} from "@goauthentik/api";

export type OneOfProvider =
    | Partial<SCIMProvider>
    | Partial<SAMLProvider>
    | Partial<RadiusProvider>
    | Partial<ProxyProvider>
    | Partial<OAuth2Provider>
    | Partial<LDAPProvider>;

export interface WizardState {
    step: number;
    providerType: string;
    application: Partial<Application>;
    provider: OneOfProvider;
}

export type WizardStateEvent = WizardState & { target?: HTMLInputElement };

