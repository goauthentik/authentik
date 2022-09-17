import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { CSSResult, css } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFToggleGroup from "@patternfly/patternfly/components/ToggleGroup/toggle-group.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

import {
    CryptoApi,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    PropertymappingsApi,
    ProvidersApi,
    ProxyMode,
    ProxyProvider,
} from "@goauthentik/api";

@customElement("ak-provider-proxy-form")
export class ProxyProviderFormPage extends ModelForm<ProxyProvider, number> {
    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFToggleGroup,
            PFContent,
            PFList,
            PFSpacing,
            css`
                .pf-c-toggle-group {
                    justify-content: center;
                }
            `,
        );
    }

    loadInstance(pk: number): Promise<ProxyProvider> {
        return new ProvidersApi(DEFAULT_CONFIG)
            .providersProxyRetrieve({
                id: pk,
            })
            .then((provider) => {
                this.showHttpBasic = first(provider.basicAuthEnabled, true);
                this.mode = first(provider.mode, ProxyMode.Proxy);
                return provider;
            });
    }

    @property({ type: Boolean })
    showHttpBasic = true;

    @property({ attribute: false })
    mode: ProxyMode = ProxyMode.Proxy;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        } else {
            return msg("Successfully created provider.");
        }
    }

    send = (data: ProxyProvider): Promise<ProxyProvider> => {
        data.mode = this.mode;
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
    };

    renderHttpBasic(): TemplateResult {
        if (!this.showHttpBasic) {
            return html``;
        }
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
        return html` <div class="pf-c-toggle-group__item">
                <button
                    class="pf-c-toggle-group__button ${this.mode === ProxyMode.Proxy
                        ? "pf-m-selected"
                        : ""}"
                    type="button"
                    @click=${() => {
                        this.mode = ProxyMode.Proxy;
                    }}
                >
                    <span class="pf-c-toggle-group__text">${msg("Proxy")}</span>
                </button>
            </div>
            <div class="pf-c-divider pf-m-vertical" role="separator"></div>
            <div class="pf-c-toggle-group__item">
                <button
                    class="pf-c-toggle-group__button ${this.mode === ProxyMode.ForwardSingle
                        ? "pf-m-selected"
                        : ""}"
                    type="button"
                    @click=${() => {
                        this.mode = ProxyMode.ForwardSingle;
                    }}
                >
                    <span class="pf-c-toggle-group__text"
                        >${msg("Forward auth (single application)")}</span
                    >
                </button>
            </div>
            <div class="pf-c-divider pf-m-vertical" role="separator"></div>
            <div class="pf-c-toggle-group__item">
                <button
                    class="pf-c-toggle-group__button ${this.mode === ProxyMode.ForwardDomain
                        ? "pf-m-selected"
                        : ""}"
                    type="button"
                    @click=${() => {
                        this.mode = ProxyMode.ForwardDomain;
                    }}
                >
                    <span class="pf-c-toggle-group__text"
                        >${msg("Forward auth (domain level)")}</span
                    >
                </button>
            </div>`;
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
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.internalHostSslValidation, true)}
                            />
                            <label class="pf-c-check__label">
                                ${msg("Internal host SSL Validation")}
                            </label>
                        </div>
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
                label=${msg("Authorization flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <select class="pf-c-form-control">
                    ${until(
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesList({
                                ordering: "slug",
                                designation: FlowsInstancesListDesignationEnum.Authorization,
                            })
                            .then((flows) => {
                                return flows.results.map((flow) => {
                                    return html`<option
                                        value=${ifDefined(flow.pk)}
                                        ?selected=${this.instance?.authorizationFlow === flow.pk}
                                    >
                                        ${flow.name} (${flow.slug})
                                    </option>`;
                                });
                            }),
                        html`<option>${msg("Loading...")}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>

            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">
                    <div class="pf-c-toggle-group">${this.renderModeSelector()}</div>
                </div>
                <div class="pf-c-card__footer">${this.renderSettings()}</div>
            </div>
            <ak-form-element-horizontal label=${msg("Token validity")} name="tokenValidity">
                <input
                    type="text"
                    value="${first(this.instance?.tokenValidity, "hours=24")}"
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
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.certificate === undefined}>
                                ---------
                            </option>
                            ${until(
                                new CryptoApi(DEFAULT_CONFIG)
                                    .cryptoCertificatekeypairsList({
                                        ordering: "name",
                                        hasKey: true,
                                    })
                                    .then((keys) => {
                                        return keys.results.map((key) => {
                                            return html`<option
                                                value=${ifDefined(key.pk)}
                                                ?selected=${this.instance?.certificate === key.pk}
                                            >
                                                ${key.name}
                                            </option>`;
                                        });
                                    }),
                                html`<option
                                    value=${ifDefined(this.instance?.certificate || undefined)}
                                    ?selected=${this.instance?.certificate !== undefined}
                                >
                                    ${msg("Loading...")}
                                </option>`,
                            )}
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Scopes")} name="propertyMappings">
                        <select class="pf-c-form-control" multiple>
                            ${until(
                                new PropertymappingsApi(DEFAULT_CONFIG)
                                    .propertymappingsScopeList({
                                        ordering: "scope_name",
                                    })
                                    .then((scopes) => {
                                        return scopes.results
                                            .filter((scope) => {
                                                return !scope.managed?.startsWith(
                                                    "goauthentik.io/providers",
                                                );
                                            })
                                            .map((scope) => {
                                                const selected = (
                                                    this.instance?.propertyMappings || []
                                                ).some((su) => {
                                                    return su == scope.pk;
                                                });
                                                return html`<option
                                                    value=${ifDefined(scope.pk)}
                                                    ?selected=${selected}
                                                >
                                                    ${scope.name}
                                                </option>`;
                                            });
                                    }),
                                html`<option>${msg("Loading...")}</option>`,
                            )}
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

                    <ak-form-element-horizontal name="basicAuthEnabled">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.basicAuthEnabled, false)}
                                @change=${(ev: Event) => {
                                    const el = ev.target as HTMLInputElement;
                                    this.showHttpBasic = el.checked;
                                }}
                            />
                            <label class="pf-c-check__label">
                                ${msg("Set HTTP-Basic Authentication")}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Set a custom HTTP-Basic Authentication header based on values from authentik.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.renderHttpBasic()}
                </div>
            </ak-form-group>
        </form>`;
    }
}
