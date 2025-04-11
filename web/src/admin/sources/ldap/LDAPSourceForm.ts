import "@goauthentik/admin/common/ak-crypto-certificate-search";
import { placeholderHelperText } from "@goauthentik/admin/helperText";
import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    LDAPSource,
    LDAPSourceRequest,
    SourcesApi,
} from "@goauthentik/api";

import { propertyMappingsProvider, propertyMappingsSelector } from "./LDAPSourceFormHelpers.js";

@customElement("ak-source-ldap-form")
export class LDAPSourceForm extends BaseSourceForm<LDAPSource> {
    loadInstance(pk: string): Promise<LDAPSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesLdapRetrieve({
            slug: pk,
        });
    }

    async send(data: LDAPSource): Promise<LDAPSource> {
        if (this.instance) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesLdapPartialUpdate({
                slug: this.instance.slug,
                patchedLDAPSourceRequest: data,
            });
        }

        return new SourcesApi(DEFAULT_CONFIG).sourcesLdapCreate({
            lDAPSourceRequest: data as unknown as LDAPSourceRequest,
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Slug")} ?required=${true} name="slug">
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
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="passwordLoginUpdateInternalPassword">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.passwordLoginUpdateInternalPassword, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${msg("Update internal password on login")}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When the user logs in to authentik using this source password backend, update their credentials in authentik.",
                    )}
                </p>
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
                    <span class="pf-c-switch__label">${msg("Sync users")}</span>
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
                    <span class="pf-c-switch__label">${msg("User password writeback")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Login password is synced from LDAP into authentik automatically. Enable this option only to write password changes in authentik back to LDAP.",
                    )}
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
                    <span class="pf-c-switch__label">${msg("Sync groups")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Connection settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Server URI")}
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
                            ${msg("Specify multiple server URIs by separating them with a comma.")}
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
                            <span class="pf-c-switch__label">${msg("Enable StartTLS")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("To use SSL instead, use 'ldaps://' and disable this option.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="sni">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.sni, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Use Server URI for SNI verification")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Required for servers using TLS 1.3+")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("TLS Verification Certificate")}
                        name="peerCertificate"
                    >
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.peerCertificate}
                            nokey
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When connecting to an LDAP Server with TLS, certificates are not checked by default. Specify a keypair to validate the remote certificate.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("TLS Client authentication certificate")}
                        name="clientCertificate"
                    >
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.clientCertificate}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Client certificate keypair to authenticate against the LDAP Server's Certificate.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Bind CN")} name="bindCn">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.bindCn)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Bind Password")}
                        ?writeOnly=${this.instance !== undefined}
                        name="bindPassword"
                    >
                        <input type="text" value="" class="pf-c-form-control" />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Base DN")}
                        ?required=${true}
                        name="baseDn"
                    >
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
                <span slot="header"> ${msg("LDAP Attribute mapping")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="userPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.userPropertyMappings,
                            )}
                            available-label="${msg("Available User Property Mappings")}"
                            selected-label="${msg("Selected User Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for user creation.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="groupPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.groupPropertyMappings,
                            )}
                            available-label="${msg("Available Group Property Mappings")}"
                            selected-label="${msg("Selected Group Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for group creation.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Additional settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Parent Group")} name="syncParentGroup">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Group[]> => {
                                const args: CoreGroupsListRequest = {
                                    ordering: "name",
                                    includeUsers: false,
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
                            ${msg("Parent group for all the groups imported from LDAP.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("User path")} name="userPathTemplate">
                        <input
                            type="text"
                            value="${first(
                                this.instance?.userPathTemplate,
                                "goauthentik.io/sources/%(slug)s",
                            )}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Addition User DN")}
                        name="additionalUserDn"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.additionalUserDn)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Additional user DN, prepended to the Base DN.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Addition Group DN")}
                        name="additionalGroupDn"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.additionalGroupDn)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Additional group DN, prepended to the Base DN.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("User object filter")}
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
                            ${msg("Consider Objects matching this filter to be Users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group object filter")}
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
                            ${msg("Consider Objects matching this filter to be Groups.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group membership field")}
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
                            ${msg(
                                "Field which contains members of a group. Note that if using the \"memberUid\" field, the value is assumed to contain a relative distinguished name. e.g. 'memberUid=some-user' instead of 'memberUid=cn=some-user,ou=groups,...'. When selecting 'Lookup using a user attribute', this should be a user attribute, otherwise a group attribute.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="lookupGroupsFromUser">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.lookupGroupsFromUser, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Lookup using user attribute")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Field which contains DNs of groups the user is a member of. This field is used to lookup groups from users, e.g. 'memberOf'. To lookup nested groups in an Active Directory environment use 'memberOf:1.2.840.113556.1.4.1941:'.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Object uniqueness field")}
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
                            ${msg("Field which contains a unique Identifier.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-form": LDAPSourceForm;
    }
}
