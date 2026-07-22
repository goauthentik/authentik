import "#components/ak-switch-input";
import "#components/ak-toggle-group";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";
import {
    createPassFailOptions,
    PolicyBindingCheckTarget,
    PolicyBindingCheckTargetToLabel,
} from "#common/policies/utils";
import { groupBy } from "#common/utils";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

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

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

export type PolicyBindingNotice = { type: PolicyBindingCheckTarget; notice: string };

export const pickPolicyGroupUser = (
    binding: Partial<PolicyBinding> | null | undefined,
    current: PolicyBindingCheckTarget,
): PolicyBindingCheckTarget =>
    match(binding)
        .with({ policyObj: P.nonNullable }, () => PolicyBindingCheckTarget.Policy)
        .with({ groupObj: P.nonNullable }, () => PolicyBindingCheckTarget.Group)
        .with({ userObj: P.nonNullable }, () => PolicyBindingCheckTarget.User)
        .otherwise(() => current);

export function cleanBindingForSend(
    data: PolicyBinding,
    type: PolicyBindingCheckTarget,
): PolicyBinding {
    switch (type) {
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
    return data;
}

@customElement("ak-policy-binding-form")
export class PolicyBindingForm<T extends PolicyBinding = PolicyBinding> extends ModelForm<
    T,
    string
> {
    public static styles: CSSResult[] = [...super.styles, PFContent];
    public static verboseName = msg("Policy Binding");
    public static verboseNamePlural = msg("Policy Bindings");

    async loadInstance(pk: string): Promise<T> {
        const binding = await aki(PoliciesApi).policiesBindingsRetrieve({
            policyBindingUuid: pk,
        });
        this.policyGroupUser = pickPolicyGroupUser(binding, this.policyGroupUser);
        return binding as T;
    }

    @property({ type: String })
    public targetPk = "";

    @state()
    public policyGroupUser: PolicyBindingCheckTarget = PolicyBindingCheckTarget.Policy;

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
        this.defaultOrder = await this.getOrder();
    }

    send(data: PolicyBinding): Promise<unknown> {
        if (this.targetPk) {
            data.target = this.targetPk;
        }

        data = cleanBindingForSend(data, this.policyGroupUser);

        if (this.instance?.pk) {
            return aki(PoliciesApi).policiesBindingsUpdate({
                policyBindingUuid: this.instance.pk,
                policyBindingRequest: data,
            });
        }
        return aki(PoliciesApi).policiesBindingsCreate({
            policyBindingRequest: data,
        });
    }

    async getOrder(): Promise<number> {
        if (this.instance?.pk) {
            return this.instance.order;
        }
        const bindings = await aki(PoliciesApi).policiesBindingsList({
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
            ${Object.values(PolicyBindingCheckTarget).map((ct) => {
                if (this.allowedTypes.includes(ct)) {
                    return html`<option value=${ct}>
                        ${PolicyBindingCheckTargetToLabel(ct)}
                    </option>`;
                }
                return nothing;
            })}
        </ak-toggle-group>`;
    }

    protected renderTarget() {
        return html`<ak-form-element-horizontal
                name="policy"
                ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.Policy}
            >
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "policy",
                    },
                    msg("Policy"),
                )}
                <ak-search-select
                    id="policy"
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
                        const policies = await aki(PoliciesApi).policiesAllList(args);
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
                name="group"
                ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.Group}
            >
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "group",
                    },
                    msg("Group"),
                )}
                <ak-search-select
                    id="group"
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                            includeUsers: false,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await aki(CoreApi).coreGroupsList(args);
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
                name="user"
                ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.User}
            >
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "user",
                    },
                    msg("User"),
                )}
                <ak-search-select
                    id="user"
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await aki(CoreApi).coreUsersList(args);
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
            </ak-form-element-horizontal>`;
    }

    protected override renderForm(): TemplateResult {
        return html`${this.allowedTypes.length > 1
                ? html`<div class="pf-c-card pf-m-selectable pf-m-selected">
                      <div class="pf-c-card__body">${this.renderModeSelector()}</div>
                      <div class="pf-c-card__footer">${this.renderTarget()}</div>
                  </div>`
                : this.renderTarget()}
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            >
            </ak-switch-input>
            <ak-switch-input
                name="negate"
                label=${msg("Negate Result")}
                ?checked=${this.instance?.negate ?? false}
                help=${msg("Negates the outcome of the binding. Messages are unaffected.")}
            >
            </ak-switch-input>
            <ak-form-element-horizontal required name="order">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "order",
                        required: true,
                    },
                    msg("Order"),
                )}
                <input
                    id="order"
                    type="number"
                    value="${this.instance?.order ?? this.defaultOrder}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal required name="timeout">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "timeout",
                        required: true,
                    },
                    msg("Timeout"),
                )}
                <input
                    id="timeout"
                    type="number"
                    value="${this.instance?.timeout ?? 30}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="failureResult" required>
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "failureResult",
                        required: true,
                    },
                    msg("Failure Result"),
                )}
                <ak-radio
                    id="failureResult"
                    .options=${createPassFailOptions}
                    .value=${this.instance?.failureResult}
                >
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
