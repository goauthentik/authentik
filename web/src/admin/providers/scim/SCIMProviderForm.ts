import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    PaginatedSCIMMappingList,
    PropertymappingsApi,
    ProvidersApi,
    SCIMProvider,
} from "@goauthentik/api";

@customElement("ak-provider-scim-form")
export class SCIMProviderFormPage extends ModelForm<SCIMProvider, number> {
    loadInstance(pk: number): Promise<SCIMProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimRetrieve({
            id: pk,
        });
    }

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsScimList({
            ordering: "managed",
        });
    }

    propertyMappings?: PaginatedSCIMMappingList;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    async send(data: SCIMProvider): Promise<SCIMProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersScimUpdate({
                id: this.instance.pk || 0,
                sCIMProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersScimCreate({
                sCIMProviderRequest: data,
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
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`URL`} ?required=${true} name="url">
                        <input
                            type="text"
                            value="${first(this.instance?.url, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`SCIM base url, usually ends in /v2.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Token`} ?required=${true} name="token">
                        <input
                            type="text"
                            value="${first(this.instance?.token, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Token to authenticate with. Currently only bearer authentication is supported.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header">${t`User filtering`}</span>
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
                            <span class="pf-c-switch__label">${t`Exclude service accounts`}</span>
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Group`} name="filterGroup">
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
                                return group.pk === this.instance?.filterGroup;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Only sync users within the selected group.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header"> ${t`Attribute mapping`} </span>
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
                                        mapping.managed === "goauthentik.io/providers/scim/user" ||
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
                            ${t`Property mappings used to user mapping.`}
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
                                        mapping.managed === "goauthentik.io/providers/scim/group";
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
        </form>`;
    }
}
