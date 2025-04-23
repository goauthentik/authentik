import {
    type DescriptionPair,
    renderDescriptionList,
} from "@goauthentik/components/DescriptionList.js";
import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";

import {
    ClientTypeEnum,
    LDAPProvider,
    MatchingModeEnum,
    OAuth2Provider,
    ProviderModelEnum,
    ProxyMode,
    ProxyProvider,
    RACProvider,
    RadiusProvider,
    RedirectURI,
    SAMLProvider,
    SCIMProvider,
} from "@goauthentik/api";

import { OneOfProvider } from "../types.js";

const renderSummary = (type: string, name: string, fields: DescriptionPair[]) =>
    renderDescriptionList([[msg("Type"), type], [msg("Name"), name], ...fields], {
        threecolumn: true,
    });

function renderSAMLOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as SAMLProvider;

    return renderSummary("SAML", provider.name, [
        [msg("ACS URL"), provider.acsUrl],
        [msg("Audience"), provider.audience || "-"],
        [msg("Issuer"), provider.issuer],
    ]);
}

function renderSCIMOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as SCIMProvider;
    return renderSummary("SCIM", provider.name, [[msg("URL"), provider.url]]);
}

function renderRadiusOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as RadiusProvider;
    return renderSummary("Radius", provider.name, [
        [msg("Client Networks"), provider.clientNetworks],
    ]);
}

function renderRACOverview(rawProvider: OneOfProvider) {
    const _provider = rawProvider as RACProvider;
}

function formatRedirectUris(uris: RedirectURI[] = []) {
    return uris.length > 0
        ? html`<ul class="pf-c-list pf-m-plain">
              ${uris.map(
                  (uri) =>
                      html`<li>
                          ${uri.url}
                          (${uri.matchingMode === MatchingModeEnum.Strict
                              ? msg("strict")
                              : msg("regexp")})
                      </li>`,
              )}
          </ul>`
        : "-";
}

const proxyModeToLabel = new Map([
    [ProxyMode.Proxy, msg("Proxy")],
    [ProxyMode.ForwardSingle, msg("Forward auth (single application)")],
    [ProxyMode.ForwardDomain, msg("Forward auth (domain-level)")],
    [ProxyMode.UnknownDefaultOpenApi, msg("Unknown proxy mode")],
]);

function renderProxyOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as ProxyProvider;
    return renderSummary("Proxy", provider.name, [
        [msg("Mode"), proxyModeToLabel.get(provider.mode ?? ProxyMode.Proxy)],
        ...match(provider.mode)
            .with(
                ProxyMode.Proxy,
                () =>
                    [
                        [msg("Internal Host"), provider.internalHost],
                        [msg("External Host"), provider.externalHost],
                    ] as DescriptionPair[],
            )
            .with(
                ProxyMode.ForwardSingle,
                () => [[msg("External Host"), provider.externalHost]] as DescriptionPair[],
            )
            .with(
                ProxyMode.ForwardDomain,
                () =>
                    [
                        [msg("Authentication URL"), provider.externalHost],
                        [msg("Cookie domain"), provider.cookieDomain],
                    ] as DescriptionPair[],
            )
            .otherwise(() => {
                throw new Error(
                    `Unrecognized proxy mode: ${provider.mode?.toString() ?? "-- undefined __"}`,
                );
            }),
        [
            msg("Basic-Auth"),
            html` <ak-status-label
                type="info"
                ?good=${provider.basicAuthEnabled}
            ></ak-status-label>`,
        ],
    ]);
}

const clientTypeToLabel = new Map<ClientTypeEnum, string>([
    [ClientTypeEnum.Confidential, msg("Confidential")],
    [ClientTypeEnum.Public, msg("Public")],
    [ClientTypeEnum.UnknownDefaultOpenApi, msg("Unknown type")],
]);

function renderOAuth2Overview(rawProvider: OneOfProvider) {
    const provider = rawProvider as OAuth2Provider;
    return renderSummary("OAuth2", provider.name, [
        [msg("Client type"), provider.clientType ? clientTypeToLabel.get(provider.clientType) : ""],
        [msg("Client ID"), provider.clientId],
        [msg("Redirect URIs"), formatRedirectUris(provider.redirectUris)],
    ]);
}

function renderLDAPOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as LDAPProvider;
    return renderSummary("Proxy", provider.name, [[msg("Base DN"), provider.baseDn]]);
}

const providerName = (p: ProviderModelEnum): string => p.toString().split(".")[1];

export const providerRenderers = new Map([
    [providerName(ProviderModelEnum.AuthentikProvidersSamlSamlprovider), renderSAMLOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersScimScimprovider), renderSCIMOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersRadiusRadiusprovider), renderRadiusOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersRacRacprovider), renderRACOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersProxyProxyprovider), renderProxyOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersOauth2Oauth2provider), renderOAuth2Overview],
    [providerName(ProviderModelEnum.AuthentikProvidersLdapLdapprovider), renderLDAPOverview],
]);
