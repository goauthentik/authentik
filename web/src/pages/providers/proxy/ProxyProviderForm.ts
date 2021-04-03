import { CryptoApi, FlowDesignationEnum, FlowsApi, ProvidersApi, ProxyProvider } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";

@customElement("ak-provider-proxy-form")
export class ProxyProviderFormPage extends Form<ProxyProvider> {

    set providerUUID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG).providersProxyRead({
            id: value,
        }).then(provider => {
            this.provider = provider;
            this.showHttpBasic = first(provider.basicAuthEnabled, true);
        });
    }

    @property({attribute: false})
    provider?: ProxyProvider;

    @property({type: Boolean})
    showHttpBasic = true;

    getSuccessMessage(): string {
        if (this.provider) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    send = (data: ProxyProvider): Promise<ProxyProvider> => {
        if (this.provider) {
            return new ProvidersApi(DEFAULT_CONFIG).providersProxyUpdate({
                id: this.provider.pk || 0,
                data: data
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersProxyCreate({
                data: data
            });
        }
    };

    renderHttpBasic(): TemplateResult {
        if (!this.showHttpBasic) {
            return html``;
        }
        return html`<ak-form-element-horizontal
                label=${t`HTTP-Basic Username Key`}
                name="basicAuthUserAttribute">
                <input type="text" value="${ifDefined(this.provider?.basicAuthUserAttribute)}" class="pf-c-form-control">
                <p class="pf-c-form__helper-text">${t`User/Group Attribute used for the user part of the HTTP-Basic Header. If not set, the user's Email address is used.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`HTTP-Basic Password Key`}
                name="basicAuthPasswordAttribute">
                <input type="text" value="${ifDefined(this.provider?.basicAuthPasswordAttribute)}" class="pf-c-form-control">
                <p class="pf-c-form__helper-text">${t`User/Group Attribute used for the password part of the HTTP-Basic Header.`}</p>
            </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.provider?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Authorization flow`}
                ?required=${true}
                name="authorizationFlow">
                <select class="pf-c-form-control">
                    ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                        ordering: "pk",
                        designation: FlowDesignationEnum.Authorization,
                    }).then(flows => {
                        return flows.results.map(flow => {
                            return html`<option value=${ifDefined(flow.pk)} ?selected=${this.provider?.authorizationFlow === flow.pk}>${flow.name} (${flow.slug})</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Flow used when authorizing this provider.`}</p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Protocol settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Internal host`}
                        ?required=${true}
                        name="internalHost">
                        <input type="text" value="${ifDefined(this.provider?.internalHost)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="internalHostSslValidation">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.provider?.internalHostSslValidation, true)}>
                            <label class="pf-c-check__label">
                                ${t`Internal host SSL Validation`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${t`Validate SSL Certificates of upstream servers.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`External host`}
                        ?required=${true}
                        name="externalHost">
                        <input type="text" value="${ifDefined(this.provider?.externalHost)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header">
                    ${t`Advanced protocol settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Certificate`}
                        name="certificate">
                        <select class="pf-c-form-control">
                            ${until(new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList({
                                ordering: "pk",
                                hasKey: "true",
                            }).then(keys => {
                                return keys.results.map(key => {
                                    return html`<option value=${ifDefined(key.pk)} ?selected=${this.provider?.certificate === key.pk}>${key.name}</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal
                        label=${t`Skip path regex`}
                        name="skipPathRegex">
                        <textarea class="pf-c-form-control">${this.provider?.skipPathRegex}</textarea>
                        <p class="pf-c-form__helper-text">${t`Regular expressions for which authentication is not required. Each new line is interpreted as a new Regular Expression.`}</p>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal name="basicAuthEnabled">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.provider?.basicAuthEnabled, false)} @change=${(ev: Event) => {
                                const el = ev.target as HTMLInputElement;
                                this.showHttpBasic = el.checked;
                            }}>
                            <label class="pf-c-check__label">
                                ${t`Set HTTP-Basic Authentication`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${t`Set a custom HTTP-Basic Authentication header based on values from authentik.`}</p>
                    </ak-form-element-horizontal>
                    ${this.renderHttpBasic()}
                </div>
            </ak-form-group>
        </form>`;
    }

}
