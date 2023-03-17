import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG, tenant } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CertificateKeyPair,
    CoreApi,
    CoreGroupsListRequest,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    CurrentTenant,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    Group,
    LDAPAPIAccessMode,
    LDAPProvider,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-ldap-form")
export class LDAPProviderFormPage extends ModelForm<LDAPProvider, number> {
    @state()
    tenant?: CurrentTenant;
    async loadInstance(pk: number): Promise<LDAPProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersLdapRetrieve({
            id: pk,
        });
        this.tenant = await tenant();
        return provider;
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
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Bind flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Authentication,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
                        return flows.results;
                    }}
                    .renderElement=${(flow: Flow): string => {
                        return RenderFlowOption(flow);
                    }}
                    .renderDescription=${(flow: Flow): TemplateResult => {
                        return html`${flow.slug}`;
                    }}
                    .value=${(flow: Flow | undefined): string | undefined => {
                        return flow?.pk;
                    }}
                    .selected=${(flow: Flow): boolean => {
                        let selected = flow.pk === this.tenant?.flowAuthentication;
                        if (this.instance?.authorizationFlow === flow.pk) {
                            selected = true;
                        }
                        return selected;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used for users to authenticate. Currently only identification and password stages are supported.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Search group`} name="searchGroup">
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
                    ${t`Users in the selected group can do search queries. If no group is selected, no LDAP Searches are allowed.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Bind mode`} name="bindMode">
                <ak-radio
                    .options=${[
                        {
                            label: t`Cached binding`,
                            value: LDAPAPIAccessMode.Cached,
                            default: true,
                            description: html`${t`Flow is executed and session is cached in memory. Flow is executed when session expires`}`,
                        },
                        {
                            label: t`Direct binding`,
                            value: LDAPAPIAccessMode.Direct,
                            description: html`${t`Always execute the configured bind flow to authenticate the user`}`,
                        },
                    ]}
                    .value=${this.instance?.bindMode}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${t`Configure how the outpost authenticates requests.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Search mode`} name="searchMode">
                <ak-radio
                    .options=${[
                        {
                            label: t`Cached querying`,
                            value: LDAPAPIAccessMode.Cached,
                            default: true,
                            description: html`${t`The outpost holds all users and groups in-memory and will refresh every 5 Minutes`}`,
                        },
                        {
                            label: t`Direct querying`,
                            value: LDAPAPIAccessMode.Direct,
                            description: html`${t`Always returns the latest data, but slower than cached querying`}`,
                        },
                    ]}
                    .value=${this.instance?.searchMode}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${t`Configure how the outpost queries the core authentik server's users.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Base DN`} ?required=${true} name="baseDn">
                        <input
                            type="text"
                            value="${first(this.instance?.baseDn, "DC=ldap,DC=goauthentik,DC=io")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`LDAP DN under which bind requests and search requests can be made.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Certificate`} name="certificate">
                        <ak-search-select
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<CertificateKeyPair[]> => {
                                const args: CryptoCertificatekeypairsListRequest = {
                                    ordering: "name",
                                    hasKey: true,
                                    includeDetails: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const certificates = await new CryptoApi(
                                    DEFAULT_CONFIG,
                                ).cryptoCertificatekeypairsList(args);
                                return certificates.results;
                            }}
                            .renderElement=${(item: CertificateKeyPair): string => {
                                return item.name;
                            }}
                            .value=${(item: CertificateKeyPair | undefined): string | undefined => {
                                return item?.pk;
                            }}
                            .selected=${(item: CertificateKeyPair): boolean => {
                                return item.pk === this.instance?.certificate;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Due to protocol limitations, this certificate is only used when the outpost has a single provider, or all providers use the same certificate.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`If multiple providers share an outpost, a self-signed certificate is used.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`UID start number`}
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
                            ${t`The start for uidNumbers, this number is added to the user.Pk to make sure that the numbers aren't too low for POSIX users. Default is 2000 to ensure that we don't collide with local users uidNumber`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`GID start number`}
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
                            ${t`The start for gidNumbers, this number is added to a number generated from the group.Pk to make sure that the numbers aren't too low for POSIX groups. Default is 4000 to ensure that we don't collide with local groups or users primary groups gidNumber`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
