import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CertificateKeyPair,
    CoreApi,
    CoreGroupsListRequest,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    Group,
    LDAPSource,
    LDAPSourceRequest,
    PaginatedLDAPPropertyMappingList,
    PropertymappingsApi,
    SourcesApi,
} from "@goauthentik/api";

@customElement("ak-source-ldap-form")
export class LDAPSourceForm extends ModelForm<LDAPSource, string> {
    loadInstance(pk: string): Promise<LDAPSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesLdapRetrieve({
            slug: pk,
        });
    }

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsLdapList({
            ordering: "managed,object_field",
        });
    }

    propertyMappings?: PaginatedLDAPPropertyMappingList;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
    }

    async send(data: LDAPSource): Promise<LDAPSource> {
        if (this.instance) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesLdapPartialUpdate({
                slug: this.instance.slug,
                patchedLDAPSourceRequest: data,
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesLdapCreate({
                lDAPSourceRequest: data as unknown as LDAPSourceRequest,
            });
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
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`Enabled`}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncUsers">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.syncUsers, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`Sync users`}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncUsersPassword">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.syncUsersPassword, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`User password writeback`}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${t`Login password is synced from LDAP into authentik automatically. Enable this option only to write password changes in authentik back to LDAP.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncGroups">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.syncGroups, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`Sync groups`}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Connection settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Server URI`}
                        ?required=${true}
                        name="serverUri"
                    >
                        <input
                            type="text"
                            placeholder="ldap://1.2.3.4"
                            value="${ifDefined(this.instance?.serverUri)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Specify multiple server URIs by separating them with a comma.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="startTls">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.startTls, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Enable StartTLS`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`To use SSL instead, use 'ldaps://' and disable this option.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`TLS Verification Certificate`}
                        name="peerCertificate"
                    >
                        <ak-search-select
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<CertificateKeyPair[]> => {
                                const args: CryptoCertificatekeypairsListRequest = {
                                    ordering: "name",
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
                                return item.pk === this.instance?.peerCertificate;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`When connecting to an LDAP Server with TLS, certificates are not checked by default. Specify a keypair to validate the remote certificate.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Bind CN`} name="bindCn">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.bindCn)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Bind Password`}
                        ?writeOnly=${this.instance !== undefined}
                        name="bindPassword"
                    >
                        <input type="text" value="" class="pf-c-form-control" />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Base DN`} ?required=${true} name="baseDn">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.baseDn)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header"> ${t`LDAP Attribute mapping`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`User Property Mappings`}
                        ?required=${true}
                        name="propertyMappings"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!this.instance?.propertyMappings) {
                                    selected =
                                        mapping.managed?.startsWith(
                                            "goauthentik.io/sources/ldap/default",
                                        ) ||
                                        mapping.managed?.startsWith(
                                            "goauthentik.io/sources/ldap/ms",
                                        ) ||
                                        false;
                                } else {
                                    selected = Array.from(this.instance?.propertyMappings).some(
                                        (su) => {
                                            return su == mapping.pk;
                                        },
                                    );
                                }
                                return html`<option
                                    value=${ifDefined(mapping.pk)}
                                    ?selected=${selected}
                                >
                                    ${mapping.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Property mappings used to user creation.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group Property Mappings`}
                        ?required=${true}
                        name="propertyMappingsGroup"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!this.instance?.propertyMappingsGroup) {
                                    selected =
                                        mapping.managed ===
                                        "goauthentik.io/sources/ldap/default-name";
                                } else {
                                    selected = Array.from(
                                        this.instance?.propertyMappingsGroup,
                                    ).some((su) => {
                                        return su == mapping.pk;
                                    });
                                }
                                return html`<option
                                    value=${ifDefined(mapping.pk)}
                                    ?selected=${selected}
                                >
                                    ${mapping.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Property mappings used to group creation.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Additional settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Group`} name="syncParentGroup">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Group[]> => {
                                const args: CoreGroupsListRequest = {
                                    ordering: "name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(
                                    args,
                                );
                                return groups.results;
                            }}
                            .renderElement=${(group: Group): string => {
                                return group.name;
                            }}
                            .value=${(group: Group | undefined): string | undefined => {
                                return group ? group.pk : undefined;
                            }}
                            .selected=${(group: Group): boolean => {
                                return group.pk === this.instance?.syncParentGroup;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Parent group for all the groups imported from LDAP.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`User path`} name="userPathTemplate">
                        <input
                            type="text"
                            value="${first(
                                this.instance?.userPathTemplate,
                                "goauthentik.io/sources/%(slug)s",
                            )}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Path template for users created. Use placeholders like \`%(slug)s\` to insert the source slug.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Addition User DN`}
                        name="additionalUserDn"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.additionalUserDn)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Additional user DN, prepended to the Base DN.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Addition Group DN`}
                        name="additionalGroupDn"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.additionalGroupDn)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Additional group DN, prepended to the Base DN.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`User object filter`}
                        ?required=${true}
                        name="userObjectFilter"
                    >
                        <input
                            type="text"
                            value="${this.instance?.userObjectFilter || "(objectClass=person)"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Consider Objects matching this filter to be Users.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group object filter`}
                        ?required=${true}
                        name="groupObjectFilter"
                    >
                        <input
                            type="text"
                            value="${this.instance?.groupObjectFilter || "(objectClass=group)"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Consider Objects matching this filter to be Groups.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group membership field`}
                        ?required=${true}
                        name="groupMembershipField"
                    >
                        <input
                            type="text"
                            value="${this.instance?.groupMembershipField || "member"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Field which contains members of a group. Note that if using the "memberUid" field, the value is assumed to contain a relative distinguished name. e.g. 'memberUid=some-user' instead of 'memberUid=cn=some-user,ou=groups,...'`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Object uniqueness field`}
                        ?required=${true}
                        name="objectUniquenessField"
                    >
                        <input
                            type="text"
                            value="${this.instance?.objectUniquenessField || "objectSid"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Field which contains a unique Identifier.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
