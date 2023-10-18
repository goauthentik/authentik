import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

import type { ProviderModelEnum as ProviderModelEnumType, TypeCreate } from "@goauthentik/api";
import { ProviderModelEnum, ProxyMode } from "@goauthentik/api";
import type {
    LDAPProviderRequest,
    ModelRequest,
    OAuth2ProviderRequest,
    ProxyProviderRequest,
    RadiusProviderRequest,
    SAMLProviderRequest,
    SCIMProviderRequest,
} from "@goauthentik/api";

import { OneOfProvider } from "../types";

type ProviderRenderer = () => TemplateResult;

type ModelConverter = (provider: OneOfProvider) => ModelRequest;

type ProviderType = [
    string,
    string,
    string,
    ProviderRenderer,
    ProviderModelEnumType,
    ModelConverter,
];

export type LocalTypeCreate = TypeCreate & {
    formName: string;
    modelName: ProviderModelEnumType;
    converter: ModelConverter;
};

// prettier-ignore
const _providerModelsTable: ProviderType[] = [
    [
        "oauth2provider",
        msg("OAuth2/OpenID"),
        msg("Modern applications, APIs and Single-page applications."),
        () => html`<ak-application-wizard-authentication-by-oauth></ak-application-wizard-authentication-by-oauth>`,
        ProviderModelEnum.Oauth2Oauth2provider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.Oauth2Oauth2provider,
            ...(provider as OAuth2ProviderRequest),
        }),
    ],
    [
        "ldapprovider",
        msg("LDAP"),
        msg("Provide an LDAP interface for applications and users to authenticate against."),
        () => html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`,
        ProviderModelEnum.LdapLdapprovider,
                (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.LdapLdapprovider,
            ...(provider as LDAPProviderRequest),
        }),

    ],
    [
        "proxyprovider-proxy",
        msg("Transparent Reverse Proxy"),
        msg("For transparent reverse proxies with required authentication"),
        () => html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`,
        ProviderModelEnum.ProxyProxyprovider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
            mode: ProxyMode.Proxy,
        }),
    ],
    [
        "proxyprovider-forwardsingle",
        msg("Forward Auth Single Application"),
        msg("For nginx's auth_request or traefix's forwardAuth"),
        () => html`<ak-application-wizard-authentication-for-single-forward-proxy></ak-application-wizard-authentication-for-single-forward-proxy>`,
        ProviderModelEnum.ProxyProxyprovider  ,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
            mode: ProxyMode.ForwardSingle,
        }),

    ],
    [
        "proxyprovider-forwarddomain",
        msg("Forward Auth Domain Level"),
        msg("For nginx's auth_request or traefix's forwardAuth per root domain"),
        () => html`<ak-application-wizard-authentication-for-forward-proxy-domain></ak-application-wizard-authentication-for-forward-proxy-domain>`,
        ProviderModelEnum.ProxyProxyprovider  ,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
            mode: ProxyMode.ForwardDomain,
        }),
    ],
    [
        "samlprovider",
        msg("SAML Configuration"),
        msg("Configure SAML provider manually"),
        () => html`<ak-application-wizard-authentication-by-saml-configuration></ak-application-wizard-authentication-by-saml-configuration>`,
        ProviderModelEnum.SamlSamlprovider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.SamlSamlprovider,
            ...(provider as SAMLProviderRequest),
        }),
        
    ],
    [
        "radiusprovider",
        msg("RADIUS Configuration"),
        msg("Configure RADIUS provider manually"),
        () => html`<ak-application-wizard-authentication-by-radius></ak-application-wizard-authentication-by-radius>`,
        ProviderModelEnum.RadiusRadiusprovider,
                (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.RadiusRadiusprovider,
            ...(provider as RadiusProviderRequest),
        }),

    ],
    [
        "scimprovider",
        msg("SCIM configuration"),
        msg("Configure SCIM provider manually"),
        () => html`<ak-application-wizard-authentication-by-scim></ak-application-wizard-authentication-by-scim>`,
        ProviderModelEnum.ScimScimprovider,
                (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ScimScimprovider,
            ...(provider as SCIMProviderRequest),
        }),

    ],
];

function mapProviders([
    formName,
    name,
    description,
    _,
    modelName,
    converter,
]: ProviderType): LocalTypeCreate {
    return {
        formName,
        name,
        description,
        component: "",
        modelName,
        converter,
    };
}

export const providerModelsList = _providerModelsTable.map(mapProviders);

export const providerRendererList = new Map<string, ProviderRenderer>(
    _providerModelsTable.map(([modelName, _0, _1, renderer]) => [modelName, renderer]),
);

export default providerModelsList;
