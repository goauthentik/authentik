import { DEFAULT_CONFIG, tenant } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    CoreApi,
    CryptoApi,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    LDAPAPIAccessMode,
    LDAPProvider,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends ModelForm<LDAPProvider, number> {
    loadInstance(pk: number): Promise<LDAPProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersLdapRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        } else {
            return msg("Successfully created provider.");
        }
    }

    send = (data: LDAPProvider): Promise<LDAPProvider> => {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapUpdate({
                id: this.instance.pk || 0,
                lDAPProviderRequest: data,
            });
        } else {
            data.tlsServerName = "";
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapCreate({
                lDAPProviderRequest: data,
            });
        }
    };

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
                label=${msg("Bind flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <select class="pf-c-form-control">
                    ${until(
                        tenant().then((t) => {
                            return new FlowsApi(DEFAULT_CONFIG)
                                .flowsInstancesList({
                                    ordering: "slug",
                                    designation: FlowsInstancesListDesignationEnum.Authentication,
                                })
                                .then((flows) => {
                                    return flows.results.map((flow) => {
                                        let selected = flow.pk === t.flowAuthentication;
                                        if (this.instance?.authorizationFlow === flow.pk) {
                                            selected = true;
                                        }
                                        return html`<option
                                            value=${ifDefined(flow.pk)}
                                            ?selected=${selected}
                                        >
                                            ${flow.name} (${flow.slug})
                                        </option>`;
                                    });
                                });
                        }),
                        html`<option>${msg("Loading...")}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Flow used for users to authenticate. Currently only identification and password stages are supported.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Search group")} name="searchGroup">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.searchGroup === undefined}>
                        ---------
                    </option>
                    ${until(
                        new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then((groups) => {
                            return groups.results.map((group) => {
                                return html`<option
                                    value=${ifDefined(group.pk)}
                                    ?selected=${this.instance?.searchGroup === group.pk}
                                >
                                    ${group.name}
                                </option>`;
                            });
                        }),
                        html`<option>${msg("Loading...")}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Users in the selected group can do search queries. If no group is selected, no LDAP Searches are allowed.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Bind mode")} name="bindMode">
                <select class="pf-c-form-control">
                    <option
                        value="${LDAPAPIAccessMode.Cached}"
                        ?selected=${this.instance?.bindMode === LDAPAPIAccessMode.Cached}
                    >
                        ${msg(
                            "Cached binding, flow is executed and session is cached in memory. Flow is executed when session expires.",
                        )}
                    </option>
                    <option
                        value="${LDAPAPIAccessMode.Direct}"
                        ?selected=${this.instance?.bindMode === LDAPAPIAccessMode.Direct}
                    >
                        ${msg(
                            "Direct binding, always execute the configured bind flow to authenticate the user.",
                        )}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("Configure how the outpost authenticates requests.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Search mode")} name="searchMode">
                <select class="pf-c-form-control">
                    <option
                        value="${LDAPAPIAccessMode.Cached}"
                        ?selected=${this.instance?.searchMode === LDAPAPIAccessMode.Cached}
                    >
                        ${msg(
                            "Cached querying, the outpost holds all users and groups in-memory and will refresh every 5 Minutes.",
                        )}
                    </option>
                    <option
                        value="${LDAPAPIAccessMode.Direct}"
                        ?selected=${this.instance?.searchMode === LDAPAPIAccessMode.Direct}
                    >
                        ${msg(
                            "Direct querying, always returns the latest data, but slower than cached querying.",
                        )}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("Configure how the outpost queries the core authentik server's users.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Base DN")}
                        ?required=${true}
                        name="baseDn"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.baseDn, "DC=ldap,DC=goauthentik,DC=io")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "LDAP DN under which bind requests and search requests can be made.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
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
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Due to protocol limitations, this certificate is only used when the outpost has a single provider.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If multiple providers share an outpost, a self-signed certificate is used.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("UID start number")}
                        ?required=${true}
                        name="uidStartNumber"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.uidStartNumber, 2000)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The start for uidNumbers, this number is added to the user.Pk to make sure that the numbers aren't too low for POSIX users. Default is 2000 to ensure that we don't collide with local users uidNumber",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("GID start number")}
                        ?required=${true}
                        name="gidStartNumber"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.gidStartNumber, 4000)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The start for gidNumbers, this number is added to a number generated from the group.Pk to make sure that the numbers aren't too low for POSIX groups. Default is 4000 to ensure that we don't collide with local groups or users primary groups gidNumber",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
