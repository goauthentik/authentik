import "#components/ak-switch-input";
import "#components/ak-toggle-group";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { ModelForm } from "#elements/forms/ModelForm";

import {
    createPassFailOptions,
    PolicyBindingCheckTarget,
    PolicyBindingCheckTargetToLabel,
} from "#admin/policies/utils";

import {
    CoreApi,
    CoreGroupsListRequest,
    CoreUsersListRequest,
    Group,
    PoliciesAllListRequest,
    PoliciesApi,
    Policy,
    PolicyBinding,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

export type PolicyBindingNotice = { type: PolicyBindingCheckTarget; notice: string };

@customElement("ak-policy-binding-form")
export class PolicyBindingForm<T extends PolicyBinding = PolicyBinding> extends ModelForm<
    T,
    string
> {
    static styles: CSSResult[] = [...super.styles, PFContent];

    async loadInstance(pk: string): Promise<T> {
        const binding = await new PoliciesApi(DEFAULT_CONFIG).policiesBindingsRetrieve({
            policyBindingUuid: pk,
        });
        if (binding?.policyObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.Policy;
        }
        if (binding?.groupObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.Group;
        }
        if (binding?.userObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.User;
        }
        this.defaultOrder = await this.getOrder();
        return binding as T;
    }

    @property({ type: String })
    public targetPk = "";

    @state()
    protected policyGroupUser: PolicyBindingCheckTarget = PolicyBindingCheckTarget.Policy;

    @property({ type: Array })
    public allowedTypes: PolicyBindingCheckTarget[] = [
        PolicyBindingCheckTarget.Policy,
        PolicyBindingCheckTarget.Group,
        PolicyBindingCheckTarget.User,
    ];

    @property({ type: Array })
    public typeNotices: PolicyBindingNotice[] = [];

    @state()
    protected defaultOrder = 0;

    public override reset(): void {
        super.reset();

        this.policyGroupUser = PolicyBindingCheckTarget.Policy;
        this.defaultOrder = 0;
    }

    getSuccessMessage(): string {
        if (this.instance?.pk) {
            return msg("Successfully updated binding.");
        }
        return msg("Successfully created binding.");
    }

    async load(): Promise<void> {
        // Overwrite the default for policyGroupUser with the first allowed type,
        // as this function is called when the correct parameters are set
        this.policyGroupUser = this.allowedTypes[0];
    }

    send(data: PolicyBinding): Promise<unknown> {
        if (this.targetPk) {
            data.target = this.targetPk;
        }
        switch (this.policyGroupUser) {
            case PolicyBindingCheckTarget.Policy:
                data.user = null;
                data.group = null;
                break;
            case PolicyBindingCheckTarget.Group:
                data.policy = null;
                data.user = null;
                break;
            case PolicyBindingCheckTarget.User:
                data.policy = null;
                data.group = null;
                break;
        }

        if (this.instance?.pk) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsUpdate({
                policyBindingUuid: this.instance.pk,
                policyBindingRequest: data,
            });
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsCreate({
            policyBindingRequest: data,
        });
    }

    async getOrder(): Promise<number> {
        if (this.instance?.pk) {
            return this.instance.order;
        }
        const bindings = await new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            target: this.targetPk || "",
        });
        const orders = bindings.results.map((binding) => binding.order);
        if (orders.length < 1) {
            return 0;
        }
        return Math.max(...orders) + 1;
    }

    renderModeSelector(): TemplateResult {
        return html` <ak-toggle-group
            value=${this.policyGroupUser}
            @ak-toggle=${(ev: CustomEvent<{ value: PolicyBindingCheckTarget }>) => {
                this.policyGroupUser = ev.detail.value;
            }}
        >
            ${Object.keys(PolicyBindingCheckTarget).map((ct) => {
                if (this.allowedTypes.includes(ct.toLowerCase() as PolicyBindingCheckTarget)) {
                    return html`<option value=${ct.toLowerCase()}>
                        ${PolicyBindingCheckTargetToLabel(
                            ct.toLowerCase() as PolicyBindingCheckTarget,
                        )}
                    </option>`;
                }
                return nothing;
            })}
        </ak-toggle-group>`;
    }

    protected override renderForm(): TemplateResult {
        return html` <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">${this.renderModeSelector()}</div>
                <div class="pf-c-card__footer">
                    <ak-form-element-horizontal
                        label=${msg("Policy")}
                        name="policy"
                        ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.Policy}
                    >
                        <ak-search-select
                            .groupBy=${(items: Policy[]) => {
                                return groupBy(items, (policy) => policy.verboseNamePlural);
                            }}
                            .fetchObjects=${async (query?: string): Promise<Policy[]> => {
                                const args: PoliciesAllListRequest = {
                                    ordering: "name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const policies = await new PoliciesApi(
                                    DEFAULT_CONFIG,
                                ).policiesAllList(args);
                                return policies.results;
                            }}
                            .renderElement=${(policy: Policy) => policy.name}
                            .value=${(policy: Policy | null) => policy?.pk}
                            .selected=${(policy: Policy) => policy.pk === this.instance?.policy}
                            blankable
                        >
                        </ak-search-select>
                        ${this.typeNotices
                            .filter(({ type }) => type === PolicyBindingCheckTarget.Policy)
                            .map((msg) => {
                                return html`<p class="pf-c-form__helper-text">${msg.notice}</p>`;
                            })}
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group")}
                        name="group"
                        ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.Group}
                    >
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
                            .value=${(group: Group | null) => String(group?.pk ?? "")}
                            .selected=${(group: Group) => group.pk === this.instance?.group}
                            blankable
                        >
                        </ak-search-select>
                        ${this.typeNotices
                            .filter(({ type }) => type === PolicyBindingCheckTarget.Group)
                            .map((msg) => {
                                return html`<p class="pf-c-form__helper-text">${msg.notice}</p>`;
                            })}
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("User")}
                        name="user"
                        ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.User}
                    >
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
                            .renderElement=${(user: User) => user.username}
                            .renderDescription=${(user: User) => html`${user.name}`}
                            .value=${(user: User | null) => user?.pk}
                            .selected=${(user: User) => user.pk === this.instance?.user}
                            blankable
                        >
                        </ak-search-select>
                        ${this.typeNotices
                            .filter(({ type }) => type === PolicyBindingCheckTarget.User)
                            .map((msg) => {
                                return html`<p class="pf-c-form__helper-text">${msg.notice}</p>`;
                            })}
                    </ak-form-element-horizontal>
                </div>
            </div>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            >
            </ak-switch-input>
            <ak-switch-input
                name="negate"
                label=${msg("Negate result")}
                ?checked=${this.instance?.negate ?? false}
                help=${msg("Negates the outcome of the binding. Messages are unaffected.")}
            >
            </ak-switch-input>
            <ak-form-element-horizontal label=${msg("Order")} required name="order">
                <input
                    type="number"
                    value="${this.instance?.order ?? this.defaultOrder}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Timeout")} required name="timeout">
                <input
                    type="number"
                    value="${this.instance?.timeout ?? 30}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="failureResult" label=${msg("Failure result")}>
                <ak-radio .options=${createPassFailOptions} .value=${this.instance?.failureResult}>
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Result used when policy execution fails.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-binding-form": PolicyBindingForm;
    }
}
