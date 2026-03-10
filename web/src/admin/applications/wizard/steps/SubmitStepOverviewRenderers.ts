import "#components/ak-status-label";

import { SlottedTemplateResult } from "#elements/types";

import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { OneOfProvider } from "#admin/applications/wizard/steps/providers/shared";

import {
    ClientTypeEnum,
    LDAPProvider,
    MatchingModeEnum,
    OAuth2Provider,
    ProviderModelEnum,
    ProvidersSamlImportMetadataCreateRequest,
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
    renderDescriptionList([[msg("Type"), type], [msg("Name"), name], ...fields], {
        threecolumn: true,
    });

export type ProviderOverview<T extends OneOfProvider | unknown = unknown> = (
    provider: T,
) => SlottedTemplateResult;

const renderSAMLOverview: ProviderOverview<SAMLProvider> = (provider) => {
    return renderSummary("SAML", provider.name, [
        [msg("ACS URL"), provider.acsUrl],
        [msg("Audience"), provider.audience || "-"],
        [msg("Issuer"), provider.issuer],
    ]);
};

const renderSAMLImportOverview: ProviderOverview<ProvidersSamlImportMetadataCreateRequest> = (
    provider,
) => {
    return renderSummary("SAML", provider.name, [
        [msg("Authorization flow"), provider.authorizationFlow ?? "-"],
        [msg("Invalidation flow"), provider.invalidationFlow ?? "-"],
    ]);
};

const renderSCIMOverview: ProviderOverview<SCIMProvider> = (provider) => {
    return renderSummary("SCIM", provider.name, [[msg("URL"), provider.url]]);
};

const renderRadiusOverview: ProviderOverview<RadiusProvider> = (provider) => {
    return renderSummary("Radius", provider.name, [
        [msg("Client Networks"), provider.clientNetworks],
    ]);
};

const renderRACOverview: ProviderOverview<RACProvider> = (provider) => {
    return renderSummary("RAC", provider.name, [
        [msg("Connection expiry"), provider.connectionExpiry ?? "-"],
        [
            msg("Property mappings"),
            Array.isArray(provider.propertyMappings) && provider.propertyMappings.length
                ? provider.propertyMappings.join(", ")
                : msg("None"),
        ],
    ]);
};

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

const proxyModeToLabel = {
    [ProxyMode.Proxy]: () => msg("Proxy"),
    [ProxyMode.ForwardSingle]: () => msg("Forward auth (single application)"),
    [ProxyMode.ForwardDomain]: () => msg("Forward auth (domain-level)"),
    [ProxyMode.UnknownDefaultOpenApi]: () => msg("Unknown proxy mode"),
} as const satisfies Record<ProxyMode, () => string>;

const renderProxyOverview: ProviderOverview<ProxyProvider> = (provider) => {
    const proxyHostMappings: DescriptionPair[] = match<ProxyMode | undefined, DescriptionPair[]>(
        provider.mode,
    )
        .with(ProxyMode.Proxy, () => {
            return [
                [msg("Internal Host"), provider.internalHost],
                [msg("External Host"), provider.externalHost],
            ];
        })
        .with(ProxyMode.ForwardSingle, () => {
            return [[msg("External Host"), provider.externalHost]];
        })
        .with(ProxyMode.ForwardDomain, () => {
            return [
                [msg("Authentication URL"), provider.externalHost],
                [msg("Cookie domain"), provider.cookieDomain],
            ];
        })
        .otherwise(() => {
            throw new Error(
                `Unrecognized proxy mode: ${provider.mode?.toString() ?? "-- undefined __"}`,
            );
        });

    const label = proxyModeToLabel[provider.mode ?? ProxyMode.Proxy];

    return renderSummary("Proxy", provider.name, [
        [msg("Mode"), label()],
        ...proxyHostMappings,
        [
            msg("Basic-Auth"),
            html`<ak-status-label
                type="info"
                ?good=${provider.basicAuthEnabled}
            ></ak-status-label>`,
        ],
    ]);
};

const clientTypeToLabel = {
    [ClientTypeEnum.Confidential]: () => msg("Confidential"),
    [ClientTypeEnum.Public]: () => msg("Public"),
    [ClientTypeEnum.UnknownDefaultOpenApi]: () => msg("Unknown type"),
} as const satisfies Record<ClientTypeEnum, () => string>;

const renderOAuth2Overview: ProviderOverview<OAuth2Provider> = (provider) => {
    const label = provider.clientType ? clientTypeToLabel[provider.clientType]() : "";

    return renderSummary("OAuth2", provider.name, [
        [msg("Client type"), label],
        [msg("Client ID"), provider.clientId],
        [msg("Redirect URIs"), formatRedirectUris(provider.redirectUris)],
    ]);
};

const renderLDAPOverview: ProviderOverview<LDAPProvider> = (provider) => {
    return renderSummary("Proxy", provider.name, [[msg("Base DN"), provider.baseDn]]);
};

const providerName = (p: ProviderModelEnum): string => p.toString().split(".")[1];

export const providerRenderers = new Map<string, ProviderOverview<OneOfProvider>>([
    [providerName(ProviderModelEnum.AuthentikProvidersSamlSamlprovider), renderSAMLOverview],
    ["samlproviderimportmodel", renderSAMLImportOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersScimScimprovider), renderSCIMOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersRadiusRadiusprovider), renderRadiusOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersRacRacprovider), renderRACOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersProxyProxyprovider), renderProxyOverview],
    [providerName(ProviderModelEnum.AuthentikProvidersOauth2Oauth2provider), renderOAuth2Overview],
    [providerName(ProviderModelEnum.AuthentikProvidersLdapLdapprovider), renderLDAPOverview],
] satisfies [string, ProviderOverview<never>][] as [string, ProviderOverview<OneOfProvider>][]);
