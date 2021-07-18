import { FlowsApi, ProvidersApi, LDAPProvider, CoreApi, FlowsInstancesListDesignationEnum, CryptoApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ModelForm } from "../../../elements/forms/ModelForm";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";

@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends ModelForm<LDAPProvider, number> {

    loadInstance(pk: number): Promise<LDAPProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersLdapRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    send = (data: LDAPProvider): Promise<LDAPProvider> => {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapUpdate({
                id: this.instance.pk || 0,
                lDAPProviderRequest: data
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapCreate({
                lDAPProviderRequest: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Bind flow`}
                ?required=${true}
                name="authorizationFlow">
                <select class="pf-c-form-control">
                    ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                        ordering: "pk",
                        designation: FlowsInstancesListDesignationEnum.Authentication,
                    }).then(flows => {
                        return flows.results.map(flow => {
                            return html`<option value=${ifDefined(flow.pk)} ?selected=${this.instance?.authorizationFlow === flow.pk}>${flow.name} (${flow.slug})</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Flow used for users to authenticate. Currently only identification and password stages are supported.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Group`}
                name="searchGroup">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.searchGroup === undefined}>---------</option>
                    ${until(new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then(groups => {
                        return groups.results.map(group => {
                            return html`<option value=${ifDefined(group.pk)} ?selected=${this.instance?.searchGroup === group.pk}>${group.name}</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
                <p class="pf-c-form__helper-text">${t`Users in the selected group can do search queries. If no group is selected, no LDAP Searches are allowed.`}</p>
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
                        <input type="text" value="${first(this.instance?.baseDn, "DC=ldap,DC=goauthentik,DC=io")}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`LDAP DN under which bind requests and search requests can be made.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`TLS Server name`}
                        name="tlsServerName">
                        <input type="text" value="${first(this.instance?.tlsServerName, "")}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${t`Server name for which this provider's certificate is valid for.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Certificate`}
                        name="certificate">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.certificate === undefined}>---------</option>
                            ${until(new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList({
                                ordering: "pk",
                                hasKey: true,
                            }).then(keys => {
                                return keys.results.map(key => {
                                    return html`<option value=${ifDefined(key.pk)} ?selected=${this.instance?.certificate === key.pk}>${key.name}</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`UID start number`}
                        ?required=${true}
                        name="uidStartNumber">
                        <input type="number" value="${first(this.instance?.uidStartNumber, 2000)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`The start for uidNumbers, this number is added to the user.Pk to make sure that the numbers aren't too low for POSIX users. Default is 2000 to ensure that we don't collide with local users uidNumber`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`GID start number`}
                        ?required=${true}
                        name="gidStartNumber">
                        <input type="number" value="${first(this.instance?.gidStartNumber, 4000)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`The start for gidNumbers, this number is added to a number generated from the group.Pk to make sure that the numbers aren't too low for POSIX groups. Default is 4000 to ensure that we don't collide with local groups or users primary groups gidNumber`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
