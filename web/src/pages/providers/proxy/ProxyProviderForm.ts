import {
    CryptoApi,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    ProvidersApi,
    ProxyMode,
    ProxyProvider,
} from "@goauthentik/api";
import { t } from "@lingui/macro";
import { css, CSSResult, customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ModelForm } from "../../../elements/forms/ModelForm";
import PFToggleGroup from "@patternfly/patternfly/components/ToggleGroup/toggle-group.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";

@customElement("ak-provider-proxy-form")
export class ProxyProviderFormPage extends ModelForm<ProxyProvider, number> {
    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFToggleGroup,
            PFContent,
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
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
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
                label=${t`HTTP-Basic Username Key`}
                name="basicAuthUserAttribute"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.basicAuthUserAttribute)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`User/Group Attribute used for the user part of the HTTP-Basic Header. If not set, the user's Email address is used.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`HTTP-Basic Password Key`}
                name="basicAuthPasswordAttribute"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.basicAuthPasswordAttribute)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`User/Group Attribute used for the password part of the HTTP-Basic Header.`}
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
                    <span class="pf-c-toggle-group__text">${t`Proxy`}</span>
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
                        >${t`Forward auth (single application)`}</span
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
                    <span class="pf-c-toggle-group__text">${t`Forward auth (domain level)`}</span>
                </button>
            </div>`;
    }

    renderSettings(): TemplateResult {
        switch (this.mode) {
            case ProxyMode.Proxy:
                return html` <p class="pf-u-mb-xl">
                        ${t`This provider will behave like a transparent reverse-proxy, except requests must be authenticated. If your upstream application uses HTTPS, make sure to connect to the outpost using HTTPS as well.`}
                    </p>
                    <ak-form-element-horizontal
                        label=${t`External host`}
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
                            ${t`The external URL you'll access the application at. Include any non-standard port.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Internal host`}
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
                            ${t`Upstream host that the requests are forwarded to.`}
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
                                ${t`Internal host SSL Validation`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${t`Validate SSL Certificates of upstream servers.`}
                        </p>
                    </ak-form-element-horizontal>`;
            case ProxyMode.ForwardSingle:
                return html` <p class="pf-u-mb-xl">
                        ${t`Use this provider with nginx's auth_request or traefik's forwardAuth. Each application/domain needs its own provider. Additionally, on each domain, /akprox must be routed to the outpost (when using a manged outpost, this is done for you).`}
                    </p>
                    <ak-form-element-horizontal
                        label=${t`External host`}
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
                            ${t`The external URL you'll access the application at. Include any non-standard port.`}
                        </p>
                    </ak-form-element-horizontal>`;
            case ProxyMode.ForwardDomain:
                return html` <p class="pf-u-mb-xl">
                        ${t`Use this provider with nginx's auth_request or traefik's forwardAuth. Only a single provider is required per root domain. You can't do per-application authorization, but you don't have to create a provider for each application.`}
                    </p>
                    <ak-form-element-horizontal
                        label=${t`External host`}
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
                            ${t`The external URL you'll authenticate at. Can be the same domain as authentik.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Cookie domain`} name="cookieDomain">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.cookieDomain)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Optionally set this to your parent domain, if you want authentication and authorization to happen on a domain level. If you're running applications as app1.domain.tld, app2.domain.tld, set this to 'domain.tld'.`}
                        </p>
                    </ak-form-element-horizontal>`;
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <select class="pf-c-form-control">
                    ${until(
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesList({
                                ordering: "pk",
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
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used when authorizing this provider.`}
                </p>
            </ak-form-element-horizontal>

            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">
                    <div class="pf-c-toggle-group">${this.renderModeSelector()}</div>
                </div>
                <div class="pf-c-card__footer">${this.renderSettings()}</div>
            </div>

            <ak-form-group>
                <span slot="header"> ${t`Advanced protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Certificate`} name="certificate">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.certificate === undefined}>
                                ---------
                            </option>
                            ${until(
                                new CryptoApi(DEFAULT_CONFIG)
                                    .cryptoCertificatekeypairsList({
                                        ordering: "pk",
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
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal label=${t`Skip path regex`} name="skipPathRegex">
                        <textarea class="pf-c-form-control">
${this.instance?.skipPathRegex}</textarea
                        >
                        <p class="pf-c-form__helper-text">
                            ${t`Regular expressions for which authentication is not required. Each new line is interpreted as a new Regular Expression.`}
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
                                ${t`Set HTTP-Basic Authentication`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${t`Set a custom HTTP-Basic Authentication header based on values from authentik.`}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.renderHttpBasic()}
                </div>
            </ak-form-group>
        </form>`;
    }
}
