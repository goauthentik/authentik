import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { WizardReadyProviderSuffix } from "#admin/applications/wizard/steps/ProviderChoices";
import { OneOfProvider } from "#admin/applications/wizard/steps/providers/shared";

import {
    ClientTypeEnum,
    LDAPProvider,
    MatchingModeEnum,
    OAuth2Provider,
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
import { html, TemplateResult } from "lit";

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
    const provider = rawProvider as RACProvider;
    return renderSummary("RAC", provider.name, [
        [msg("Connection expiry"), provider.connectionExpiry ?? "-"],
        [
            msg("Property mappings"),
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

export const ProviderOverviewRenderer: Readonly<
    Record<WizardReadyProviderSuffix, (provider: OneOfProvider) => TemplateResult>
> = {
    samlprovider: renderSAMLOverview,
    scimprovider: renderSCIMOverview,
    radiusprovider: renderRadiusOverview,
    racprovider: renderRACOverview,
    proxyprovider: renderProxyOverview,
    oauth2provider: renderOAuth2Overview,
    ldapprovider: renderLDAPOverview,
};
