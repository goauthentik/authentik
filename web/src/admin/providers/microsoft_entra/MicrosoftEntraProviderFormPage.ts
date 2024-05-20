import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
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
    Group,
    MicrosoftEntraProvider,
    OutgoingSyncDeleteAction,
    PaginatedMicrosoftEntraProviderMappingList,
    PropertymappingsApi,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-microsoft-entra-form")
export class MicrosoftEntraProviderFormPage extends BaseProviderForm<MicrosoftEntraProvider> {
    loadInstance(pk: number): Promise<MicrosoftEntraProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraRetrieve({
            id: pk,
        });
    }

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsProviderMicrosoftEntraList({
            ordering: "managed",
        });
    }

    propertyMappings?: PaginatedMicrosoftEntraProviderMappingList;

    async send(data: MicrosoftEntraProvider): Promise<MicrosoftEntraProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraUpdate({
                id: this.instance.pk,
                microsoftEntraProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraCreate({
                microsoftEntraProviderRequest: data,
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
                        label=${msg("Client ID")}
                        ?required=${true}
                        name="clientId"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientId, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Client ID for the app registration.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Client Secret")}
                        ?required=${true}
                        name="clientSecret"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientSecret, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Client secret for the app registration.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Tenant ID")}
                        ?required=${true}
                        name="tenantId"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.tenantId, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("ID of the tenant accounts will be synced into.")}
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
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!this.instance?.propertyMappings) {
                                    selected =
                                        mapping.managed ===
                                            "goauthentik.io/providers/microsoft_entra/user" ||
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
                            ${msg("Property mappings used to user mapping.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="propertyMappingsGroup"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!this.instance?.propertyMappingsGroup) {
                                    selected =
                                        mapping.managed ===
                                        "goauthentik.io/providers/microsoft_entra/group";
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
                            ${msg("Property mappings used to group creation.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
