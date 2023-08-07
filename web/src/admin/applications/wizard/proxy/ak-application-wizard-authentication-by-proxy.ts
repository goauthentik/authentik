import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/components/ak-toggle-group";

import {
    FlowsInstancesListDesignationEnum,
    PaginatedOAuthSourceList,
    PaginatedScopeMappingList,
    PropertymappingsApi,
    ProxyMode,
    ProxyProvider,
    SourcesApi,
} from "@goauthentik/api";

import ApplicationWizardPageBase from "../ApplicationWizardPageBase";

@customElement("ak-application-wizard-authentication-by-proxy")
export class AkTypeProxyApplicationWizardPage extends ApplicationWizardPageBase {
    constructor() {
        super();
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsScopeList({ ordering: "scope_name" })
            .then((propertyMappings: PaginatedScopeMappingList) => {
                this.propertyMappings = propertyMappings;
            });

        new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthList({
                ordering: "name",
                hasJwks: true,
            })
            .then((oauthSources: PaginatedOAuthSourceList) => {
                this.oauthSources = oauthSources;
            });
    }

    handleChange(ev: InputEvent) {
        if (!ev.target) {
            console.warn(`Received event with no target: ${ev}`);
            return;
        }
        const target = ev.target as HTMLInputElement;
        const value = target.type === "checkbox" ? target.checked : target.value;
        this.dispatchWizardUpdate({
            provider: {
                ...this.wizard.provider,
                [target.name]: value,
            },
        });
    }

    propertyMappings?: PaginatedScopeMappingList;
    oauthSources?: PaginatedOAuthSourceList;

    @state()
    showHttpBasic = true;

    @state()
    mode: ProxyMode = ProxyMode.Proxy;

    get instance(): ProxyProvider | undefined {
        return this.wizard.provider as ProxyProvider;
    }

    renderHttpBasic(): TemplateResult {
        return html`<ak-text-input
                name="basicAuthUserAttribute"
                label=${msg("HTTP-Basic Username Key")}
                value="${ifDefined(this.instance?.basicAuthUserAttribute)}"
                help=${msg(
                    "User/Group Attribute used for the user part of the HTTP-Basic Header. If not set, the user's Email address is used.",
                )}
            >
            </ak-text-input>

            <ak-text-input
                name="basicAuthPasswordAttribute"
                label=${msg("HTTP-Basic Password Key")}
                value="${ifDefined(this.instance?.basicAuthPasswordAttribute)}"
                help=${msg(
                    "User/Group Attribute used for the password part of the HTTP-Basic Header.",
                )}
            >
            </ak-text-input>`;
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

    renderProxyModeProxy() {
        return html`<p class="pf-u-mb-xl">
                ${msg(
                    "This provider will behave like a transparent reverse-proxy, except requests must be authenticated. If your upstream application uses HTTPS, make sure to connect to the outpost using HTTPS as well.",
                )}
            </p>
            <ak-text-input
                name="externalHost"
                value=${ifDefined(this.instance?.externalHost)}
                required
                label=${msg("External host")}
                help=${msg(
                    "The external URL you'll access the application at. Include any non-standard port.",
                )}
            ></ak-text-input>
            <ak-text-input
                name="internalHost"
                value=${ifDefined(this.instance?.internalHost)}
                required
                label=${msg("Internal host")}
                help=${msg("Upstream host that the requests are forwarded to.")}
            ></ak-text-input>
            <ak-switch-input
                name="internalHostSslValidation"
                ?checked=${first(this.instance?.internalHostSslValidation, true)}
                label=${msg("Internal host SSL Validation")}
                help=${msg("Validate SSL Certificates of upstream servers.")}
            >
            </ak-switch-input>`;
    }

    renderProxyModeForwardSingle() {
        return html`<p class="pf-u-mb-xl">
                ${msg(
                    "Use this provider with nginx's auth_request or traefik's forwardAuth. Each application/domain needs its own provider. Additionally, on each domain, /outpost.goauthentik.io must be routed to the outpost (when using a manged outpost, this is done for you).",
                )}
            </p>
            <ak-text-input
                name="externalHost"
                value=${ifDefined(this.instance?.externalHost)}
                required
                label=${msg("External host")}
                help=${msg(
                    "The external URL you'll access the application at. Include any non-standard port.",
                )}
            ></ak-text-input>`;
    }

    renderProxyModeForwardDomain() {
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
            <ak-text-input
                name="externalHost"
                value=${first(this.instance?.externalHost, window.location.origin)}
                required
                label=${msg("Authentication URL")}
                help=${msg(
                    "The external URL you'll authenticate at. The authentik core server should be reachable under this URL.",
                )}
            ></ak-text-input>
            <ak-text-input
                name="cookieDomain"
                value=${ifDefined(this.instance?.cookieDomain)}
                required
                label=${msg("Cookie domain")}
                help=${msg(
                    "Set this to the domain you wish the authentication to be valid for. Must be a parent domain of the URL above. If you're running applications as app1.domain.tld, app2.domain.tld, set this to 'domain.tld'.",
                )}
            ></ak-text-input>`;
    }

    renderSettings() {
        switch (this.mode) {
            case ProxyMode.Proxy:
                return this.renderProxyModeProxy();
            case ProxyMode.ForwardSingle:
                return this.renderProxyModeForwardSingle();
            case ProxyMode.ForwardDomain:
                return this.renderProxyModeForwardDomain();
            case ProxyMode.UnknownDefaultOpenApi:
                return html`<p>${msg("Unknown proxy mode")}</p>`;
        }
    }

    render() {
        return html`<form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                value=${ifDefined(this.instance?.name)}
                required
                label=${msg("Name")}
            ></ak-text-input>
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
            <ak-text-input
                name="accessTokenValidity"
                value=${first(this.instance?.accessTokenValidity, "hours=24")}
                label=${msg("Token validity")}
                help=${msg("Configure how long tokens are valid for.")}
            ></ak-text-input>

            <ak-form-group>
                <span slot="header">${msg("Advanced protocol settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Certificate")} name="certificate">
                        <ak-crypto-certificate-search
                            certificate=${ifDefined(this.instance?.certificate ?? undefined)}
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
                    <ak-textarea-input
                        name="skipPathRegex"
                        label=${this.mode === ProxyMode.ForwardDomain
                            ? msg("Unauthenticated URLs")
                            : msg("Unauthenticated Paths")}
                        value=${ifDefined(this.instance?.skipPathRegex)}
                        .bighelp=${html` <p class="pf-c-form__helper-text">
                                ${msg(
                                    "Regular expressions for which authentication is not required. Each new line is interpreted as a new expression.",
                                )}
                            </p>
                            <p class="pf-c-form__helper-text">
                                ${msg(
                                    "When using proxy or forward auth (single application) mode, the requested URL Path is checked against the regular expressions. When using forward auth (domain mode), the full requested URL including scheme and host is matched against the regular expressions.",
                                )}
                            </p>`}
                    >
                    </ak-textarea-input>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header">${msg("Authentication settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-switch-input
                        name="interceptHeaderAuth"
                        ?checked=${first(this.instance?.interceptHeaderAuth, true)}
                        label=${msg("Intercept header authentication")}
                        help=${msg(
                            "When enabled, authentik will intercept the Authorization header to authenticate the request.",
                        )}
                    ></ak-switch-input>

                    <ak-switch-input
                        name="basicAuthEnabled"
                        ?checked=${first(this.instance?.basicAuthEnabled, false)}
                        @change=${(ev: Event) => {
                            const el = ev.target as HTMLInputElement;
                            this.showHttpBasic = el.checked;
                        }}
                        label=${msg("Send HTTP-Basic Authentication")}
                        help=${msg(
                            "Send a custom HTTP-Basic Authentication header based on values from authentik.",
                        )}
                    ></ak-switch-input>

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

export default AkTypeProxyApplicationWizardPage;
