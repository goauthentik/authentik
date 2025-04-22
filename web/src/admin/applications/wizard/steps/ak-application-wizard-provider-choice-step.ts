import { ApplicationWizardStep } from "@goauthentik/admin/applications/wizard/ApplicationWizardStep.js";
import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import type { NavigableButton, WizardButton } from "@goauthentik/components/ak-wizard/types";
import "@goauthentik/elements/EmptyState.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import "@goauthentik/elements/forms/FormGroup.js";
import "@goauthentik/elements/forms/HorizontalFormElement.js";
import { WithLicenseSummary } from "@goauthentik/elements/mixins/license";
import { TypeCreateWizardPageLayouts } from "@goauthentik/elements/wizard/TypeCreateWizardPage.js";
import "@goauthentik/elements/wizard/TypeCreateWizardPage.js";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { TypeCreate } from "@goauthentik/api";

import { applicationWizardProvidersContext } from "../ContextIdentity";
import { type LocalTypeCreate } from "./ProviderChoices.js";

@customElement("ak-application-wizard-provider-choice-step")
export class ApplicationWizardProviderChoiceStep extends WithLicenseSummary(ApplicationWizardStep) {
    label = msg("Choose A Provider");

    @state()
    failureMessage = "";

    @consume({ context: applicationWizardProvidersContext, subscribe: true })
    public providerModelsList!: LocalTypeCreate[];

    get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "provider" },
            { kind: "back", destination: "application" },
            { kind: "cancel" },
        ];
    }

    override handleButton(button: NavigableButton) {
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

    @bound
    onSelect(ev: CustomEvent<LocalTypeCreate>) {
        ev.stopPropagation();
        const detail: TypeCreate = ev.detail;
        this.handleUpdate({ providerModel: detail.modelName });
    }

    renderMain() {
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
            : html`<ak-empty-state loading header=${msg("Loading")}></ak-empty-state>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-choice-step": ApplicationWizardProviderChoiceStep;
    }
}
