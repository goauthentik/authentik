import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-toggle-group";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";

import { propertyMappingsProvider, propertyMappingsSelector } from "./ProxyProviderFormHelpers.js";

import {
    oauth2ProviderSelector,
    oauth2ProvidersProvider,
} from "#admin/providers/oauth2/OAuth2ProviderForm";
import {
    oauth2SourcesProvider,
    oauth2SourcesSelector,
} from "#admin/providers/oauth2/OAuth2Sources";

import {
    FlowsInstancesListDesignationEnum,
    ProxyMode,
    ProxyProvider,
    ValidationError,
} from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type ProxyModeValue = { value: ProxyMode };
export type SetMode = (ev: CustomEvent<ProxyModeValue>) => void;
export type SetShowHttpBasic = (ev: Event) => void;

export interface ProxyModeExtraArgs {
    mode: ProxyMode;
    onSetMode: SetMode;
    showHttpBasic: boolean;
    onSetShowHttpBasic: SetShowHttpBasic;
}

function renderHttpBasic(provider: Partial<ProxyProvider>) {
    return html`<ak-text-input
            name="basicAuthUserAttribute"
            label=${msg("HTTP-Basic Username Key")}
            value="${ifDefined(provider?.basicAuthUserAttribute)}"
            help=${msg(
                "User/Group Attribute used for the user part of the HTTP-Basic Header. If not set, the user's Email address is used.",
            )}
            input-hint="code"
        >
        </ak-text-input>

        <ak-text-input
            name="basicAuthPasswordAttribute"
            label=${msg("HTTP-Basic Password Key")}
            value="${ifDefined(provider?.basicAuthPasswordAttribute)}"
            help=${msg("User/Group Attribute used for the password part of the HTTP-Basic Header.")}
            input-hint="code"
        >
        </ak-text-input>`;
}

function renderModeSelector(mode: ProxyMode, onSet: SetMode) {
    // prettier-ignore
    return html` <ak-toggle-group
        value=${mode}
        @ak-toggle=${onSet}
        data-ouid-component-name="proxy-type-toggle"
    >
        <option value=${ProxyMode.Proxy}>${msg("Proxy")}</option>
        <option value=${ProxyMode.ForwardSingle}>${msg("Forward auth (single application)")}</option>
        <option value=${ProxyMode.ForwardDomain}>${msg("Forward auth (domain level)")}</option>
    </ak-toggle-group>`;
}

function renderProxySettings(provider: Partial<ProxyProvider>, errors?: ValidationError) {
    return html`<p class="pf-u-mb-xl">
            ${msg(
                "This provider will behave like a transparent reverse-proxy, except requests must be authenticated. If your upstream application uses HTTPS, make sure to connect to the outpost using HTTPS as well.",
            )}
        </p>
        <ak-text-input
            name="externalHost"
            label=${msg("External host")}
            value="${ifDefined(provider?.externalHost)}"
            required
            .errorMessages=${errors?.externalHost}
            help=${msg(
                "The external URL you'll access the application at. Include any non-standard port.",
            )}
            input-hint="code"
        ></ak-text-input>
        <ak-text-input
            name="internalHost"
            label=${msg("Internal host")}
            value="${ifDefined(provider?.internalHost)}"
            required
            .errorMessages=${errors?.internalHost}
            help=${msg("Upstream host that the requests are forwarded to.")}
            input-hint="code"
        ></ak-text-input>

        <ak-switch-input
            name="internalHostSslValidation"
            label=${msg("Internal host SSL Validation")}
            ?checked=${provider?.internalHostSslValidation ?? true}
            help=${msg("Validate SSL Certificates of upstream servers.")}
        >
        </ak-switch-input>`;
}

function renderForwardSingleSettings(provider: Partial<ProxyProvider>, errors?: ValidationError) {
    return html`<p class="pf-u-mb-xl">
            ${msg(
                "Use this provider with nginx's auth_request or traefik's forwardAuth. Each application/domain needs its own provider. Additionally, on each domain, /outpost.goauthentik.io must be routed to the outpost (when using a managed outpost, this is done for you).",
            )}
        </p>
        <ak-text-input
            name="externalHost"
            label=${msg("External host")}
            value="${ifDefined(provider?.externalHost)}"
            required
            .errorMessages=${errors?.externalHost}
            help=${msg(
                "The external URL you'll access the application at. Include any non-standard port.",
            )}
            input-hint="code"
        ></ak-text-input>`;
}

function renderForwardDomainSettings(provider: Partial<ProxyProvider>, errors?: ValidationError) {
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
            label=${msg("Authentication URL")}
            value="${provider?.externalHost ?? window.location.origin}"
            required
            .errorMessages=${errors?.externalHost}
            help=${msg(
                "The external URL you'll authenticate at. The authentik core server should be reachable under this URL.",
            )}
        ></ak-text-input>

        <ak-text-input
            label=${msg("Cookie domain")}
            name="cookieDomain"
            value="${ifDefined(provider?.cookieDomain)}"
            required
            .errorMessages=${errors?.cookieDomain}
            help=${msg(
                "Set this to the domain you wish the authentication to be valid for. Must be a parent domain of the URL above. If you're running applications as app1.domain.tld, app2.domain.tld, set this to 'domain.tld'.",
            )}
        ></ak-text-input> `;
}

type StrictProxyMode = Omit<ProxyMode, "11184809">;

function renderSettings(provider: Partial<ProxyProvider>, mode: ProxyMode) {
    return match(mode as StrictProxyMode)
        .with(ProxyMode.Proxy, () => renderProxySettings(provider))
        .with(ProxyMode.ForwardSingle, () => renderForwardSingleSettings(provider))
        .with(ProxyMode.ForwardDomain, () => renderForwardDomainSettings(provider))
        .otherwise(() => {
            throw new Error("Unrecognized proxy mode");
        });
}

export function renderForm(
    provider: Partial<ProxyProvider> = {},
    errors: ValidationError = {},
    args: ProxyModeExtraArgs,
) {
    const { mode, onSetMode, showHttpBasic, onSetShowHttpBasic } = args;

    return html`
        <ak-text-input
            name="name"
            value=${ifDefined(provider?.name)}
            label=${msg("Name")}
            .errorMessages=${errors?.name}
            required
        ></ak-text-input>

        <ak-form-element-horizontal
            label=${msg("Authorization flow")}
            required
            name="authorizationFlow"
        >
            <ak-flow-search
                flowType=${FlowsInstancesListDesignationEnum.Authorization}
                .currentFlow=${provider?.authorizationFlow}
                required
            ></ak-flow-search>
            <p class="pf-c-form__helper-text">
                ${msg("Flow used when authorizing this provider.")}
            </p>
        </ak-form-element-horizontal>

        <div class="pf-c-card pf-m-selectable pf-m-selected">
            <div class="pf-c-card__body">${renderModeSelector(mode, onSetMode)}</div>
            <div class="pf-c-card__footer">${renderSettings(provider, mode)}</div>
        </div>

        <ak-text-input
            label=${msg("Token validity")}
            name="accessTokenValidity"
            value="${provider?.accessTokenValidity ?? "hours=24"}"
            .errorMessages=${errors?.accessTokenValidity}
            required
            .help=${msg("Configure how long tokens are valid for.")}
            input-hint="code"
        ></ak-text-input>

        <ak-form-group label="${msg("Advanced protocol settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("Certificate")} name="certificate">
                    <ak-crypto-certificate-search
                        .certificate=${provider?.certificate}
                    ></ak-crypto-certificate-search>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Additional scopes")}
                    name="propertyMappings"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(provider?.propertyMappings)}
                        available-label="${msg("Available Scopes")}"
                        selected-label="${msg("Selected Scopes")}"
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg("Additional scope mappings, which are passed to the proxy.")}
                    </p>
                </ak-form-element-horizontal>

                <ak-form-element-horizontal
                    label="${mode === ProxyMode.ForwardDomain
                        ? msg("Unauthenticated URLs")
                        : msg("Unauthenticated Paths")}"
                    name="skipPathRegex"
                >
                    <textarea class="pf-c-form-control pf-m-monospace">
${provider?.skipPathRegex}</textarea
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
        <ak-form-group label="${msg("Authentication settings")}">
            <div class="pf-c-form">
                <ak-switch-input
                    name="interceptHeaderAuth"
                    label=${msg("Intercept header authentication")}
                    ?checked=${provider?.interceptHeaderAuth ?? true}
                    help=${msg(
                        "When enabled, authentik will intercept the Authorization header to authenticate the request.",
                    )}
                >
                </ak-switch-input>

                <ak-switch-input
                    name="basicAuthEnabled"
                    label=${msg("Send HTTP-Basic Authentication")}
                    ?checked=${provider?.basicAuthEnabled ?? false}
                    help=${msg(
                        "Send a custom HTTP-Basic Authentication header based on values from authentik.",
                    )}
                    @change=${onSetShowHttpBasic}
                >
                </ak-switch-input>

                ${showHttpBasic ? renderHttpBasic(provider) : nothing}
                <ak-form-element-horizontal
                    label=${msg("Federated OIDC Sources")}
                    name="jwtFederationSources"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${oauth2SourcesProvider}
                        .selector=${oauth2SourcesSelector(provider?.jwtFederationSources)}
                        available-label=${msg("Available Sources")}
                        selected-label=${msg("Selected Sources")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Federated OIDC Providers")}
                    name="jwtFederationProviders"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${oauth2ProvidersProvider}
                        .selector=${oauth2ProviderSelector(provider?.jwtFederationProviders)}
                        available-label=${msg("Available Providers")}
                        selected-label=${msg("Selected Providers")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "JWTs signed by the selected providers can be used to authenticate to this provider.",
                        )}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Advanced flow settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Authentication flow")}
                    name="authenticationFlow"
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authentication}
                        .currentFlow=${provider?.authenticationFlow}
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
                        .currentFlow=${provider?.invalidationFlow}
                        defaultFlowSlug="default-provider-invalidation-flow"
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when logging out of this provider.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>
    `;
}
