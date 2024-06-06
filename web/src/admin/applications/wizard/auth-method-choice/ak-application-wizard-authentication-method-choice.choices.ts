import "@goauthentik/admin/common/ak-license-notice";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

import type { ProviderModelEnum as ProviderModelEnumType, TypeCreate } from "@goauthentik/api";
import { ProviderModelEnum, ProxyMode } from "@goauthentik/api";
import type {
    LDAPProviderRequest,
    ModelRequest,
    OAuth2ProviderRequest,
    ProxyProviderRequest,
    RACProviderRequest,
    RadiusProviderRequest,
    SAMLProviderRequest,
    SCIMProviderRequest,
} from "@goauthentik/api";

import { OneOfProvider } from "../types";

type ProviderRenderer = () => TemplateResult;

type ModelConverter = (provider: OneOfProvider) => ModelRequest;

type ProviderNoteProvider = () => TemplateResult | undefined;
type ProviderNote = ProviderNoteProvider | undefined;

export type LocalTypeCreate = TypeCreate & {
    formName: string;
    modelName: ProviderModelEnumType;
    converter: ModelConverter;
    note?: ProviderNote;
    renderer: ProviderRenderer;
};

export const providerModelsList: LocalTypeCreate[] = [
    {
        formName: "oauth2provider",
        name: msg("OAuth2/OIDC (Open Authorization/OpenID Connect)"),
        description: msg("Modern applications, APIs and Single-page applications."),
        renderer: () =>
            html`<ak-application-wizard-authentication-by-oauth></ak-application-wizard-authentication-by-oauth>`,
        modelName: ProviderModelEnum.Oauth2Oauth2provider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.Oauth2Oauth2provider,
            ...(provider as OAuth2ProviderRequest),
        }),
        component: "",
        iconUrl: "/static/authentik/sources/openidconnect.svg",
    },
    {
        formName: "ldapprovider",
        name: msg("LDAP (Lightweight Directory Access Protocol)"),
        description: msg(
            "Provide an LDAP interface for applications and users to authenticate against.",
        ),
        renderer: () =>
            html`<ak-application-wizard-authentication-by-ldap></ak-application-wizard-authentication-by-ldap>`,
        modelName: ProviderModelEnum.LdapLdapprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.LdapLdapprovider,
            ...(provider as LDAPProviderRequest),
        }),
        component: "",
        iconUrl: "/static/authentik/sources/ldap.png",
    },
    {
        formName: "proxyprovider-proxy",
        name: msg("Transparent Reverse Proxy"),
        description: msg("For transparent reverse proxies with required authentication"),
        renderer: () =>
            html`<ak-application-wizard-authentication-for-reverse-proxy></ak-application-wizard-authentication-for-reverse-proxy>`,
        modelName: ProviderModelEnum.ProxyProxyprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
            mode: ProxyMode.Proxy,
        }),
        component: "",
        iconUrl: "/static/authentik/sources/proxy.svg",
    },
    {
        formName: "proxyprovider-forwardsingle",
        name: msg("Forward Auth (Single Application)"),
        description: msg("For nginx's auth_request or traefik's forwardAuth"),
        renderer: () =>
            html`<ak-application-wizard-authentication-for-single-forward-proxy></ak-application-wizard-authentication-for-single-forward-proxy>`,
        modelName: ProviderModelEnum.ProxyProxyprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
            mode: ProxyMode.ForwardSingle,
        }),
        component: "",
        iconUrl: "/static/authentik/sources/proxy.svg",
    },
    {
        formName: "proxyprovider-forwarddomain",
        name: msg("Forward Auth (Domain Level)"),
        description: msg("For nginx's auth_request or traefik's forwardAuth per root domain"),
        renderer: () =>
            html`<ak-application-wizard-authentication-for-forward-proxy-domain></ak-application-wizard-authentication-for-forward-proxy-domain>`,
        modelName: ProviderModelEnum.ProxyProxyprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ProxyProxyprovider,
            ...(provider as ProxyProviderRequest),
            mode: ProxyMode.ForwardDomain,
        }),
        component: "",
        iconUrl: "/static/authentik/sources/proxy.svg",
    },
    {
        formName: "racprovider",
        name: msg("Remote Access Provider"),
        description: msg("Remotely access computers/servers via RDP/SSH/VNC"),
        renderer: () =>
            html`<ak-application-wizard-authentication-for-rac></ak-application-wizard-authentication-for-rac>`,
        modelName: ProviderModelEnum.RacRacprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.RacRacprovider,
            ...(provider as RACProviderRequest),
        }),
        note: () => html`<ak-license-notice></ak-license-notice>`,
        requiresEnterprise: true,
        component: "",
        iconUrl: "/static/authentik/sources/rac.svg",
    },
    {
        formName: "samlprovider",
        name: msg("SAML (Security Assertion Markup Language)"),
        description: msg("Configure SAML provider manually"),
        renderer: () =>
            html`<ak-application-wizard-authentication-by-saml-configuration></ak-application-wizard-authentication-by-saml-configuration>`,
        modelName: ProviderModelEnum.SamlSamlprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.SamlSamlprovider,
            ...(provider as SAMLProviderRequest),
        }),
        component: "",
        iconUrl: "/static/authentik/sources/saml.png",
    },
    {
        formName: "radiusprovider",
        name: msg("RADIUS (Remote Authentication Dial-In User Service)"),
        description: msg("Configure RADIUS provider manually"),
        renderer: () =>
            html`<ak-application-wizard-authentication-by-radius></ak-application-wizard-authentication-by-radius>`,
        modelName: ProviderModelEnum.RadiusRadiusprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.RadiusRadiusprovider,
            ...(provider as RadiusProviderRequest),
        }),
        component: "",
        iconUrl: "/static/authentik/sources/radius.svg",
    },
    {
        formName: "scimprovider",
        name: msg("SCIM (System for Cross-domain Identity Management)"),
        description: msg("Configure SCIM provider manually"),
        renderer: () =>
            html`<ak-application-wizard-authentication-by-scim></ak-application-wizard-authentication-by-scim>`,
        modelName: ProviderModelEnum.ScimScimprovider,
        converter: (provider: OneOfProvider) => ({
            providerModel: ProviderModelEnum.ScimScimprovider,
            ...(provider as SCIMProviderRequest),
        }),
        component: "",
        iconUrl: "/static/authentik/sources/scim.png",
    },
];

export const providerRendererList = new Map<string, ProviderRenderer>(
    providerModelsList.map((tc) => [tc.formName, tc.renderer]),
);

export default providerModelsList;
