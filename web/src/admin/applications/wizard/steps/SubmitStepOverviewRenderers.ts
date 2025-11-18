import { OneOfProvider } from "../types.js";

import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

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

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";

const renderSummary = (type: string, name: string, fields: DescriptionPair[]) =>
    renderDescriptionList(
        [
            [
                msg("Type", {
                    id: "label.type",
                }),
                type,
            ],
            [
                msg("Name", {
                    id: "label.name",
                }),
                name,
            ],
            ...fields,
        ],
        {
            threecolumn: true,
        },
    );

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
    return renderSummary("SCIM", provider.name, [
        [
            msg("URL", {
                id: "label.url",
            }),
            provider.url,
        ],
    ]);
}

function renderRadiusOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as RadiusProvider;
    return renderSummary("Radius", provider.name, [
        [msg("Client Networks", { id: "label.client-networks" }), provider.clientNetworks],
    ]);
}

function renderRACOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as RACProvider;
    return renderSummary("RAC", provider.name, [
        [
            msg("Connection expiry", {
                id: "label.connection-expiry",
            }),
            provider.connectionExpiry ?? msg("-"),
        ],
        [
            msg("Property mappings", {
                id: "label.property-mappings",
            }),
            Array.isArray(provider.propertyMappings) && provider.propertyMappings.length
                ? provider.propertyMappings.join(", ")
                : msg("None"),
        ],
    ]);
}

function formatRedirectUris(uris: RedirectURI[] = []) {
    return uris.length > 0
        ? html`<ul class="pf-c-list pf-m-plain">
              ${uris.map(
                  (uri) =>
                      html`<li>
                          ${uri.url}
                          (${uri.matchingMode === MatchingModeEnum.Strict
                              ? msg("strict", { id: "matching-mode.strict" })
                              : msg("regexp", { id: "matching-mode.regexp" })})
                      </li>`,
              )}
          </ul>`
        : "-";
}

function createProxyModeLabelRecord(): Record<ProxyMode, string> {
    return {
        [ProxyMode.Proxy]: msg("Proxy", {
            id: "label.proxy-mode.proxy",
        }),
        [ProxyMode.ForwardSingle]: msg("Forward auth (single application)", {
            id: "label.proxy-mode.forward-single",
        }),
        [ProxyMode.ForwardDomain]: msg("Forward auth (domain-level)", {
            id: "label.proxy-mode.forward-domain",
        }),
        [ProxyMode.UnknownDefaultOpenApi]: msg("Unknown proxy mode", {
            id: "label.proxy-mode.unknown",
        }),
    };
}

function renderProxyOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as ProxyProvider;

    const proxyModeToLabel = createProxyModeLabelRecord();
    const mode = provider.mode ?? ProxyMode.Proxy;
    const modeLabel = proxyModeToLabel[mode];

    return renderSummary("Proxy", provider.name, [
        [msg("Mode"), modeLabel],
        ...match(provider.mode)
            .with(
                ProxyMode.Proxy,
                () =>
                    [
                        [
                            msg("Internal Host", {
                                id: "label.internal-host",
                            }),
                            provider.internalHost,
                        ],
                        [
                            msg("External Host", {
                                id: "label.external-host",
                            }),
                            provider.externalHost,
                        ],
                    ] satisfies DescriptionPair[],
            )
            .with(
                ProxyMode.ForwardSingle,
                () =>
                    [
                        [
                            msg("External Host", {
                                id: "label.external-host",
                            }),
                            provider.externalHost,
                        ],
                    ] satisfies DescriptionPair[],
            )
            .with(
                ProxyMode.ForwardDomain,
                () =>
                    [
                        [
                            msg("Authentication URL", {
                                id: "label.authentication-url",
                            }),
                            provider.externalHost,
                        ],
                        [
                            msg("Cookie domain", {
                                id: "label.cookie-domain",
                            }),
                            provider.cookieDomain,
                        ],
                    ] satisfies DescriptionPair[],
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

function createClientTypeLabelRecord(): Record<ClientTypeEnum, string> {
    return {
        [ClientTypeEnum.Confidential]: msg("Confidential", {
            id: "label.oauth2.client.type.confidential",
        }),
        [ClientTypeEnum.Public]: msg("Public", {
            id: "label.oauth2.client.type.public",
        }),
        [ClientTypeEnum.UnknownDefaultOpenApi]: msg("Unknown type", {
            id: "label.oauth2.client.type.unknown",
        }),
    };
}

function renderOAuth2Overview(rawProvider: OneOfProvider) {
    const provider = rawProvider as OAuth2Provider;
    const clientTypeToLabel = createClientTypeLabelRecord();
    const clientTypeLabel = provider.clientType ? clientTypeToLabel[provider.clientType] : "";

    return renderSummary("OAuth2", provider.name, [
        [
            msg("Client type", {
                id: "label.oauth2.client.type",
            }),
            clientTypeLabel,
        ],
        [
            msg("Client ID", {
                id: "label.oauth2.client.id",
            }),
            provider.clientId,
        ],
        [
            msg("Redirect URIs", {
                id: "label.oauth2.redirect.uris",
            }),
            formatRedirectUris(provider.redirectUris),
        ],
    ]);
}

function renderLDAPOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as LDAPProvider;
    return renderSummary("Proxy", provider.name, [
        [
            msg("Base DN", {
                id: "label.ldap.base.dn",
            }),
            provider.baseDn,
        ],
    ]);
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
