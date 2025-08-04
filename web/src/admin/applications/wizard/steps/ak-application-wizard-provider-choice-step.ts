import "#admin/applications/wizard/ak-wizard-title";
import "#elements/EmptyState";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/wizard/TypeCreateWizardPage";

import { applicationWizardProvidersContext } from "../ContextIdentity.js";
import { type LocalTypeCreate } from "./ProviderChoices.js";

import { WithLicenseSummary } from "#elements/mixins/license";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import type { NavigableButton, WizardButton } from "#components/ak-wizard/types";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-application-wizard-provider-choice-step")
export class ApplicationWizardProviderChoiceStep extends WithLicenseSummary(ApplicationWizardStep) {
    public override label = msg("Choose a Provider");

    @state()
    protected failureMessage = "";

    @consume({ context: applicationWizardProvidersContext, subscribe: true })
    public providerModelsList!: LocalTypeCreate[];

    public override get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "provider" },
            { kind: "back", destination: "application" },
            { kind: "cancel" },
        ];
    }

    protected override handleButton(button: NavigableButton) {
        this.failureMessage = "";
        if (button.kind === "next") {
            if (!this.wizard.providerModel) {
                this.failureMessage = msg("Please choose a provider type before proceeding.");
                this.handleEnabling({ disabled: ["provider", "bindings", "submit"] });
                return;
            }
            this.handleUpdate(undefined, button.destination, { enable: "provider" });
            return;
        }
        super.handleButton(button);
    }

    protected override renderMain() {
        const selectedTypes = this.providerModelsList.filter(
            (t) => t.modelName === this.wizard.providerModel,
        );

        return this.providerModelsList.length > 0
            ? html` <ak-wizard-title>${msg("Choose a Provider Type")}</ak-wizard-title>
                  <form class="pf-c-form pf-m-horizontal">
                      <ak-wizard-page-type-create
                          .types=${this.providerModelsList}
                          name="selectProviderType"
                          layout=${TypeCreateWizardPageLayouts.grid}
                          .selectedType=${selectedTypes.length > 0 ? selectedTypes[0] : undefined}
                          @select=${(ev: CustomEvent<LocalTypeCreate>) => {
                              this.handleUpdate(
                                  {
                                      ...this.wizard,
                                      providerModel: ev.detail.modelName,
                                  },
                                  undefined,
                                  { enable: "provider" },
                              );
                          }}
                      ></ak-wizard-page-type-create>
                  </form>`
            : html`<ak-empty-state default-label></ak-empty-state>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-choice-step": ApplicationWizardProviderChoiceStep;
    }
}
