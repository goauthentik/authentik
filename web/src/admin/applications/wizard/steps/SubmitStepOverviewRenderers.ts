import { msg } from "@lit/localize";
import { html, nothing } from "lit";

import {
    ClientTypeEnum,
    LDAPProvider,
    OAuth2Provider,
    ProviderModelEnum,
    ProxyMode,
    ProxyProvider,
    RACProvider,
    RadiusProvider,
    SAMLProvider,
    SCIMProvider,
} from "@goauthentik/api";

import { OneOfProvider } from "../types.js";

function renderSAMLOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as SAMLProvider;
    return html` <dl>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Name")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.name}</div>
            </dd>
        </div>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("ACS URL")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.acsUrl}</div>
            </dd>
        </div>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Audience")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.audience || "-"}</div>
            </dd>
        </div>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Issuer")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.issuer}</div>
            </dd>
        </div>
    </dl>`;
}

function renderSCIMOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as SCIMProvider;
    return html` <dl class="pf-c-description-list pf-m-3-col-on-lg">
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Name")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.name}</div>
            </dd>
        </div>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("URL")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.url}</div>
            </dd>
        </div>
    </dl>`;
}

function renderRadiusOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as RadiusProvider;
    return html`
        <dl class="pf-c-description-list pf-m-3-col-on-lg">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Name")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${provider.name}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Client Networks")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${provider.clientNetworks}</div>
                </dd>
            </div>
        </dl>
    `;
}

function renderRACOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as RACProvider;
    return html`
        <dl class="pf-c-description-list pf-m-3-col-on-lg">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Name")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${provider.name}</div>
                </dd>
            </div>
        </dl>
    `;
}

const proxyModeToLabel = new Map([
    [ProxyMode.Proxy, msg("Proxy")],
    [ProxyMode.ForwardSingle, msg("Forward auth (single application)")],
    [ProxyMode.ForwardDomain, msg("Forward auth (domain-level)")],
    [ProxyMode.UnknownDefaultOpenApi, msg("Unknown proxy mode")],
]);

function renderProxyOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as ProxyProvider;
    return html` <dl class="pf-c-description-list pf-m-3-col-on-lg">
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Name")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.name}</div>
            </dd>
        </div>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Mode")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">
                    ${proxyModeToLabel.get(provider.mode ?? ProxyMode.Proxy)}
                </div>
            </dd>
        </div>
        ${provider.mode === ProxyMode.Proxy
            ? html` <div class="pf-c-description-list__group">
                  <dt class="pf-c-description-list__term">
                      <span class="pf-c-description-list__text">${msg("Internal Host")}</span>
                  </dt>
                  <dd class="pf-c-description-list__description">
                      <div class="pf-c-description-list__text">${provider.internalHost}</div>
                  </dd>
              </div>`
            : nothing}
        ${provider.mode === ProxyMode.Proxy || provider.mode === ProxyMode.ForwardSingle
            ? html` <div class="pf-c-description-list__group">
                  <dt class="pf-c-description-list__term">
                      <span class="pf-c-description-list__text">${msg("External Host")}</span>
                  </dt>
                  <dd class="pf-c-description-list__description">
                      <div class="pf-c-description-list__text">
                          <a target="_blank" href="${provider.externalHost}"
                              >${provider.externalHost}</a
                          >
                      </div>
                  </dd>
              </div>`
            : nothing}
        ${provider.mode === ProxyMode.ForwardDomain
            ? html` <div class="pf-c-description-list__group">
                      <dt class="pf-c-description-list__term">
                          <span class="pf-c-description-list__text"
                              >${msg("Authentication URL")}</span
                          >
                      </dt>
                      <dd class="pf-c-description-list__description">
                          <div class="pf-c-description-list__text">
                              <div class="pf-c-description-list__text">
                                  ${provider.externalHost}
                              </div>
                          </div>
                      </dd>
                  </div>
                  <div class="pf-c-description-list__group">
                      <dt class="pf-c-description-list__term">
                          <span class="pf-c-description-list__text">${msg("Cookie domain")}</span>
                      </dt>
                      <dd class="pf-c-description-list__description">
                          <div class="pf-c-description-list__text">
                              <div class="pf-c-description-list__text">
                                  ${provider.cookieDomain}
                              </div>
                          </div>
                      </dd>
                  </div>`
            : nothing}
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Basic-Auth")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">
                    <ak-status-label
                        type="info"
                        ?good=${provider.basicAuthEnabled}
                    ></ak-status-label>
                </div>
            </dd>
        </div>
    </dl>`;
}

const clientTypeToLabel = new Map<ClientTypeEnum, string>([
    [ClientTypeEnum.Confidential, msg("Confidential")],
    [ClientTypeEnum.Public, msg("Public")],
    [ClientTypeEnum.UnknownDefaultOpenApi, msg("Unknown type")],
]);

function renderOAuth2Overview(rawProvider: OneOfProvider) {
    const provider = rawProvider as OAuth2Provider;
    return html`
        <dl class="pf-c-description-list">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Name")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${provider.name}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Client type")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${provider.clientType ? clientTypeToLabel.get(provider.clientType) : ""}
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Client ID")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${provider.clientId}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Redirect URIs")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${provider.redirectUris}</div>
                </dd>
            </div>
        </dl>
    `;
}

function renderLDAPOverview(rawProvider: OneOfProvider) {
    const provider = rawProvider as LDAPProvider;
    return html` <dl class="pf-c-description-list pf-m-3-col-on-lg">
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Name")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.name}</div>
            </dd>
        </div>
        <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${msg("Base DN")}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${provider.baseDn}</div>
            </dd>
        </div>
    </dl>`;
}

export const providerRenderers = new Map([
    [ProviderModelEnum.SamlSamlprovider, renderSAMLOverview],
    [ProviderModelEnum.ScimScimprovider, renderSCIMOverview],
    [ProviderModelEnum.RadiusRadiusprovider, renderRadiusOverview],
    [ProviderModelEnum.RacRacprovider, renderRACOverview],
    [ProviderModelEnum.ProxyProxyprovider, renderProxyOverview],
    [ProviderModelEnum.Oauth2Oauth2provider, renderOAuth2Overview],
    [ProviderModelEnum.LdapLdapprovider, renderLDAPOverview],
]);
