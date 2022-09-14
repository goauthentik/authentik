import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/SearchSelect";
import "@goauthentik/web/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/web/elements/forms/ModelForm";
import { UserOption } from "@goauthentik/web/elements/user/utils";
import { first, groupBy } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

import { CSSResult, css } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFToggleGroup from "@patternfly/patternfly/components/ToggleGroup/toggle-group.css";

import {
    CoreApi,
    CoreGroupsListRequest,
    CoreUsersListRequest,
    Group,
    PoliciesApi,
    Policy,
    PolicyBinding,
    User,
} from "@goauthentik/api";

enum target {
    policy,
    group,
    user,
}

@customElement("ak-policy-binding-form")
export class PolicyBindingForm extends ModelForm<PolicyBinding, string> {
    loadInstance(pk: string): Promise<PolicyBinding> {
        return new PoliciesApi(DEFAULT_CONFIG)
            .policiesBindingsRetrieve({
                policyBindingUuid: pk,
            })
            .then((binding) => {
                if (binding?.policyObj) {
                    this.policyGroupUser = target.policy;
                }
                if (binding?.groupObj) {
                    this.policyGroupUser = target.group;
                }
                if (binding?.userObj) {
                    this.policyGroupUser = target.user;
                }
                return binding;
            });
    }

    @property()
    targetPk?: string;

    @property({ type: Number })
    policyGroupUser: target = target.policy;

    @property({ type: Boolean })
    policyOnly = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated binding.`;
        } else {
            return t`Successfully created binding.`;
        }
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFToggleGroup,
            PFContent,
            css`
                .pf-c-toggle-group {
                    justify-content: center;
                }
            `,
        );
    }

    send = (data: PolicyBinding): Promise<PolicyBinding> => {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsUpdate({
                policyBindingUuid: this.instance.pk || "",
                policyBindingRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsCreate({
                policyBindingRequest: data,
            });
        }
    };

    groupPolicies(policies: Policy[]): TemplateResult {
        return html`
            ${groupBy<Policy>(policies, (p) => p.verboseName || "").map(([group, policies]) => {
                return html`<optgroup label=${group}>
                    ${policies.map((p) => {
                        const selected = this.instance?.policy === p.pk;
                        return html`<option ?selected=${selected} value=${ifDefined(p.pk)}>
                            ${p.name}
                        </option>`;
                    })}
                </optgroup>`;
            })}
        `;
    }

    getOrder(): Promise<number> {
        if (this.instance) {
            return Promise.resolve(this.instance.order);
        }
        return new PoliciesApi(DEFAULT_CONFIG)
            .policiesBindingsList({
                target: this.targetPk || "",
            })
            .then((bindings) => {
                const orders = bindings.results.map((binding) => binding.order);
                if (orders.length < 1) {
                    return 0;
                }
                return Math.max(...orders) + 1;
            });
    }

    renderModeSelector(): TemplateResult {
        return html` <div class="pf-c-toggle-group__item">
                <button
                    class="pf-c-toggle-group__button ${this.policyGroupUser === target.policy
                        ? "pf-m-selected"
                        : ""}"
                    type="button"
                    @click=${() => {
                        this.policyGroupUser = target.policy;
                    }}
                >
                    <span class="pf-c-toggle-group__text">${t`Policy`}</span>
                </button>
            </div>
            <div class="pf-c-divider pf-m-vertical" role="separator"></div>
            <div class="pf-c-toggle-group__item">
                <button
                    class="pf-c-toggle-group__button ${this.policyGroupUser === target.group
                        ? "pf-m-selected"
                        : ""}"
                    type="button"
                    @click=${() => {
                        this.policyGroupUser = target.group;
                    }}
                >
                    <span class="pf-c-toggle-group__text">${t`Group`}</span>
                </button>
            </div>
            <div class="pf-c-divider pf-m-vertical" role="separator"></div>
            <div class="pf-c-toggle-group__item">
                <button
                    class="pf-c-toggle-group__button ${this.policyGroupUser === target.user
                        ? "pf-m-selected"
                        : ""}"
                    type="button"
                    @click=${() => {
                        this.policyGroupUser = target.user;
                    }}
                >
                    <span class="pf-c-toggle-group__text">${t`User`}</span>
                </button>
            </div>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">
                    <div class="pf-c-toggle-group">${this.renderModeSelector()}</div>
                </div>
                <div class="pf-c-card__footer">
                    <ak-form-element-horizontal
                        label=${t`Policy`}
                        name="policy"
                        ?hidden=${this.policyGroupUser !== target.policy}
                    >
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.policy === undefined}>
                                ---------
                            </option>
                            ${until(
                                new PoliciesApi(DEFAULT_CONFIG)
                                    .policiesAllList({
                                        ordering: "name",
                                    })
                                    .then((policies) => {
                                        return this.groupPolicies(policies.results);
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group`}
                        name="group"
                        ?hidden=${this.policyGroupUser !== target.group}
                    >
                        <!-- @ts-ignore -->
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
                                return group.pk === this.instance?.group;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        ${this.policyOnly
                            ? html`<p class="pf-c-form__helper-text">
                                  ${t`Group mappings can only be checked if a user is already logged in when trying to access this source.`}
                              </p>`
                            : html``}
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`User`}
                        name="user"
                        ?hidden=${this.policyGroupUser !== target.user}
                    >
                        <!-- @ts-ignore -->
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<User[]> => {
                                const args: CoreUsersListRequest = {
                                    ordering: "username",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                                return users.results;
                            }}
                            .renderElement=${(user: User): string => {
                                return UserOption(user);
                            }}
                            .value=${(user: User | undefined): number | undefined => {
                                return user ? user.pk : undefined;
                            }}
                            .selected=${(user: User): boolean => {
                                return user.pk === this.instance?.user;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        ${this.policyOnly
                            ? html`<p class="pf-c-form__helper-text">
                                  ${t`User mappings can only be checked if a user is already logged in when trying to access this source.`}
                              </p>`
                            : html``}
                    </ak-form-element-horizontal>
                </div>
            </div>
            <input
                required
                name="target"
                type="hidden"
                value=${ifDefined(this.instance?.target || this.targetPk)}
            />
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Enabled`} </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="negate">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.negate, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Negate result`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Negates the outcome of the binding. Messages are unaffected.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Order`} ?required=${true} name="order">
                <!-- @ts-ignore -->
                <input
                    type="number"
                    value="${until(this.getOrder())}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Timeout`} ?required=${true} name="timeout">
                <input
                    type="number"
                    value="${first(this.instance?.timeout, 30)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
