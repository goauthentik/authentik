import { ApplicationWizardStep } from "@goauthentik/admin/applications/wizard/ApplicationWizardStep.js";
import type { NavigableButton, WizardButton } from "@goauthentik/components/ak-wizard/types";
import "@goauthentik/elements/EmptyState.js";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import "@goauthentik/elements/forms/FormGroup.js";
import "@goauthentik/elements/forms/HorizontalFormElement.js";
import { TypeCreateWizardPageLayouts } from "@goauthentik/elements/wizard/TypeCreateWizardPage.js";
import "@goauthentik/elements/wizard/TypeCreateWizardPage.js";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import { TypeCreate } from "@goauthentik/api";

import { type LocalTypeCreate, providerModelsList } from "./ProviderChoices.js";

@customElement("ak-application-wizard-provider-choice-step")
export class ApplicationWizardProviderChoiceStep extends WithLicenseSummary(ApplicationWizardStep) {
    label = msg("Choose A Provider");

    @state()
    failureMessage = "";

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

    renderForm(model: string) {
        const selectedType = providerModelsList.find((t) => t.formName === model);

        // As a hack, the Application wizard has separate provider paths for our three types of
        // proxy providers. This patch swaps the form we want to be directed to on page 3 from the
        // modelName to the formName, so we get the right one.  This information isn't modified
        // or forwarded, so the proxy-plus-subtype is correctly mapped on submission.
        const typesForWizard = providerModelsList.map((provider) => ({
            ...provider,
            modelName: provider.formName,
        }));

        return providerModelsList.length > 0
            ? html`<form class="pf-c-form pf-m-horizontal" slot="form">
                  ${this.failureMessage !== ""
                      ? html`<p class="pf-c-form__helper-text pf-m-error" aria-live="polite">
                            ${this.failureMessage}
                        </p>`
                      : nothing}

                  <ak-wizard-page-type-create
                      .types=${typesForWizard}
                      layout=${TypeCreateWizardPageLayouts.grid}
                      .selectedType=${selectedType}
                      @select=${this.onSelect}
                  ></ak-wizard-page-type-create>
              </form> `
            : html`<ak-empty-state loading header=${msg("Loading")} slot="form"></ak-empty-state>`;
    }

    renderMain() {
        if (this.wizard.providerModel === undefined) {
            throw new Error("Application Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.providerModel);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-choice-step": ApplicationWizardProviderChoiceStep;
    }
}
