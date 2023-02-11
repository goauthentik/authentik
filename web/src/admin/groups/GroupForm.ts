import "@goauthentik/admin/groups/MemberSelectModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/chips/Chip";
import "@goauthentik/elements/chips/ChipGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import { UserOption } from "@goauthentik/elements/user/utils";
import YAML from "yaml";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { CoreApi, CoreGroupsListRequest, Group, User } from "@goauthentik/api";

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
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated group.`;
        } else {
            return t`Successfully created group.`;
        }
    }

    send = (data: Group): Promise<Group> => {
        if (this.instance?.pk) {
            return new CoreApi(DEFAULT_CONFIG).coreGroupsUpdate({
                groupUuid: this.instance.pk,
                groupRequest: data,
            });
        } else {
            data.users = Array.from(this.instance?.users || []);
            return new CoreApi(DEFAULT_CONFIG).coreGroupsCreate({
                groupRequest: data,
            });
        }
    };

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
                    <span class="pf-c-switch__label">${t`Is superuser`}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${t`Users added to this group will be superusers.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Parent`} name="parent">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
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
            <ak-form-element-horizontal label=${t`Members`} name="users">
                <div class="pf-c-input-group">
                    <ak-group-member-select-table
                        .confirm=${(items: User[]) => {
                            // Because the model only has the IDs, map the user list to IDs
                            const ids = items.map((u) => u.pk || 0);
                            if (!this.instance) this.instance = {} as Group;
                            this.instance.users = Array.from(this.instance?.users || []).concat(
                                ids,
                            );
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </button>
                    </ak-group-member-select-table>
                    <div class="pf-c-form-control">
                        <ak-chip-group>
                            ${until(
                                new CoreApi(DEFAULT_CONFIG)
                                    .coreUsersList({
                                        ordering: "username",
                                    })
                                    .then((users) => {
                                        return users.results.map((user) => {
                                            const selected = Array.from(
                                                this.instance?.users || [],
                                            ).some((su) => {
                                                return su == user.pk;
                                            });
                                            if (!selected) return;
                                            return html`<ak-chip
                                                .removable=${true}
                                                value=${ifDefined(user.pk)}
                                                @remove=${() => {
                                                    if (!this.instance) return;
                                                    const users = Array.from(
                                                        this.instance?.users || [],
                                                    );
                                                    const idx = users.indexOf(user.pk || 0);
                                                    users.splice(idx, 1);
                                                    this.instance.users = users;
                                                    this.requestUpdate();
                                                }}
                                            >
                                                ${UserOption(user)}
                                            </ak-chip>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </ak-chip-group>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Attributes`} ?required=${true} name="attributes">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(first(this.instance?.attributes, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Set custom attributes using YAML or JSON.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
