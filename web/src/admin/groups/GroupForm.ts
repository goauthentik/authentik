import "@goauthentik/admin/groups/MemberSelectModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { first } from "@goauthentik/common/utils.js";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider";
import { DataProvision, DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";
import "@goauthentik/elements/chips/Chip";
import "@goauthentik/elements/chips/ChipGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, CoreGroupsListRequest, Group, RbacApi, Role } from "@goauthentik/api";

export function rbacRolePair(item: Role): DualSelectPair {
    return [item.pk, html`<div class="selection-main">${item.name}</div>`, item.name];
}

@customElement("ak-group-form")
export class GroupForm extends ModelForm<Group, string> {
    static get styles(): CSSResult[] {
        return super.styles.concat(css`
            .pf-c-button.pf-m-control {
                height: 100%;
            }
            .pf-c-form-control {
                height: auto !important;
            }
        `);
    }

    loadInstance(pk: string): Promise<Group> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsRetrieve({
            groupUuid: pk,
            includeUsers: false,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated group.")
            : msg("Successfully created group.");
    }

    async send(data: Group): Promise<Group> {
        if (this.instance?.pk) {
            return new CoreApi(DEFAULT_CONFIG).coreGroupsPartialUpdate({
                groupUuid: this.instance.pk,
                patchedGroupRequest: data,
            });
        } else {
            data.users = [];
            return new CoreApi(DEFAULT_CONFIG).coreGroupsCreate({
                groupRequest: data,
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
            <ak-form-element-horizontal name="isSuperuser">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.isSuperuser, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Is superuser")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Users added to this group will be superusers.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Parent")} name="parent">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
                        if (this.instance) {
                            return groups.results.filter((g) => g.pk !== this.instance?.pk);
                        }
                        return groups.results;
                    }}
                    .renderElement=${(group: Group): string => {
                        return group.name;
                    }}
                    .value=${(group: Group | undefined): string | undefined => {
                        return group?.pk;
                    }}
                    .selected=${(group: Group): boolean => {
                        return group.pk === this.instance?.parent;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Roles")} name="roles">
                <ak-dual-select-provider
                    .provider=${(page: number, search?: string): Promise<DataProvision> => {
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
                    }}
                    .selected=${(this.instance?.rolesObj ?? []).map(rbacRolePair)}
                    available-label="${msg("Available Roles")}"
                    selected-label="${msg("Selected Roles")}"
                ></ak-dual-select-provider>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select roles to grant this groups' users' permissions from the selected roles.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Attributes")}
                ?required=${true}
                name="attributes"
            >
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    value="${YAML.stringify(first(this.instance?.attributes, {}))}"
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
