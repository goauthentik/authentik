import YAML from "yaml";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { CoreApi, Group, User } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/CodeMirror";
import "../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../elements/forms/ModelForm";
import { first } from "../../utils";
import "./GroupSelectModal";

@customElement("ak-user-form")
export class UserForm extends ModelForm<User, number> {
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

    loadInstance(pk: number): Promise<User> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated user.`;
        } else {
            return t`Successfully created user.`;
        }
    }

    send = (data: User): Promise<User> => {
        if (this.instance?.pk) {
            return new CoreApi(DEFAULT_CONFIG).coreUsersUpdate({
                id: this.instance.pk,
                userRequest: data,
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreUsersCreate({
                userRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Username`} ?required=${true} name="username">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.username)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`User's primary identifier. 150 characters or fewer.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Path`} ?required=${true} name="path">
                <input
                    type="text"
                    value="${first(this.instance?.path, "users")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Name`} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">${t`User's display name.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Email`} name="email">
                <input
                    type="email"
                    autocomplete="off"
                    value="${ifDefined(this.instance?.email)}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="isActive">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.isActive, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Is active`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Designates whether this user should be treated as active. Unselect this instead of deleting accounts.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Groups`} name="groups">
                <div class="pf-c-input-group">
                    <ak-user-group-select-table
                        .confirm=${(items: Group[]) => {
                            // Because the model only has the IDs, map the group list to IDs
                            const ids = items.map((g) => g.pk);
                            if (!this.instance) this.instance = {} as User;
                            this.instance.groups = Array.from(this.instance?.groups || []).concat(
                                ids,
                            );
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </button>
                    </ak-user-group-select-table>
                    <div class="pf-c-form-control">
                        <ak-chip-group>
                            ${until(
                                new CoreApi(DEFAULT_CONFIG)
                                    .coreGroupsList({
                                        ordering: "name",
                                    })
                                    .then((groups) => {
                                        return groups.results.map((group) => {
                                            const selected = Array.from(
                                                this.instance?.groups || [],
                                            ).some((sg) => {
                                                return sg == group.pk;
                                            });
                                            if (!selected) return;
                                            return html`<ak-chip
                                                .removable=${true}
                                                value=${ifDefined(group.pk)}
                                                @remove=${() => {
                                                    if (!this.instance) return;
                                                    const groups = Array.from(
                                                        this.instance?.groups || [],
                                                    );
                                                    const idx = groups.indexOf(group.pk);
                                                    groups.splice(idx, 1);
                                                    this.instance.groups = groups;
                                                    this.requestUpdate();
                                                }}
                                            >
                                                ${group.name}
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
