import {
    makeSourceSelector,
    oauth2SourcesProvider,
} from "@goauthentik/admin/providers/oauth2/OAuth2Sources.js";
import {
    makeProxyPropertyMappingsSelector,
    proxyPropertyMappingsProvider,
} from "@goauthentik/admin/providers/proxy/ProxyProviderPropertyMappings.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { state } from "@lit/reactive-element/decorators.js";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    PaginatedOAuthSourceList,
    PaginatedScopeMappingList,
    ProxyMode,
    ProxyProvider,
    SourcesApi,
} from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm";

export class ApplicationWizardProxyProviderForm extends ApplicationWizardProviderForm<ProxyProvider> {
    constructor() {
        super();
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthList({
                ordering: "name",
                hasJwks: true,
            })
            .then((oauthSources: PaginatedOAuthSourceList) => {
                this.oauthSources = oauthSources;
            });
    }

    propertyMappings?: PaginatedScopeMappingList;
    oauthSources?: PaginatedOAuthSourceList;

    @state()
    showHttpBasic = true;

    @state()
    mode: ProxyMode = ProxyMode.Proxy;

    label = msg("Configure Proxy Provider");

    renderProxyMode(_provider: ProxyProvider) {
        throw new Error("Must be implemented in a child class.");
    }

    renderModeDescription() {
        throw new Error("Must be implemented in a child class.");
    }

    renderHttpBasic(provider: ProxyProvider) {
        return html`<ak-text-input
                name="basicAuthUserAttribute"
                label=${msg("HTTP-Basic Username Key")}
                value="${ifDefined(provider.basicAuthUserAttribute)}"
                help=${msg(
                    "User/Group Attribute used for the user part of the HTTP-Basic Header. If not set, the user's Email address is used.",
                )}
            >
            </ak-text-input>

            <ak-text-input
                name="basicAuthPasswordAttribute"
                label=${msg("HTTP-Basic Password Key")}
                value="${ifDefined(provider.basicAuthPasswordAttribute)}"
                help=${msg(
                    "User/Group Attribute used for the password part of the HTTP-Basic Header.",
                )}
            >
            </ak-text-input>`;
    }

    renderForm(provider: ProxyProvider) {
        return html`
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${this.renderModeDescription()}
                <ak-text-input
                    name="name"
                    value=${ifDefined(provider.name)}
                    required
                    .errorMessages=${this.errorMessages("name")}
                    label=${msg("Name")}
                ></ak-text-input>

                <ak-form-element-horizontal
                    label=${msg("Authorization flow")}
                    required
                    name="authorizationFlow"
                    .errorMessages=${this.errorMessages("authorizationFlow")}
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authorization}
                        .currentFlow=${provider.authorizationFlow}
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when authorizing this provider.")}
                    </p>
                </ak-form-element-horizontal>

                ${this.renderProxyMode(provider)}

                <ak-text-input
                    name="accessTokenValidity"
                    value=${first(provider.accessTokenValidity, "hours=24")}
                    label=${msg("Token validity")}
                    help=${msg("Configure how long tokens are valid for.")}
                    .errorMessages=${this.errorMessages("accessTokenValidity")}
                ></ak-text-input>

                <ak-form-group>
                    <span slot="header">${msg("Advanced protocol settings")}</span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal
                            label=${msg("Certificate")}
                            name="certificate"
                            .errorMessages=${this.errorMessages("certificate")}
                        >
                            <ak-crypto-certificate-search
                                certificate=${ifDefined(provider.certificate ?? undefined)}
                            ></ak-crypto-certificate-search>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${msg("Additional scopes")}
                            name="propertyMappings"
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${proxyPropertyMappingsProvider}
                                .selector=${makeProxyPropertyMappingsSelector(
                                    provider.propertyMappings,
                                )}
                                available-label="${msg("Available Scopes")}"
                                selected-label="${msg("Selected Scopes")}"
                            ></ak-dual-select-dynamic-selected>
                            <p class="pf-c-form__helper-text">
                                ${msg("Additional scope mappings, which are passed to the proxy.")}
                            </p>
                        </ak-form-element-horizontal>

                        <ak-textarea-input
                            name="skipPathRegex"
                            label=${this.mode === ProxyMode.ForwardDomain
                                ? msg("Unauthenticated URLs")
                                : msg("Unauthenticated Paths")}
                            value=${ifDefined(provider.skipPathRegex)}
                            .errorMessages=${this.errorMessages("skipPathRegex")}
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
                    <span slot="header"> ${msg("Advanced flow settings")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal
                            name="authenticationFlow"
                            label=${msg("Authentication flow")}
                        >
                            <ak-flow-search
                                flowType=${FlowsInstancesListDesignationEnum.Authentication}
                                .currentFlow=${this.instance?.authenticationFlow}
                            ></ak-flow-search>
                            <p class="pf-c-form__helper-text">
                                ${msg(
                                    "Flow used when a user access this provider and is not authenticated.",
                                )}
                            </p>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${msg("Invalidation flow")}
                            name="invalidationFlow"
                            required
                        >
                            <ak-flow-search
                                flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                                .currentFlow=${this.instance?.invalidationFlow}
                                defaultFlowSlug="default-provider-invalidation-flow"
                                required
                            ></ak-flow-search>
                            <p class="pf-c-form__helper-text">
                                ${msg("Flow used when logging out of this provider.")}
                            </p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
                <ak-form-group>
                    <span slot="header">${msg("Authentication settings")}</span>
                    <div slot="body" class="pf-c-form">
                        <ak-switch-input
                            name="interceptHeaderAuth"
                            ?checked=${first(provider.interceptHeaderAuth, true)}
                            label=${msg("Intercept header authentication")}
                            help=${msg(
                                "When enabled, authentik will intercept the Authorization header to authenticate the request.",
                            )}
                        ></ak-switch-input>

                        <ak-switch-input
                            name="basicAuthEnabled"
                            ?checked=${first(provider.basicAuthEnabled, false)}
                            @change=${(ev: Event) => {
                                const el = ev.target as HTMLInputElement;
                                this.showHttpBasic = el.checked;
                            }}
                            label=${msg("Send HTTP-Basic Authentication")}
                            help=${msg(
                                "Send a custom HTTP-Basic Authentication header based on values from authentik.",
                            )}
                        ></ak-switch-input>

                        ${this.showHttpBasic ? this.renderHttpBasic(provider) : nothing}

                        <ak-form-element-horizontal
                            label=${msg("Trusted OIDC Sources")}
                            name="jwksSources"
                            .errorMessages=${this.errorMessages("jwksSources")}
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${oauth2SourcesProvider}
                                .selector=${makeSourceSelector(provider.jwksSources)}
                                available-label=${msg("Available Sources")}
                                selected-label=${msg("Selected Sources")}
                            ></ak-dual-select-dynamic-selected>
                            <p class="pf-c-form__helper-text">
                                ${msg(
                                    "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                                )}
                            </p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>
        `;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("Proxy Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as ProxyProvider);
    }
}
