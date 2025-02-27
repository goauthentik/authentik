import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "@goauthentik/admin/providers/google_workspace/GoogleWorkspaceProviderFormHelpers.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    GoogleWorkspaceProvider,
    Group,
    OutgoingSyncDeleteAction,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-google-workspace-form")
export class GoogleWorkspaceProviderFormPage extends BaseProviderForm<GoogleWorkspaceProvider> {
    loadInstance(pk: number): Promise<GoogleWorkspaceProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersGoogleWorkspaceRetrieve({
            id: pk,
        });
    }

    async send(data: GoogleWorkspaceProvider): Promise<GoogleWorkspaceProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersGoogleWorkspaceUpdate({
                id: this.instance.pk,
                googleWorkspaceProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersGoogleWorkspaceCreate({
                googleWorkspaceProviderRequest: data,
            });
        }
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
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Credentials")}
                        ?required=${true}
                        name="credentials"
                    >
                        <ak-codemirror
                            mode=${CodeMirrorMode.JavaScript}
                            .value="${first(this.instance?.credentials, {})}"
                        ></ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Google Cloud credentials file.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Delegated Subject")}
                        ?required=${true}
                        name="delegatedSubject"
                    >
                        <input
                            type="email"
                            value="${first(this.instance?.delegatedSubject, "")}"
                            class="pf-c-form-control pf-m-monospace"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Email address of the user the actions of authentik will be delegated to.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Default group email domain")}
                        ?required=${true}
                        name="defaultGroupEmailDomain"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.defaultGroupEmailDomain, "")}"
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
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header">${msg("User filtering")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="excludeUsersServiceAccount">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.excludeUsersServiceAccount, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Exclude service accounts")}</span
                            >
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Group")} name="filterGroup">
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
                                return group.pk === this.instance?.filterGroup;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Only sync users within the selected group.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header"> ${msg("Attribute mapping")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="propertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
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
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="propertyMappingsGroup"
                    >
                        <ak-dual-select-dynamic-selected
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
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-google-workspace-form": GoogleWorkspaceProviderFormPage;
    }
}
