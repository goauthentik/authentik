import "#admin/stages/register";
import "#elements/LicenseNotice";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";
import "#elements/forms/FormGroup";
import "#admin/flows/StageBindingForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { FormWizardPage } from "#elements/wizard/FormWizardPage";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { FlowStageBinding, Stage, StagesApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

@customElement("ak-stage-wizard")
export class AKStageWizard extends CreateWizard {
    #api = new StagesApi(DEFAULT_CONFIG);

    @property({ type: Boolean })
    public showBindingPage = false;

    @property({ type: String, useDefault: true })
    public bindingTarget: string | null = null;

    public override initialSteps = this.showBindingPage
        ? ["initial", "create-binding"]
        : ["initial"];

    public static override verboseName = msg("Stage");
    public static override verboseNamePlural = msg("Stages");

    public override layout = TypeCreateWizardPageLayouts.list;

    public override groupLabel = msg("Bind New Stage");
    public override groupDescription = msg("Select the type of stage you want to create.");

    protected apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.stagesAllTypesList(requestInit);
    };

    protected override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("showBindingPage")) {
            this.initialSteps = this.showBindingPage ? ["initial", "create-binding"] : ["initial"];
        }
    }

    protected createBindingActivate = async (
        context: FormWizardPage<{ "create-binding": Stage }>,
    ) => {
        const createSlot = context.host.steps[1] as "create-binding";
        const bindingForm = context.querySelector("ak-stage-binding-form");

        if (!bindingForm) return;

        if (context.host.state[createSlot]) {
            bindingForm.instance = {
                stage: (context.host.state[createSlot] as Stage).pk,
            } as FlowStageBinding;
        }
    };

    protected override renderCreateBefore(): SlottedTemplateResult {
        if (!this.showBindingPage) {
            return null;
        }

        return html`<ak-form-group
            slot="pre-items"
            label=${msg("Existing Stage")}
            description=${msg("Bind an existing stage to this flow.")}
            open
        >
            <ak-radio
                .options=${[
                    {
                        label: "Bind existing stage",
                        description: msg("Bind an existing stage to this flow."),
                        value: true,
                    },
                ] satisfies RadioOption<boolean>[]}
                @change=${() => {
                    if (!this.wizard) {
                        return;
                    }

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
              >
                  <ak-stage-binding-form .targetPk=${this.bindingTarget}></ak-stage-binding-form>
              </ak-wizard-page-form>`
            : null;

        return [super.renderForms(), bindingPage];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-wizard": AKStageWizard;
    }
}
