import { FlowDesignationEnum, FlowsApi, ProvidersApi, LDAPProvider } from "authentik-api";
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

@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends Form<LDAPProvider> {

    set providerUUID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG).providersLdapRead({
            id: value,
        }).then(provider => {
            this.provider = provider;
        });
    }

    @property({attribute: false})
    provider?: LDAPProvider;

    getSuccessMessage(): string {
        if (this.provider) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    send = (data: LDAPProvider): Promise<LDAPProvider> => {
        if (this.provider) {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapUpdate({
                id: this.provider.pk || 0,
                data: data
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.provider?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Bind flow`}
                ?required=${true}
                name="authorizationFlow">
                <select class="pf-c-form-control">
                    ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                        ordering: "pk",
                        designation: FlowDesignationEnum.Authentication,
                    }).then(flows => {
                        return flows.results.map(flow => {
                            return html`<option value=${ifDefined(flow.pk)} ?selected=${this.provider?.authorizationFlow === flow.pk}>${flow.name} (${flow.slug})</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Flow used for users to authenticate. Currently only identification and password stages are supported.`}</p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Protocol settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Base DN`}
                        ?required=${true}
                        name="baseDn">
                        <input type="text" value="${first(this.provider?.baseDn, "DC=ldap,DC=goauthentik,DC=io")}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`LDAP DN under which bind requests and search requests can be made.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
