import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

import type { TypeCreate } from "@goauthentik/api";

type ProviderRenderer = () => TemplateResult;

type ProviderType = [string, string, string, ProviderRenderer];

// prettier-ignore
const _providerTypesTable: ProviderType[] = [
    [
        "oauth2provider",
        msg("OAuth2/OpenID"),
        msg("Modern applications, APIs and Single-page applications."),
        () => html`<ak-application-wizard-authentication-by-oauth></ak-application-wizard-authentication-by-oauth>`
    ],
    
    [
        "ldapprovider",
        msg("LDAP"),
        msg("Provide an LDAP interface for applications and users to authenticate against."),
        () => html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`
    ],
    
    [
        "proxyprovider-proxy",
        msg("Transparent Reverse Proxy"),
        msg("For transparent reverse proxies with required authentication"),
        () => html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`
    ],

    [
        "proxyprovider-forwardsingle",
        msg("Forward Single Proxy"),
        msg("For nginx's auth_request or traefix's forwardAuth"),
        () => html`<ak-application-wizard-authentication-for-single-forward-proxy></ak-application-wizard-authentication-for-single-forward-proxy>`
    ],

    [
        "samlprovider-manual",
        msg("SAML Manual configuration"),
        msg("Configure SAML provider manually"),
        () => html`<p>Under construction</p>`
    ],
    
    [
        "samlprovider-import",
        msg("SAML Import Configuration"),
        msg("Create a SAML provider by importing its metadata"),
        () => html`<p>Under construction</p>`
    ],
];

function mapProviders([modelName, name, description]: ProviderType): TypeCreate {
    return {
        modelName,
        name,
        description,
        component: "",
    };
}

export const providerTypesList = _providerTypesTable.map(mapProviders);

export const providerRendererList = new Map<string, ProviderRenderer>(
    _providerTypesTable.map(([modelName, _0, _1, renderer]) => [modelName, renderer]),
);

export default providerTypesList;
