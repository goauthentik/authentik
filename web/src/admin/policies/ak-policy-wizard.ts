import "#admin/policies/dummy/DummyPolicyForm";
import "#admin/policies/event_matcher/EventMatcherPolicyForm";
import "#admin/policies/expiry/ExpiryPolicyForm";
import "#admin/policies/expression/ExpressionPolicyForm";
import "#admin/policies/geoip/GeoIPPolicyForm";
import "#admin/policies/password/PasswordPolicyForm";
import "#admin/policies/reputation/ReputationPolicyForm";
import "#admin/policies/unique_password/UniquePasswordPolicyForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";
import "#elements/forms/FormGroup";
import "#admin/policies/PolicyBindingForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PolicyBindingCheckTarget } from "#common/policies/utils";

import { RadioChangeEventDetail, RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { FormWizardPage } from "#elements/wizard/FormWizardPage";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import {
    PoliciesApi,
    Policy,
    PolicyBinding,
    PolicyBindingRequest,
    TypeCreate,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

const initialStep = "initial";

@customElement("ak-policy-wizard")
export class PolicyWizard extends CreateWizard {
    protected policiesAPI = new PoliciesApi(DEFAULT_CONFIG);

    @property({ type: Boolean })
    public showBindingPage = false;

    @property()
    public bindingTarget: string | null = null;

    public override groupLabel = msg("Choose Policy Type");
    public override groupDescription = msg("Select the type of policy you want to create.");

    public override initialSteps = this.showBindingPage
        ? ["initial", "create-binding"]
        : ["initial"];

    public static override verboseName = msg("Policy");
    public static override verboseNamePlural = msg("Policies");

    public override layout = TypeCreateWizardPageLayouts.list;

    protected override apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.policiesAPI.policiesAllTypesList(requestInit);
    };

    protected override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("showBindingPage")) {
            this.initialSteps = this.showBindingPage ? ["initial", "create-binding"] : ["initial"];
        }
    }

    protected createBindingActivate = async (
        page: FormWizardPage<{ "initial": PolicyBindingCheckTarget; "create-binding": Policy }>,
    ) => {
        const createSlot = page.host.steps[1] as "create-binding";
        const bindingForm = page.querySelector("ak-policy-binding-form");

        if (!bindingForm) return;

        if (page.host.state[createSlot]) {
            bindingForm.allowedTypes = [PolicyBindingCheckTarget.Policy];
            bindingForm.policyGroupUser = PolicyBindingCheckTarget.Policy;

            const policyBindingRequest: Partial<PolicyBindingRequest> = {
                policy: (page.host.state[createSlot] as Policy).pk,
            };

            bindingForm.instance = policyBindingRequest as unknown as PolicyBinding;
        }
        if (page.host.state[initialStep]) {
            bindingForm.allowedTypes = [page.host.state[initialStep]];
            bindingForm.policyGroupUser = page.host.state[initialStep];
        }
    };

    protected override renderCreateBefore(): SlottedTemplateResult {
        if (!this.showBindingPage) {
            return null;
        }

        return html`<ak-form-group
            slot="pre-items"
            label=${msg("Bind Existing...")}
            description=${msg(
                "Select a type to bind an existing object instead of creating a new one.",
            )}
            open
        >
            <ak-radio
                .options=${[
                    {
                        label: msg("Bind a user"),
                        description: html`${msg("Statically bind an existing user.")}`,
                        value: PolicyBindingCheckTarget.User,
                    },
                    {
                        label: msg("Bind a group"),
                        description: html`${msg("Statically bind an existing group.")}`,
                        value: PolicyBindingCheckTarget.Group,
                    },
                    {
                        label: msg("Bind an existing policy"),
                        description: html`${msg("Bind an existing policy.")}`,
                        value: PolicyBindingCheckTarget.Policy,
                    },
                ] satisfies RadioOption<PolicyBindingCheckTarget>[]}
                @change=${(ev: CustomEvent<RadioChangeEventDetail<PolicyBindingCheckTarget>>) => {
                    if (!this.wizard) {
                        return;
                    }

                    this.wizard.state[initialStep] = ev.detail.value;
                    this.wizard.navigateNext();
                }}
            >
            </ak-radio>
        </ak-form-group>`;
    }

    protected renderForms(): SlottedTemplateResult {
        const bindingPage = this.showBindingPage
            ? html`<ak-wizard-page-form
                  slot="create-binding"
                  headline=${msg("Create Binding")}
                  .activePageCallback=${this.createBindingActivate}
                  ><ak-policy-binding-form .targetPk=${this.bindingTarget}></ak-policy-binding-form>
              </ak-wizard-page-form>`
            : null;

        return [super.renderForms(), bindingPage];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-wizard": PolicyWizard;
    }
}
