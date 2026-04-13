import "#admin/stages/register";
import "#elements/LicenseNotice";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { FormWizardPage } from "#elements/wizard/FormWizardPage";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { StageBindingForm } from "#admin/flows/StageBindingForm";

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

    @property()
    public bindingTarget?: string;

    public override initialSteps = this.showBindingPage
        ? ["initial", "create-binding"]
        : ["initial"];

    public static override verboseName = msg("Stage");
    public static override verboseNamePlural = msg("Stages");

    public override layout = TypeCreateWizardPageLayouts.list;

    protected apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.stagesAllTypesList(requestInit);
    };

    protected updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("showBindingPage")) {
            this.initialSteps = this.showBindingPage ? ["initial", "create-binding"] : ["initial"];
        }
    }

    protected createBindingActivate = async (context: FormWizardPage) => {
        const createSlot = context.host.steps[1];
        const bindingForm = context.querySelector<StageBindingForm>("ak-stage-binding-form");

        if (!bindingForm) return;

        bindingForm.instance = {
            stage: (context.host.state[createSlot] as Stage).pk,
        } as FlowStageBinding;
    };

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
