import "#admin/common/ak-flow-search/ak-source-flow-search";
import "#components/ak-secret-text-input";
import "#components/ak-secret-textarea-input";
import "#components/ak-slug-input";
import "#components/ak-radio-input";
import "#components/ak-file-search-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { propertyMappingsProvider, propertyMappingsSelector } from "./KerberosSourceFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { RadioOption } from "#elements/forms/Radio";

import { iconHelperText, placeholderHelperText } from "#admin/helperText";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";
import { GroupMatchingModeToLabel, UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import {
    AdminFileListUsageEnum,
    FlowsInstancesListDesignationEnum,
    GroupMatchingModeEnum,
    KadminTypeEnum,
    KerberosSource,
    KerberosSourceRequest,
    SourcesApi,
    SyncOutgoingTriggerModeEnum,
    UserMatchingModeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const SyncOutgoingTriggerModeOptions: readonly RadioOption<SyncOutgoingTriggerModeEnum>[] = [
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
@customElement("ak-source-kerberos-form")
export class KerberosSourceForm extends BaseSourceForm<KerberosSource> {
    async loadInstance(pk: string): Promise<KerberosSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosRetrieve({
            slug: pk,
        });
    }

    async send(data: KerberosSource): Promise<KerberosSource> {
        if (this.instance) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosPartialUpdate({
                slug: this.instance.slug,
                patchedKerberosSourceRequest: data,
            });
        }

        return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosCreate({
            kerberosSourceRequest: data as unknown as KerberosSourceRequest,
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                input-hint="code"
            ></ak-slug-input>
            <ak-switch-input
                name="enabled"
                ?checked=${this.instance?.enabled ?? true}
                label=${msg("Enabled")}
            ></ak-switch-input>
            <ak-switch-input
                name="promoted"
                ?checked=${this.instance?.promoted ?? false}
                label=${msg("Promoted")}
                help=${msg(
                    "When enabled, this source will be displayed as a prominent button on the login page, instead of a small icon.",
                )}
            ></ak-switch-input>
            <ak-switch-input
                name="passwordLoginUpdateInternalPassword"
                ?checked=${this.instance?.passwordLoginUpdateInternalPassword ?? false}
                label=${msg("Update internal password on login")}
                help=${msg(
                    "When the user logs in to authentik using this source password backend, update their credentials in authentik.",
                )}
            ></ak-switch-input>
            <ak-switch-input
                name="syncUsers"
                ?checked=${this.instance?.syncUsers ?? true}
                label=${msg("Sync users")}
            ></ak-switch-input>
            <ak-switch-input
                name="syncUsersPassword"
                ?checked=${this.instance?.syncUsersPassword ?? true}
                label=${msg("User password writeback")}
                help=${msg(
                    "Enable this option to write password changes made in authentik back to Kerberos. Ignored if sync is disabled.",
                )}
            ></ak-switch-input>
            <ak-form-group open label="${msg("Realm settings")}">
                <div class="pf-c-form">
                    <ak-text-input
                        name="realm"
                        label=${msg("Realm")}
                        value=${ifDefined(this.instance?.realm)}
                        placeholder="AUTHENTIK.COMPANY"
                        required
                    ></ak-text-input>
                    <ak-textarea-input
                        name="krb5Conf"
                        label=${msg("Kerberos 5 configuration")}
                        value=${ifDefined(this.instance?.krb5Conf)}
                        help=${msg(
                            "Kerberos 5 configuration. See man krb5.conf(5) for configuration format. If left empty, a default krb5.conf will be used.",
                        )}
                    ></ak-textarea-input>
                    <ak-form-element-horizontal
                        label=${msg("User matching mode")}
                        required
                        name="userMatchingMode"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${UserMatchingModeEnum.Identifier}
                                ?selected=${this.instance?.userMatchingMode ===
                                UserMatchingModeEnum.Identifier}
                            >
                                ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                            </option>
                            <option
                                value=${UserMatchingModeEnum.EmailLink}
                                ?selected=${this.instance?.userMatchingMode ===
                                UserMatchingModeEnum.EmailLink}
                            >
                                ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                            </option>
                            <option
                                value=${UserMatchingModeEnum.EmailDeny}
                                ?selected=${this.instance?.userMatchingMode ===
                                UserMatchingModeEnum.EmailDeny}
                            >
                                ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                            </option>
                            <option
                                value=${UserMatchingModeEnum.UsernameLink}
                                ?selected=${this.instance?.userMatchingMode ===
                                UserMatchingModeEnum.UsernameLink}
                            >
                                ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                            </option>
                            <option
                                value=${UserMatchingModeEnum.UsernameDeny}
                                ?selected=${this.instance?.userMatchingMode ===
                                UserMatchingModeEnum.UsernameDeny}
                            >
                                ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameDeny)}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group matching mode")}
                        required
                        name="groupMatchingMode"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${GroupMatchingModeEnum.Identifier}
                                ?selected=${this.instance?.groupMatchingMode ===
                                GroupMatchingModeEnum.Identifier}
                            >
                                ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                            </option>
                            <option
                                value=${GroupMatchingModeEnum.NameLink}
                                ?selected=${this.instance?.groupMatchingMode ===
                                GroupMatchingModeEnum.NameLink}
                            >
                                ${GroupMatchingModeToLabel(GroupMatchingModeEnum.NameLink)}
                            </option>
                            <option
                                value=${GroupMatchingModeEnum.NameDeny}
                                ?selected=${this.instance?.groupMatchingMode ===
                                GroupMatchingModeEnum.NameDeny}
                            >
                                ${GroupMatchingModeToLabel(GroupMatchingModeEnum.NameDeny)}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Sync connection settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("KAdmin type")}
                        required
                        name="kadminType"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: "MIT",
                                    value: KadminTypeEnum.Mit,
                                    default: true,
                                    description: html`${msg("MIT krb5 kadmin")}`,
                                },
                                {
                                    label: "Heimdal",
                                    value: KadminTypeEnum.Heimdal,
                                    description: html`${msg("Heimdal kadmin")}`,
                                },
                                {
                                    label: msg("Other"),
                                    value: KadminTypeEnum.Other,
                                    description: html`${msg("Other type of kadmin")}`,
                                },
                            ]}
                            .value=${this.instance?.kadminType}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-text-input
                        name="syncPrincipal"
                        label=${msg("Sync principal")}
                        value=${ifDefined(this.instance?.syncPrincipal)}
                        help=${msg("Principal used to authenticate to the KDC for syncing.")}
                    ></ak-text-input>
                    <ak-secret-text-input
                        name="syncPassword"
                        label=${msg("Sync password")}
                        ?revealed=${!this.instance}
                        help=${msg(
                            "Password used to authenticate to the KDC for syncing. Optional if Sync keytab or Sync credentials cache is provided.",
                        )}
                    ></ak-secret-text-input>
                    <ak-secret-textarea-input
                        name="syncKeytab"
                        label=${msg("Sync keytab")}
                        ?revealed=${!this.instance}
                        help=${msg(
                            "Keytab used to authenticate to the KDC for syncing. Optional if Sync password or Sync credentials cache is provided. Must be base64 encoded or in the form TYPE:residual.",
                        )}
                    ></ak-secret-textarea-input>
                    <ak-text-input
                        name="syncCcache"
                        label=${msg("Sync credentials cache")}
                        value=${ifDefined(this.instance?.syncCcache)}
                        help=${msg(
                            "Credentials cache used to authenticate to the KDC for syncing. Optional if Sync password or Sync keytab is provided. Must be in the form TYPE:residual.",
                        )}
                    ></ak-text-input>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("SPNEGO settings")}">
                <div class="pf-c-form">
                    <ak-text-input
                        name="spnegoServerName"
                        label=${msg("SPNEGO server name")}
                        value=${ifDefined(this.instance?.spnegoServerName)}
                        help=${msg(
                            "Force the use of a specific server name for SPNEGO. Must be in the form HTTP@domain",
                        )}
                    ></ak-text-input>
                    <ak-secret-textarea-input
                        name="spnegoKeytab"
                        label=${msg("SPNEGO keytab")}
                        ?revealed=${!this.instance}
                        help=${msg(
                            "Keytab used for SPNEGO. Optional if SPNEGO credentials cache is provided. Must be base64 encoded or in the form TYPE:residual.",
                        )}
                    ></ak-secret-textarea-input>
                    <ak-text-input
                        name="spnegoCcache"
                        label=${msg("SPNEGO credentials cache")}
                        value=${ifDefined(this.instance?.spnegoCcache)}
                        help=${msg(
                            "Credentials cache used for SPNEGO. Optional if SPNEGO keytab is provided. Must be in the form TYPE:residual.",
                        )}
                    ></ak-text-input>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Kerberos Attribute mapping")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="userPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                "user",
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
                                "group",
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
            <ak-form-group label="${msg("Flow settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        name="enrollmentFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-enrollment"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Additional settings")}">
                <div class="pf-c-form">
                    <ak-text-input
                        name="userPathTemplate"
                        label=${msg("User path")}
                        value=${this.instance?.userPathTemplate ??
                        "goauthentik.io/sources/%(slug)s"}
                        help=${placeholderHelperText}
                    ></ak-text-input>
                </div>
                <ak-radio-input
                    label=${msg("Outgoing sync trigger mode")}
                    required
                    name="type"
                    .value=${this.instance?.syncOutgoingTriggerMode}
                    .options=${SyncOutgoingTriggerModeOptions}
                >
                </ak-radio-input>
                <ak-file-search-input
                    name="icon"
                    label=${msg("Icon")}
                    .value=${this.instance?.icon}
                    .usage=${AdminFileListUsageEnum.Media}
                    blankable
                    help=${iconHelperText}
                ></ak-file-search-input>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-kerberos-form": KerberosSourceForm;
    }
}
