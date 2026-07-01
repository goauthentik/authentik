import "#admin/common/ak-crypto-certificate-search";
import "#components/ak-secret-text-input";
import "#components/ak-slug-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { propertyMappingsProvider, propertyMappingsSelector } from "./LDAPSourceFormHelpers.js";

import { aki } from "#common/api/client";

import { RadioOption } from "#elements/forms/Radio";

import { AKLabel } from "#components/ak-label";

import { placeholderHelperText } from "#admin/helperText";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    LDAPSource,
    LDAPSourceRequest,
    SourcesApi,
    SyncOutgoingTriggerModeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

function createSyncOutgoingTriggerModeOptions(): RadioOption<SyncOutgoingTriggerModeEnum>[] {
    return [
        {
            label: msg("None"),
            value: SyncOutgoingTriggerModeEnum.None,
            description: html`${msg("Outgoing syncs will not be triggered.")}`,
        },
        {
            label: msg("Immediate"),
            value: SyncOutgoingTriggerModeEnum.Immediate,
            description: html`${msg(
                "Outgoing syncs will be triggered immediately for each object that is updated. This can create many background tasks and is therefore not recommended",
            )}`,
        },
        {
            label: msg("Deferred until end"),
            value: SyncOutgoingTriggerModeEnum.DeferredEnd,
            default: true,
            description: html`${msg(
                "Outgoing syncs will be triggered at the end of the source synchronization.",
            )}`,
        },
    ];
}

@customElement("ak-source-ldap-form")
export class LDAPSourceForm extends BaseSourceForm<LDAPSource> {
    protected endpoints = {
        load: (slug: string) => aki(SourcesApi).sourcesLdapRetrieve({ slug }),
        create: (lDAPSource: LDAPSource) =>
            aki(SourcesApi).sourcesLdapCreate({
                lDAPSourceRequest: lDAPSource as unknown as LDAPSourceRequest,
            }),
        update: (slug: string, patchedLDAPSourceRequest: LDAPSource) =>
            aki(SourcesApi).sourcesLdapPartialUpdate({ slug, patchedLDAPSourceRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-slug-input
                name="slug"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                input-hint="code"
            ></ak-slug-input>

            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            ></ak-switch-input>
            <ak-switch-input
                name="passwordLoginUpdateInternalPassword"
                label=${msg("Update internal password on login")}
                ?checked=${this.instance?.passwordLoginUpdateInternalPassword ?? false}
                help=${msg(
                    "When the user logs in to authentik using this source password backend, update their credentials in authentik.",
                )}
            ></ak-switch-input>
            <ak-switch-input
                name="syncUsers"
                label=${msg("Sync users")}
                ?checked=${this.instance?.syncUsers ?? true}
            ></ak-switch-input>
            <ak-switch-input
                name="syncUsersPassword"
                label=${msg("User password writeback")}
                ?checked=${this.instance?.syncUsersPassword ?? true}
                help=${msg(
                    "Login password is synced from LDAP into authentik automatically. Enable this option only to write password changes in authentik back to LDAP.",
                )}
            ></ak-switch-input>
            <ak-switch-input
                name="syncGroups"
                label=${msg("Sync groups")}
                ?checked=${this.instance?.syncGroups ?? true}
            ></ak-switch-input>
            <ak-switch-input
                name="deleteNotFoundObjects"
                label=${msg("Delete Not Found Objects")}
                ?checked=${this.instance?.deleteNotFoundObjects ?? false}
                help=${msg(
                    "Delete authentik users and groups which were previously supplied by this source, but are now missing from it.",
                )}
            ></ak-switch-input>
            <ak-form-group open label="${msg("Connection settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="serverUri">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "serverUri",
                                required: true,
                            },
                            msg("Server URI"),
                        )}
                        <input
                            id="serverUri"
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
                    <ak-switch-input
                        name="startTls"
                        label=${msg("Enable StartTLS")}
                        ?checked=${this.instance?.startTls ?? true}
                        help=${msg("To use SSL instead, use 'ldaps://' and disable this option.")}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="sni"
                        label=${msg("Use Server URI for SNI verification")}
                        ?checked=${this.instance?.sni ?? false}
                        help=${msg("Required for servers using TLS 1.3+")}
                    ></ak-switch-input>
                    <ak-form-element-horizontal name="peerCertificate">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "peerCertificate",
                            },
                            msg("TLS Verification Certificate"),
                        )}
                        <ak-crypto-certificate-search
                            id="peerCertificate"
                            .certificate=${this.instance?.peerCertificate}
                            nokey
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Leave empty to skip certificate validation, or select a certificate/keypair containing the LDAP server CA chain to validate the remote certificate.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="clientCertificate">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "clientCertificate",
                            },
                            msg("TLS Client authentication certificate"),
                        )}
                        <ak-crypto-certificate-search
                            id="clientCertificate"
                            .certificate=${this.instance?.clientCertificate}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Client certificate keypair to authenticate against the LDAP Server's Certificate.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="bindCn">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "bindCn",
                            },
                            msg("Bind CN"),
                        )}
                        <input
                            id="bindCn"
                            type="text"
                            value="${ifDefined(this.instance?.bindCn)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-secret-text-input
                        label=${msg("Bind Password")}
                        name="bindPassword"
                        ?revealed=${!this.instance}
                    ></ak-secret-text-input>
                    <ak-form-element-horizontal required name="baseDn">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "baseDn",
                                required: true,
                            },
                            msg("Base DN"),
                        )}
                        <input
                            id="baseDn"
                            type="text"
                            value="${ifDefined(this.instance?.baseDn)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("LDAP Attribute mapping")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="userPropertyMappings">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userPropertyMappings",
                            },
                            msg("User Property Mappings"),
                        )}
                        <ak-dual-select-dynamic-selected
                            id="userPropertyMappings"
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
                    <ak-form-element-horizontal name="groupPropertyMappings">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "groupPropertyMappings",
                            },
                            msg("Group Property Mappings"),
                        )}
                        <ak-dual-select-dynamic-selected
                            id="groupPropertyMappings"
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
            <ak-form-group label="${msg("Additional settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="syncParentGroup">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "syncParentGroup",
                            },
                            msg("Parent Group"),
                        )}
                        <ak-search-select
                            id="syncParentGroup"
                            .fetchObjects=${async (query?: string): Promise<Group[]> => {
                                const args: CoreGroupsListRequest = {
                                    ordering: "name",
                                    includeUsers: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const groups = await aki(CoreApi).coreGroupsList(args);
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
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Parent group for all the groups imported from LDAP.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="userPathTemplate">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userPathTemplate",
                            },
                            msg("User path"),
                        )}
                        <input
                            id="userPathTemplate"
                            type="text"
                            value="${this.instance?.userPathTemplate ??
                            "goauthentik.io/sources/%(slug)s"}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="additionalUserDn">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "additionalUserDn",
                            },
                            msg("Additional User DN"),
                        )}
                        <input
                            id="additionalUserDn"
                            type="text"
                            value="${ifDefined(this.instance?.additionalUserDn)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Additional user DN, prepended to the Base DN.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="additionalGroupDn">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "additionalGroupDn",
                            },
                            msg("Additional Group DN"),
                        )}
                        <input
                            id="additionalGroupDn"
                            type="text"
                            value="${ifDefined(this.instance?.additionalGroupDn)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Additional group DN, prepended to the Base DN.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="userObjectFilter">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userObjectFilter",
                                required: true,
                            },
                            msg("User object filter"),
                        )}
                        <input
                            id="userObjectFilter"
                            type="text"
                            value="${this.instance?.userObjectFilter || "(objectClass=person)"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Consider Objects matching this filter to be Users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="groupObjectFilter">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "groupObjectFilter",
                                required: true,
                            },
                            msg("Group object filter"),
                        )}
                        <input
                            id="groupObjectFilter"
                            type="text"
                            value="${this.instance?.groupObjectFilter || "(objectClass=group)"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Consider Objects matching this filter to be Groups.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="groupMembershipField">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "groupMembershipField",
                                required: true,
                            },
                            msg("Group membership field"),
                        )}
                        <input
                            id="groupMembershipField"
                            type="text"
                            value="${this.instance?.groupMembershipField || "member"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Field which contains members of a group. The value of this field is matched against User membership attribute.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="userMembershipAttribute">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userMembershipAttribute",
                                required: true,
                            },
                            msg("User membership attribute"),
                        )}
                        <input
                            id="userMembershipAttribute"
                            type="text"
                            value="${this.instance?.userMembershipAttribute || "distinguishedName"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Attribute which matches the value of Group membership field.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="lookupGroupsFromUser"
                        label=${msg("Lookup using user attribute")}
                        ?checked=${this.instance?.lookupGroupsFromUser ?? false}
                        help=${msg(
                            "Field which contains DNs of groups the user is a member of. This field is used to lookup groups from users, e.g. 'memberOf'. To lookup nested groups in an Active Directory environment use 'memberOf:1.2.840.113556.1.4.1941:'.",
                        )}
                    ></ak-switch-input>
                    <ak-form-element-horizontal required name="objectUniquenessField">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "objectUniquenessField",
                                required: true,
                            },
                            msg("Object uniqueness field"),
                        )}
                        <input
                            id="objectUniquenessField"
                            type="text"
                            value="${this.instance?.objectUniquenessField || "objectSid"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Field which contains a unique Identifier.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-radio-input
                        label=${msg("Outgoing sync trigger mode")}
                        required
                        name="syncOutgoingTriggerMode"
                        .value=${this.instance?.syncOutgoingTriggerMode}
                        .options=${createSyncOutgoingTriggerModeOptions}
                    >
                    </ak-radio-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-form": LDAPSourceForm;
    }
}
