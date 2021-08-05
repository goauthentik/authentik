import { CoreApi, Group, User } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import "../../elements/chips/ChipGroup";
import "../../elements/chips/Chip";
import "./MemberSelectModal";
import YAML from "yaml";
import { first } from "../../utils";
import { ModelForm } from "../../elements/forms/ModelForm";

@customElement("ak-group-form")
export class GroupForm extends ModelForm<Group, string> {
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
                groupUuid: this.instance.pk || "",
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
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.isSuperuser, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Is superuser`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Users added to this group will be superusers.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Parent`} name="parent">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.parent === undefined}>
                        ---------
                    </option>
                    ${until(
                        new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then((groups) => {
                            return groups.results.map((group) => {
                                return html`<option
                                    value=${ifDefined(group.pk)}
                                    ?selected=${this.instance?.parent === group.pk}
                                >
                                    ${group.name}
                                </option>`;
                            });
                        }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
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
                                                ${user.username}
                                            </ak-chip>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </ak-chip-group>
                    </div>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Hold control/command to select multiple items.`}
                </p>
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
