import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

import type { ProviderModelEnum as ProviderModelEnumType, TypeCreate } from "@goauthentik/api";
import { ProviderModelEnum } from "@goauthentik/api";
import type {
    LDAPProviderRequest,
    ModelRequest,
    OAuth2ProviderRequest,
    ProxyProviderRequest,
    SAMLProviderRequest,
    SCIMProviderRequest,
} from "@goauthentik/api";

import { OneOfProvider } from "../types";

type ProviderRenderer = () => TemplateResult;

type ProviderType = [string, string, string, ProviderRenderer, ProviderModelEnumType];

type ModelConverter = (provider: OneOfProvider) => ModelRequest;

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
    ],
    [
        "ldapprovider",
        msg("LDAP"),
        msg("Provide an LDAP interface for applications and users to authenticate against."),
        () => html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`,
        ProviderModelEnum.LdapLdapprovider,
    ],
    [
        "proxyprovider-proxy",
        msg("Transparent Reverse Proxy"),
        msg("For transparent reverse proxies with required authentication"),
        () => html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`,
        ProviderModelEnum.ProxyProxyprovider  
    ],
    [
        "proxyprovider-forwardsingle",
        msg("Forward Single Proxy"),
        msg("For nginx's auth_request or traefix's forwardAuth"),
        () => html`<ak-application-wizard-authentication-for-single-forward-proxy></ak-application-wizard-authentication-for-single-forward-proxy>`,
        ProviderModelEnum.ProxyProxyprovider  

    ],
    [
        "samlprovider",
        msg("SAML Manual configuration"),
        msg("Configure SAML provider manually"),
        () => html`<ak-application-wizard-authentication-by-saml-configuration></ak-application-wizard-authentication-by-saml-configuration>`,
        ProviderModelEnum.SamlSamlprovider
    ],
    [
        "scimprovider",
        msg("SCIM Manual configuration"),
        msg("Configure SCIM provider manually"),
        () => html`<ak-application-wizard-authentication-by-scim></ak-application-wizard-authentication-by-scim>`,
        ProviderModelEnum.ScimScimprovider
    ],
];

const converters = new Map<ProviderModelEnumType, ModelConverter>([
    [
        ProviderModelEnum.Oauth2Oauth2provider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.Oauth2Oauth2provider,
            ...(provider as OAuth2ProviderRequest),
        }),
    ],
    [
        ProviderModelEnum.LdapLdapprovider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.LdapLdapprovider,
            ...(provider as LDAPProviderRequest),
        }),
    ],
    [
        ProviderModelEnum.ProxyProxyprovider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
        }),
    ],
    [
        ProviderModelEnum.SamlSamlprovider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.SamlSamlprovider,
            ...(provider as SAMLProviderRequest),
        }),
    ],
    [
        ProviderModelEnum.ScimScimprovider,
        (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ScimScimprovider,
            ...(provider as SCIMProviderRequest),
        }),
    ],
]);

// Contract enforcement
const getConverter = (modelName: ProviderModelEnumType): ModelConverter => {
    const maybeConverter = converters.get(modelName);
    if (!maybeConverter) {
        throw new Error(`ModelName lookup failed in model converter definition: ${"modelName"}`);
    }
    return maybeConverter;
};

function mapProviders([formName, name, description, _, modelName]: ProviderType): LocalTypeCreate {
    return {
        formName,
        name,
        description,
        component: "",
        modelName,
        converter: getConverter(modelName),
    };
}

export const providerModelsList = _providerModelsTable.map(mapProviders);

export const providerRendererList = new Map<string, ProviderRenderer>(
    _providerModelsTable.map(([modelName, _0, _1, renderer]) => [modelName, renderer]),
);

export default providerModelsList;
