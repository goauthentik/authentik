import "#components/ak-number-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/ToggleGroup";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import {
    createPassFailOptions,
    PolicyBindingCheckTarget,
    PolicyObjectKeys,
} from "#common/policies/utils";

import type { SearchSelect } from "#elements/forms/SearchSelect/ak-search-select";
import { ToggleGroupEvent } from "#elements/ToggleGroup";

import { AKSearchSelect } from "#components/ak-search-select-field";
import { type NavigableButton, type WizardButton } from "#components/ak-wizard/shared";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import { groupSource, policySource, userSource } from "#admin/common/search-sources";

import { Group, Policy, PolicyBinding, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, query, state } from "lit/decorators.js";

/**
 * @property wizard - The current state of the application wizard, shared across all steps.
 */
@customElement("ak-application-wizard-edit-binding-step")
export class ApplicationWizardEditBindingStep extends ApplicationWizardStep<PolicyBinding> {
    label = msg("Edit Binding");

    hide = true;

    public get form(): HTMLFormElement | null {
        return this.renderRoot.querySelector("form#bindingform");
    }

    @query("ak-search-select")
    searchSelect!: SearchSelect<Policy> | SearchSelect<Group> | SearchSelect<User>;

    @state()
    policyGroupUser: PolicyBindingCheckTarget = PolicyBindingCheckTarget.Policy;

    protected instanceId = -1;

    protected instance: PolicyBinding | null = null;

    protected buttons: WizardButton[] = [
        { kind: "cancel" },
        { kind: "back", destination: "bindings" },
        { kind: "next", label: msg("Save Binding"), destination: "bindings" },
    ];

    public override handleButton(button: NavigableButton) {
        if (button.kind === "next") {
            if (!this.form?.checkValidity()) {
                return;
            }

            const policyObject = this.searchSelect.selectedObject;
            const policyKey = PolicyObjectKeys[this.policyGroupUser];

            const newBinding: PolicyBinding = {
                ...this.formValues,
                [policyKey]: policyObject,
            };

            const bindings = [...(this.wizard.bindings ?? [])];

            if (this.instanceId === -1) {
                bindings.push(newBinding);
            } else {
                bindings[this.instanceId] = newBinding;
            }

            this.instanceId = -1;

            return this.dispatchEvents({
                update: { bindings },
                destination: "bindings",
            });
        }

        return super.handleButton(button);
    }

    protected renderSearch(title: string, policyKind: PolicyBindingCheckTarget) {
        if (policyKind !== this.policyGroupUser) {
            return nothing;
        }

        const { instance } = this;
        const placeholder = msg(str`Select a ${title}...`);

        const search = (() => {
            switch (policyKind) {
                case PolicyBindingCheckTarget.Policy:
                    return AKSearchSelect({
                        name: policyKind,
                        source: policySource,
                        value: instance?.policy,
                        selectedObject: instance?.policyObj,
                        label: title,
                        placeholder,
                    });
                case PolicyBindingCheckTarget.Group:
                    return AKSearchSelect({
                        name: policyKind,
                        source: groupSource,
                        value: instance?.group,
                        selectedObject: instance?.groupObj,
                        label: title,
                        placeholder,
                    });
                case PolicyBindingCheckTarget.User:
                    return AKSearchSelect({
                        name: policyKind,
                        source: userSource,
                        value: instance?.user?.toString(),
                        selectedObject: instance?.userObj,
                        label: title,
                        placeholder,
                    });
            }
        })();

        return html`<ak-form-element-horizontal label=${title} name=${policyKind}>
            ${search}
        </ak-form-element-horizontal>`;
    }

    protected renderForm(instance?: PolicyBinding | null) {
        return html`<h3 class="pf-c-wizard__main-title">
                ${msg("Create a Policy/User/Group Binding")}
            </h3>
            <form id="bindingform" class="pf-c-form pf-m-horizontal" slot="form">
                <div class="pf-c-card pf-m-selectable pf-m-selected">
                    <div class="pf-c-card__body">
                        <ak-toggle-group
                            value=${this.policyGroupUser}
                            @ak-toggle=${(ev: ToggleGroupEvent<PolicyBindingCheckTarget>) => {
                                this.policyGroupUser = ev.value;
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
                    label=${msg("Negate Result")}
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
                    label=${msg("Failure Result")}
                    .options=${createPassFailOptions}
                    required
                ></ak-radio-input>
            </form>`;
    }

    protected renderMain() {
        if (!(this.wizard.bindings && this.wizard.errors)) {
            throw new Error("Application Step received uninitialized wizard context.");
        }

        const currentBinding = this.wizard.currentBinding ?? -1;

        if (this.instanceId !== currentBinding) {
            this.instanceId = currentBinding;
            this.instance = this.instanceId === -1 ? null : this.wizard.bindings[this.instanceId];
        }

        return this.renderForm(this.instance);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-edit-binding-step": ApplicationWizardEditBindingStep;
    }
}
