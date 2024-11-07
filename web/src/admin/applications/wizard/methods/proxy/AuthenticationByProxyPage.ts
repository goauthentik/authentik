import "@goauthentik/admin/applications/wizard/ak-wizard-title";
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
import { TemplateResult, html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    PaginatedOAuthSourceList,
    PaginatedScopeMappingList,
    ProxyMode,
    ProxyProvider,
    SourcesApi,
} from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

type MaybeTemplateResult = TemplateResult | typeof nothing;

export class AkTypeProxyApplicationWizardPage extends BaseProviderPanel {
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

    get instance(): ProxyProvider | undefined {
        return this.wizard.provider as ProxyProvider;
    }

    renderModeDescription(): MaybeTemplateResult {
        return nothing;
    }

    renderProxyMode(): TemplateResult {
        throw new Error("Must be implemented in a child class.");
    }

    renderHttpBasic() {
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

    render() {
        const errors = this.wizard.errors.provider;

        return html` <ak-wizard-title>${msg("Configure Proxy Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${this.renderModeDescription()}
                <ak-text-input
                    name="name"
                    value=${ifDefined(this.instance?.name)}
                    required
                    .errorMessages=${errors?.name ?? []}
                    label=${msg("Name")}
                ></ak-text-input>

                <ak-form-element-horizontal
                    label=${msg("Authorization flow")}
                    required
                    name="authorizationFlow"
                    .errorMessages=${errors?.authorizationFlow ?? []}
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

                ${this.renderProxyMode()}

                <ak-text-input
                    name="accessTokenValidity"
                    value=${first(this.instance?.accessTokenValidity, "hours=24")}
                    label=${msg("Token validity")}
                    help=${msg("Configure how long tokens are valid for.")}
                    .errorMessages=${errors?.accessTokenValidity ?? []}
                ></ak-text-input>

                <ak-form-group>
                    <span slot="header">${msg("Advanced protocol settings")}</span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal
                            label=${msg("Certificate")}
                            name="certificate"
                            .errorMessages=${errors?.certificate ?? []}
                        >
                            <ak-crypto-certificate-search
                                certificate=${ifDefined(this.instance?.certificate ?? undefined)}
                            ></ak-crypto-certificate-search>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${msg("Additional scopes")}
                            name="propertyMappings"
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${proxyPropertyMappingsProvider}
                                .selector=${makeProxyPropertyMappingsSelector(
                                    this.instance?.propertyMappings,
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
                            value=${ifDefined(this.instance?.skipPathRegex)}
                            .errorMessages=${errors?.skipPathRegex ?? []}
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
                            name="jwtFederationSources"
                            .errorMessages=${errors?.jwtFederationSources ?? []}
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${oauth2SourcesProvider}
                                .selector=${makeSourceSelector(this.instance?.jwtFederationSources)}
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
            </form>`;
    }
}

export default AkTypeProxyApplicationWizardPage;
