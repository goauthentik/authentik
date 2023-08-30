import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

import {
    FlowsInstancesListDesignationEnum,
    PaginatedOAuthSourceList,
    PaginatedScopeMappingList,
    PropertymappingsApi,
    ProvidersApi,
    ProxyMode,
    ProxyProvider,
    SourcesApi,
} from "@goauthentik/api";

@customElement("ak-provider-proxy-form")
export class ProxyProviderFormPage extends ModelForm<ProxyProvider, number> {
    static get styles(): CSSResult[] {
        return [...super.styles, PFContent, PFList, PFSpacing];
    }

    async loadInstance(pk: number): Promise<ProxyProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersProxyRetrieve({
            id: pk,
        });
        this.showHttpBasic = first(provider.basicAuthEnabled, true);
        this.mode = first(provider.mode, ProxyMode.Proxy);
        return provider;
    }

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsScopeList({
            ordering: "scope_name",
        });
        this.oauthSources = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthList({
            ordering: "name",
            hasJwks: true,
        });
    }

    propertyMappings?: PaginatedScopeMappingList;
    oauthSources?: PaginatedOAuthSourceList;

    @state()
    showHttpBasic = true;

    @state()
    mode: ProxyMode = ProxyMode.Proxy;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        } else {
            return msg("Successfully created provider.");
        }
    }

    async send(data: ProxyProvider): Promise<ProxyProvider> {
        data.mode = this.mode;
        if (this.mode !== ProxyMode.ForwardDomain) {
            data.cookieDomain = "";
        }
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersProxyUpdate({
                id: this.instance.pk || 0,
                proxyProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersProxyCreate({
                proxyProviderRequest: data,
            });
        }
    }

    renderHttpBasic(): TemplateResult {
        return html`<ak-form-element-horizontal
                label=${msg("HTTP-Basic Username Key")}
                name="basicAuthUserAttribute"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.basicAuthUserAttribute)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "User/Group Attribute used for the user part of the HTTP-Basic Header. If not set, the user's Email address is used.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("HTTP-Basic Password Key")}
                name="basicAuthPasswordAttribute"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.basicAuthPasswordAttribute)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "User/Group Attribute used for the password part of the HTTP-Basic Header.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }

    renderModeSelector(): TemplateResult {
        const setMode = (ev: CustomEvent<{ value: ProxyMode }>) => {
            this.mode = ev.detail.value;
        };

        // prettier-ignore
        return html`
            <ak-toggle-group value=${this.mode} @ak-toggle=${setMode}>
                <option value=${ProxyMode.Proxy}>${msg("Proxy")}</option>
                <option value=${ProxyMode.ForwardSingle}>${msg("Forward auth (single application)")}</option>
                <option value=${ProxyMode.ForwardDomain}>${msg("Forward auth (domain level)")}</option>
            </ak-toggle-group>
        `;
    }

    renderSettings(): TemplateResult {
        switch (this.mode) {
            case ProxyMode.Proxy:
                return html`<p class="pf-u-mb-xl">
                        ${msg(
                            "This provider will behave like a transparent reverse-proxy, except requests must be authenticated. If your upstream application uses HTTPS, make sure to connect to the outpost using HTTPS as well.",
                        )}
                    </p>
                    <ak-form-element-horizontal
                        label=${msg("External host")}
                        ?required=${true}
                        name="externalHost"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.externalHost)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The external URL you'll access the application at. Include any non-standard port.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Internal host")}
                        ?required=${true}
                        name="internalHost"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.internalHost)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Upstream host that the requests are forwarded to.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="internalHostSslValidation">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.internalHostSslValidation, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Internal host SSL Validation")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Validate SSL Certificates of upstream servers.")}
                        </p>
                    </ak-form-element-horizontal>`;
            case ProxyMode.ForwardSingle:
                return html`<p class="pf-u-mb-xl">
                        ${msg(
                            "Use this provider with nginx's auth_request or traefik's forwardAuth. Each application/domain needs its own provider. Additionally, on each domain, /outpost.goauthentik.io must be routed to the outpost (when using a manged outpost, this is done for you).",
                        )}
                    </p>
                    <ak-form-element-horizontal
                        label=${msg("External host")}
                        ?required=${true}
                        name="externalHost"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.externalHost)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The external URL you'll access the application at. Include any non-standard port.",
                            )}
                        </p>
                    </ak-form-element-horizontal>`;
            case ProxyMode.ForwardDomain:
                return html`<p class="pf-u-mb-xl">
                        ${msg(
                            "Use this provider with nginx's auth_request or traefik's forwardAuth. Only a single provider is required per root domain. You can't do per-application authorization, but you don't have to create a provider for each application.",
                        )}
                    </p>
                    <div class="pf-u-mb-xl">
                        ${msg("An example setup can look like this:")}
                        <ul class="pf-c-list">
                            <li>${msg("authentik running on auth.example.com")}</li>
                            <li>${msg("app1 running on app1.example.com")}</li>
                        </ul>
                        ${msg(
                            "In this case, you'd set the Authentication URL to auth.example.com and Cookie domain to example.com.",
                        )}
                    </div>
                    <ak-form-element-horizontal
                        label=${msg("Authentication URL")}
                        ?required=${true}
                        name="externalHost"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.externalHost, window.location.origin)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The external URL you'll authenticate at. The authentik core server should be reachable under this URL.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Cookie domain")}
                        name="cookieDomain"
                        ?required=${true}
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.cookieDomain)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Set this to the domain you wish the authentication to be valid for. Must be a parent domain of the URL above. If you're running applications as app1.domain.tld, app2.domain.tld, set this to 'domain.tld'.",
                            )}
                        </p>
                    </ak-form-element-horizontal>`;
            case ProxyMode.UnknownDefaultOpenApi:
                return html`<p>${msg("Unknown proxy mode")}</p>`;
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                ?required=${false}
                name="authenticationFlow"
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${this.instance?.authenticationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when a user access this provider and is not authenticated.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authorization flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authorization}
                    .currentFlow=${this.instance?.authorizationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>

            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">${this.renderModeSelector()}</div>
                <div class="pf-c-card__footer">${this.renderSettings()}</div>
            </div>
            <ak-form-element-horizontal label=${msg("Token validity")} name="accessTokenValidity">
                <input
                    type="text"
                    value="${first(this.instance?.accessTokenValidity, "hours=24")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Configure how long tokens are valid for.")}
                </p>
                <ak-utils-time-delta-help></ak-utils-time-delta-help>
            </ak-form-element-horizontal>

            <ak-form-group>
                <span slot="header">${msg("Advanced protocol settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Certificate")} name="certificate">
                        <ak-crypto-certificate-search
                            certificate=${this.instance?.certificate}
                        ></ak-crypto-certificate-search>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Additional scopes")}
                        name="propertyMappings"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results
                                .filter((scope) => {
                                    return !scope.managed?.startsWith("goauthentik.io/providers");
                                })
                                .map((scope) => {
                                    const selected = (this.instance?.propertyMappings || []).some(
                                        (su) => {
                                            return su == scope.pk;
                                        },
                                    );
                                    return html`<option
                                        value=${ifDefined(scope.pk)}
                                        ?selected=${selected}
                                    >
                                        ${scope.name}
                                    </option>`;
                                })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Additional scope mappings, which are passed to the proxy.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label="${this.mode === ProxyMode.ForwardDomain
                            ? msg("Unauthenticated URLs")
                            : msg("Unauthenticated Paths")}"
                        name="skipPathRegex"
                    >
                        <textarea class="pf-c-form-control">
${this.instance?.skipPathRegex}</textarea
                        >
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Regular expressions for which authentication is not required. Each new line is interpreted as a new expression.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When using proxy or forward auth (single application) mode, the requested URL Path is checked against the regular expressions. When using forward auth (domain mode), the full requested URL including scheme and host is matched against the regular expressions.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header">${msg("Authentication settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="interceptHeaderAuth">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.interceptHeaderAuth, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Intercept header authentication")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When enabled, authentik will intercept the Authorization header to authenticate the request.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="basicAuthEnabled">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.basicAuthEnabled, false)}
                                @change=${(ev: Event) => {
                                    const el = ev.target as HTMLInputElement;
                                    this.showHttpBasic = el.checked;
                                }}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Send HTTP-Basic Authentication")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Send a custom HTTP-Basic Authentication header based on values from authentik.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.showHttpBasic ? this.renderHttpBasic() : html``}
                    <ak-form-element-horizontal
                        label=${msg("Trusted OIDC Sources")}
                        name="jwksSources"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.oauthSources?.results.map((source) => {
                                const selected = (this.instance?.jwksSources || []).some((su) => {
                                    return su == source.pk;
                                });
                                return html`<option value=${source.pk} ?selected=${selected}>
                                    ${source.name} (${source.slug})
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
