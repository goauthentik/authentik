import "#admin/groups/MemberSelectModal";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/chips/Chip";
import "#elements/chips/ChipGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { DataProvision, DualSelectPair } from "#elements/ak-dual-select/types";
import { ModelForm } from "#elements/forms/ModelForm";

import { CoreApi, Group, RbacApi, RelatedGroup, Role } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export function coreGroupPair(item: Group | RelatedGroup): DualSelectPair {
    return [item.pk, html`<div class="selection-main">${item.name}</div>`, item.name];
}
export function rbacRolePair(item: Role): DualSelectPair {
    return [item.pk, html`<div class="selection-main">${item.name}</div>`, item.name];
}

@customElement("ak-group-form")
export class GroupForm extends ModelForm<Group, string> {
    static styles: CSSResult[] = [
        ...super.styles,
        css`
            .pf-c-button.pf-m-control {
                height: 100%;
            }
            .pf-c-form-control {
                height: auto !important;
            }
        `,
    ];

    #fetchGroups = (page: number, search?: string): Promise<DataProvision> => {
        return new CoreApi(DEFAULT_CONFIG)
            .coreGroupsList({
                page: page,
                search: search,
            })
            .then((results) => {
                return {
                    pagination: results.pagination,
                    options: results.results.map(coreGroupPair),
                };
            });
    };
    #fetchRoles = (page: number, search?: string): Promise<DataProvision> => {
        return new RbacApi(DEFAULT_CONFIG)
            .rbacRolesList({
                page: page,
                search: search,
            })
            .then((results) => {
                return {
                    pagination: results.pagination,
                    options: results.results.map(rbacRolePair),
                };
            });
    };

    loadInstance(pk: string): Promise<Group> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsRetrieve({
            groupUuid: pk,
            includeUsers: false,
            includeParents: true,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated group.")
            : msg("Successfully created group.");
    }

    async send(data: Group): Promise<Group> {
        data.attributes ??= {};
        if (this.instance?.pk) {
            return new CoreApi(DEFAULT_CONFIG).coreGroupsPartialUpdate({
                groupUuid: this.instance.pk,
                patchedGroupRequest: data,
            });
        }
        data.users = [];
        return new CoreApi(DEFAULT_CONFIG).coreGroupsCreate({
            groupRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-text-input
                name="name"
                required
                placeholder=${msg("Type a group name...")}
                value="${ifDefined(this.instance?.name)}"
                label=${msg("Group Name")}
                autocomplete="off"
                spellcheck="false"
            ></ak-text-input>

            <ak-switch-input
                name="isSuperuser"
                label=${msg("Superuser Privileges")}
                ?checked=${this.instance?.isSuperuser ?? false}
                help=${msg("Whether users added to this group will have superuser privileges.")}
            >
            </ak-switch-input>

            <ak-form-element-horizontal label=${msg("Parents")} name="parents">
                <ak-dual-select-provider
                    .provider=${this.#fetchGroups}
                    .selected=${(this.instance?.parentsObj ?? []).map(coreGroupPair)}
                    available-label=${msg("Available Groups")}
                    selected-label=${msg("Selected Groups")}
                ></ak-dual-select-provider>
                <p class="pf-c-form__helper-text">
                    ${msg("A group recursively inherits every role from its ancestors.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Roles")} name="roles">
                <ak-dual-select-provider
                    .provider=${this.#fetchRoles}
                    .selected=${(this.instance?.rolesObj ?? []).map(rbacRolePair)}
                    available-label=${msg("Available Roles")}
                    selected-label=${msg("Selected Roles")}
                ></ak-dual-select-provider>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select roles to grant this groups' users' permissions from the selected roles.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(this.instance?.attributes ?? {})}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-form": GroupForm;
    }
}
