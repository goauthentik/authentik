import "#components/ak-switch-input";
import "#elements/ToggleGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import PFContent from "@patternfly/patternfly/components/Content/content.css";

import { aki } from "#common/api/client";
import {
    createPassFailOptions,
    PolicyBindingCheckTarget,
    PolicyBindingCheckTargetToLabel,
} from "#common/policies/utils";

import { ModelForm } from "#elements/forms/ModelForm";
import { ToggleGroupEvent } from "#elements/ToggleGroup";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { groupSource, policySource, userSource } from "#admin/common/search-sources";

import { Group, PoliciesApi, PolicyBinding, User } from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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
            @ak-toggle=${(ev: ToggleGroupEvent<PolicyBindingCheckTarget>) => {
                this.policyGroupUser = ev.value;
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
                label=${msg("Policy")}
                name="policy"
                ?hidden=${this.policyGroupUser !== PolicyBindingCheckTarget.Policy}
            >
                ${AKSearchSelect({
                    name: "policy",
                    source: policySource,
                    value: this.instance?.policy,
                    selectedObject: this.instance?.policyObj,
                    blankable: true,
                })}
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
                ${AKSearchSelect({
                    name: "group",
                    source: groupSource,
                    value: this.instance?.group,
                    selectedObject: this.instance?.groupObj as Group | null | undefined,
                    blankable: true,
                })}
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
                ${AKSearchSelect({
                    name: "user",
                    source: userSource,
                    value: this.instance?.user?.toString(),
                    selectedObject: this.instance?.userObj as User | null | undefined,
                    blankable: true,
                })}
                ${this.typeNotices
                    .filter(({ type }) => type === PolicyBindingCheckTarget.User)
                    .map((msg) => {
                        return html`<p class="pf-c-form__helper-text">${msg.notice}</p>`;
                    })}
            </ak-form-element-horizontal>`;
    }

    protected override renderForm(): TemplateResult {
        return html`${
                this.allowedTypes.length > 1
                    ? html`<div class="pf-c-card pf-m-selectable pf-m-selected">
                          <div class="pf-c-card__body">${this.renderModeSelector()}</div>
                          <div class="pf-c-card__footer">${this.renderTarget()}</div>
                      </div>`
                    : this.renderTarget()
            }
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            >
            </ak-switch-input>
            <ak-switch-input
                name="dryRun"
                label=${msg("Dry-run", { id: "policies.bindings.dry-run.label" })}
                ?checked=${this.instance?.dryRun ?? false}
                help=${msg(
                    "Evaluate this binding without including its result or messages in the final decision. Results are recorded in the Event Log. Policy side effects are not prevented.",
                    { id: "policies.bindings.dry-run.description" },
                )}
            >
            </ak-switch-input>
            <ak-switch-input
                name="negate"
                label=${msg("Negate Result")}
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
            <ak-form-element-horizontal
                name="failureResult"
                label=${msg("Failure Result")}
                required
            >
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
