import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    FlowsInstancesListDesignationEnum,
    Group,
    LDAPAPIAccessMode,
    LDAPProvider,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends ModelForm<LDAPProvider, number> {
    async loadInstance(pk: number): Promise<LDAPProvider> {
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

    async send(data: LDAPProvider): Promise<LDAPProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapUpdate({
                id: this.instance.pk || 0,
                lDAPProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersLdapCreate({
                lDAPProviderRequest: data,
            });
        }
    }

    // All Provider objects have an Authorization flow, but not all providers have an Authentication
    // flow. LDAP needs only one field, but it is not an Authorization field, it is an
    // Authentication field. So, yeah, we're using the authorization field to store the
    // authentication information, which is why the ak-tenanted-flow-search call down there looks so
    // weird-- we're looking up Authentication flows, but we're storing them in the Authorization
    // field of the target Provider.
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
                <ak-tenanted-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${this.instance?.authorizationFlow}
                    .tenantFlow=${rootInterface()?.tenant?.flowAuthentication}
                    required
                ></ak-tenanted-flow-search>
                <p class="pf-c-form__helper-text">${msg("Flow used for users to authenticate.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Search group")} name="searchGroup">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
                        return groups.results;
                    }}
                    .renderElement=${(group: Group): string => {
                        return group.name;
                    }}
                    .value=${(group: Group | undefined): string | undefined => {
                        return group?.pk;
                    }}
                    .selected=${(group: Group): boolean => {
                        return group.pk === this.instance?.searchGroup;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Users in the selected group can do search queries. If no group is selected, no LDAP Searches are allowed.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Bind mode")} name="bindMode">
                <ak-radio
                    .options=${[
                        {
                            label: msg("Cached binding"),
                            value: LDAPAPIAccessMode.Cached,
                            default: true,
                            description: html`${msg(
                                "Flow is executed and session is cached in memory. Flow is executed when session expires",
                            )}`,
                        },
                        {
                            label: msg("Direct binding"),
                            value: LDAPAPIAccessMode.Direct,
                            description: html`${msg(
                                "Always execute the configured bind flow to authenticate the user",
                            )}`,
                        },
                    ]}
                    .value=${this.instance?.bindMode}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Configure how the outpost authenticates requests.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Search mode")} name="searchMode">
                <ak-radio
                    .options=${[
                        {
                            label: msg("Cached querying"),
                            value: LDAPAPIAccessMode.Cached,
                            default: true,
                            description: html`${msg(
                                "The outpost holds all users and groups in-memory and will refresh every 5 Minutes",
                            )}`,
                        },
                        {
                            label: msg("Direct querying"),
                            value: LDAPAPIAccessMode.Direct,
                            description: html`${msg(
                                "Always returns the latest data, but slower than cached querying",
                            )}`,
                        },
                    ]}
                    .value=${this.instance?.searchMode}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Configure how the outpost queries the core authentik server's users.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="mfaSupport">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.mfaSupport, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Code-based MFA Support")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When enabled, code-based multi-factor authentication can be used by appending a semicolon and the TOTP code to the password. This should only be enabled if all users that will bind to this provider have a TOTP device configured, as otherwise a password may incorrectly be rejected if it contains a semicolon.",
                    )}
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
                        <ak-crypto-certificate-search
                            certificate=${this.instance?.certificate}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The certificate for the above configured Base DN. As a fallback, the provider uses a self-signed certificate.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("TLS Server name")}
                        name="tlsServerName"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.tlsServerName, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "DNS name for which the above configured certificate should be used. The certificate cannot be detected based on the base DN, as the SSL/TLS negotiation happens before such data is exchanged.",
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
