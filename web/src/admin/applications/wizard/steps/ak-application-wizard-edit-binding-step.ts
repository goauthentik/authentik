import "#components/ak-number-input";
import "#admin/applications/wizard/ak-wizard-title";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#components/ak-toggle-group";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/ak-search-select-ez";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { ISearchSelectConfig } from "#elements/forms/SearchSelect/ak-search-select-ez";
import { type SearchSelectBase } from "#elements/forms/SearchSelect/SearchSelect";

import { type NavigableButton, type WizardButton } from "#components/ak-wizard/types";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import {
    createPassFailOptions,
    PolicyBindingCheckTarget,
    PolicyObjectKeys,
} from "#admin/policies/utils";

import { CoreApi, Group, PoliciesApi, Policy, PolicyBinding, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, query, state } from "lit/decorators.js";

const withQuery = <T>(search: string | undefined, args: T) => (search ? { ...args, search } : args);

@customElement("ak-application-wizard-edit-binding-step")
export class ApplicationWizardEditBindingStep extends ApplicationWizardStep {
    label = msg("Edit Binding");

    hide = true;

    public get form(): HTMLFormElement | null {
        return this.renderRoot.querySelector("form#bindingform");
    }

    @query(".policy-search-select")
    searchSelect!: SearchSelectBase<Policy> | SearchSelectBase<Group> | SearchSelectBase<User>;

    @state()
    policyGroupUser: PolicyBindingCheckTarget = PolicyBindingCheckTarget.Policy;

    instanceId = -1;

    instance?: PolicyBinding;

    get buttons(): WizardButton[] {
        return [
            { kind: "next", label: msg("Save Binding"), destination: "bindings" },
            { kind: "back", destination: "bindings" },
            { kind: "cancel" },
        ];
    }

    override handleButton(button: NavigableButton) {
        if (button.kind === "next") {
            if (!this.form?.checkValidity()) {
                return;
            }

            const policyObject = this.searchSelect.selectedObject;
            const policyKey = PolicyObjectKeys[this.policyGroupUser];
            const newBinding: PolicyBinding = {
                ...(this.formValues as unknown as PolicyBinding),
                [policyKey]: policyObject,
            };

            const bindings = [...(this.wizard.bindings ?? [])];

            if (this.instanceId === -1) {
                bindings.push(newBinding);
            } else {
                bindings[this.instanceId] = newBinding;
            }

            this.instanceId = -1;
            this.handleUpdate({ bindings }, "bindings");

            return;
        }

        super.handleButton(button);
    }

    // The search select configurations for the three different types of fetches that we care about,
    // policy, user, and group, all using the SearchSelectEZ protocol.
    searchSelectConfigs(
        kind: PolicyBindingCheckTarget,
    ): ISearchSelectConfig<Policy> | ISearchSelectConfig<Group> | ISearchSelectConfig<User> {
        switch (kind) {
            case PolicyBindingCheckTarget.Policy:
                return {
                    fetchObjects: async (query) => {
                        const policies = await new PoliciesApi(DEFAULT_CONFIG).policiesAllList(
                            withQuery(query, {
                                ordering: "name",
                            }),
                        );

                        return policies.results;
                    },
                    groupBy: (items) => groupBy(items, (policy) => policy.verboseNamePlural),
                    renderElement: (policy): string => policy.name,
                    value: (policy) => policy?.pk ?? "",
                    selected: (policy) => policy.pk === this.instance?.policy,
                } satisfies ISearchSelectConfig<Policy>;

            case PolicyBindingCheckTarget.Group:
                return {
                    fetchObjects: async (query) => {
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(
                            withQuery(query, {
                                ordering: "name",
                                includeUsers: false,
                            }),
                        );

                        return groups.results;
                    },
                    renderElement: (group) => group.name,
                    value: (group) => group?.pk ?? "",
                    selected: (group) => group.pk === this.instance?.group,
                } satisfies ISearchSelectConfig<Group>;
            case PolicyBindingCheckTarget.User:
                return {
                    fetchObjects: async (query) => {
                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(
                            withQuery(query, {
                                ordering: "username",
                            }),
                        );

                        return users.results;
                    },
                    renderElement: (user): string => user.username,
                    renderDescription: (user) => html`${user.name}`,
                    value: (user) => String(user?.pk ?? ""),
                    selected: (user) => user.pk === this.instance?.user,
                } satisfies ISearchSelectConfig<User>;

            default:
                throw new Error(`Unrecognized policy binding target ${kind}`);
        }
    }

    renderSearch(title: string, policyKind: PolicyBindingCheckTarget) {
        if (policyKind !== this.policyGroupUser) {
            return nothing;
        }

        return html`<ak-form-element-horizontal label=${title} name=${policyKind}>
            <ak-search-select-ez
                .config=${this.searchSelectConfigs(policyKind)}
                class="policy-search-select"
                blankable
            ></ak-search-select-ez>
        </ak-form-element-horizontal>`;
    }

    renderForm(instance?: PolicyBinding) {
        return html`<ak-wizard-title>${msg("Create a Policy/User/Group Binding")}</ak-wizard-title>
            <form id="bindingform" class="pf-c-form pf-m-horizontal" slot="form">
                <div class="pf-c-card pf-m-selectable pf-m-selected">
                    <div class="pf-c-card__body">
                        <ak-toggle-group
                            value=${this.policyGroupUser}
                            @ak-toggle=${(ev: CustomEvent<{ value: PolicyBindingCheckTarget }>) => {
                                this.policyGroupUser = ev.detail.value;
                            }}
                        >
                            <option value=${PolicyBindingCheckTarget.Policy}>
                                ${msg("Policy")}
                            </option>
                            <option value=${PolicyBindingCheckTarget.Group}>${msg("Group")}</option>
                            <option value=${PolicyBindingCheckTarget.User}>${msg("User")}</option>
                        </ak-toggle-group>
                    </div>
                    <div class="pf-c-card__footer">
                        ${this.renderSearch(msg("Policy"), PolicyBindingCheckTarget.Policy)}
                        ${this.renderSearch(msg("Group"), PolicyBindingCheckTarget.Group)}
                        ${this.renderSearch(msg("User"), PolicyBindingCheckTarget.User)}
                    </div>
                </div>
                <ak-switch-input
                    name="enabled"
                    ?checked=${instance?.enabled ?? true}
                    label=${msg("Enabled")}
                ></ak-switch-input>
                <ak-switch-input
                    name="negate"
                    ?checked=${instance?.negate ?? false}
                    label=${msg("Negate result")}
                    help=${msg("Negates the outcome of the binding. Messages are unaffected.")}
                ></ak-switch-input>
                <ak-number-input
                    label=${msg("Order")}
                    name="order"
                    value="${instance?.order ?? 0}"
                    required
                ></ak-number-input>
                <ak-number-input
                    label=${msg("Timeout")}
                    name="timeout"
                    value="${instance?.timeout ?? 30}"
                    required
                ></ak-number-input>
                <ak-radio-input
                    name="failureResult"
                    label=${msg("Failure result")}
                    .options=${createPassFailOptions}
                ></ak-radio-input>
            </form>`;
    }

    renderMain() {
        if (!(this.wizard.bindings && this.wizard.errors)) {
            throw new Error("Application Step received uninitialized wizard context.");
        }
        const currentBinding = this.wizard.currentBinding ?? -1;
        if (this.instanceId !== currentBinding) {
            this.instanceId = currentBinding;
            this.instance =
                this.instanceId === -1 ? undefined : this.wizard.bindings[this.instanceId];
        }
        return this.renderForm(this.instance);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-edit-binding-step": ApplicationWizardEditBindingStep;
    }
}
