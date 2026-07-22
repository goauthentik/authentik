import "#components/ak-radio-input";
import "#elements/CodeMirror";
import "#components/ak-number-input";
import "#components/ak-switch-input";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-text-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { AKLabel } from "#components/ak-label";

import { BaseProviderForm } from "#admin/providers/BaseProviderForm";
import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "#admin/providers/google_workspace/GoogleWorkspaceProviderFormHelpers";

import {
    CoreApi,
    CoreGroupsListRequest,
    GoogleWorkspaceProvider,
    Group,
    OutgoingSyncDeleteAction,
    ProvidersApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-provider-google-workspace-form")
export class GoogleWorkspaceProviderFormPage extends BaseProviderForm<GoogleWorkspaceProvider> {
    protected endpoints = {
        load: (id: number) => aki(ProvidersApi).providersGoogleWorkspaceRetrieve({ id }),
        create: (googleWorkspaceProviderRequest: GoogleWorkspaceProvider) =>
            aki(ProvidersApi).providersGoogleWorkspaceCreate({ googleWorkspaceProviderRequest }),
        update: (id: number, googleWorkspaceProviderRequest: GoogleWorkspaceProvider) =>
            aki(ProvidersApi).providersGoogleWorkspaceUpdate({
                id,
                googleWorkspaceProviderRequest,
            }),
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
                    msg("Provider Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    placeholder=${msg("Type a provider name...")}
                    spellcheck="false"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Protocol settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="credentials">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "credentials",
                                required: true,
                            },
                            msg("Credentials"),
                        )}
                        <ak-codemirror
                            id="credentials"
                            mode="javascript"
                            .value="${this.instance?.credentials ?? {}}"
                        ></ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Google Cloud credentials file.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="delegatedSubject">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "delegatedSubject",
                                required: true,
                            },
                            msg("Delegated Subject"),
                        )}
                        <input
                            id="delegatedSubject"
                            type="email"
                            value="${this.instance?.delegatedSubject ?? ""}"
                            class="pf-c-form-control pf-m-monospace"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Email address of the user the actions of authentik will be delegated to.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="defaultGroupEmailDomain">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "defaultGroupEmailDomain",
                                required: true,
                            },
                            msg("Default group email domain"),
                        )}
                        <input
                            id="defaultGroupEmailDomain"
                            type="text"
                            value="${this.instance?.defaultGroupEmailDomain ?? ""}"
                            class="pf-c-form-control pf-m-monospace"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Default domain that is used to generate a group's email address. Can be customized using property mappings.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-radio-input
                        name="userDeleteAction"
                        label=${msg("User deletion action")}
                        required
                        .options=${[
                            {
                                label: msg("Delete"),
                                value: OutgoingSyncDeleteAction.Delete,
                                default: true,
                                description: html`${msg("User is deleted")}`,
                            },
                            {
                                label: msg("Suspend"),
                                value: OutgoingSyncDeleteAction.Suspend,
                                description: html`${msg(
                                    "User is suspended, and connection to user in authentik is removed.",
                                )}`,
                            },
                            {
                                label: msg("Do Nothing"),
                                value: OutgoingSyncDeleteAction.DoNothing,
                                description: html`${msg(
                                    "The connection is removed but the user is not modified",
                                )}`,
                            },
                        ]}
                        .value=${this.instance?.userDeleteAction}
                        help=${msg("Determines what authentik will do when a User is deleted.")}
                    >
                    </ak-radio-input>
                    <ak-radio-input
                        name="groupDeleteAction"
                        label=${msg("Group deletion action")}
                        required
                        .options=${[
                            {
                                label: msg("Delete"),
                                value: OutgoingSyncDeleteAction.Delete,
                                default: true,
                                description: html`${msg("Group is deleted")}`,
                            },
                            {
                                label: msg("Do Nothing"),
                                value: OutgoingSyncDeleteAction.DoNothing,
                                description: html`${msg(
                                    "The connection is removed but the group is not modified",
                                )}`,
                            },
                        ]}
                        .value=${this.instance?.groupDeleteAction}
                        help=${msg("Determines what authentik will do when a Group is deleted.")}
                    >
                    </ak-radio-input>
                    <ak-switch-input
                        name="dryRun"
                        label=${msg("Enable dry-run mode")}
                        ?checked=${this.instance?.dryRun ?? false}
                        help=${msg(
                            "When enabled, mutating requests will be dropped and logged instead.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("User filtering")}">
                <div class="pf-c-form">
                    <ak-switch-input
                        name="excludeUsersServiceAccount"
                        label=${msg("Exclude service accounts")}
                        ?checked=${this.instance?.excludeUsersServiceAccount ?? true}
                    ></ak-switch-input>
                    <ak-form-element-horizontal name="filterGroup">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "filterGroup",
                            },
                            msg("Group"),
                        )}
                        <ak-search-select
                            id="filterGroup"
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
                                return group.pk === this.instance?.filterGroup;
                            }}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Only sync users within the selected group.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("Attribute mapping")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="propertyMappings">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "propertyMappings",
                            },
                            msg("User Property Mappings"),
                        )}
                        <ak-dual-select-dynamic-selected
                            id="propertyMappings"
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.propertyMappings,
                                "goauthentik.io/providers/google_workspace/user",
                            )}
                            available-label=${msg("Available Property Mappings")}
                            selected-label=${msg("Selected Property Mappings")}
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings used to user mapping.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="propertyMappingsGroup">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "propertyMappingsGroup",
                            },
                            msg("Group Property Mappings"),
                        )}
                        <ak-dual-select-dynamic-selected
                            id="propertyMappingsGroup"
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.propertyMappingsGroup,
                                "goauthentik.io/providers/google_workspace/group",
                            )}
                            available-label=${msg("Available Property Mappings")}
                            selected-label=${msg("Selected Property Mappings")}
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings used to group creation.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Sync settings")}">
                <div class="pf-c-form">
                    <ak-number-input
                        label=${msg("Page size")}
                        required
                        name="pageSize"
                        value="${this.instance?.syncPageSize ?? 100}"
                        help=${msg("Controls the number of objects synced in a single task.")}
                    ></ak-number-input>
                    <ak-text-input
                        name="syncPageTimeout"
                        label=${msg("Page timeout")}
                        input-hint="code"
                        required
                        value="${ifDefined(this.instance?.syncPageTimeout ?? "minutes=30")}"
                        .bighelp=${html`<p class="pf-c-form__helper-text">
                                ${msg("Timeout for synchronization of a single page.")}
                            </p>
                            <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                    >
                    </ak-text-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-google-workspace-form": GoogleWorkspaceProviderFormPage;
    }
}
