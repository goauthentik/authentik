import "#elements/EmptyState";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/wizard/TypeCreateWizardPage";

import { applicationWizardProvidersContext } from "../ContextIdentity.js";

import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import type { NavigableButton, WizardButton } from "#components/ak-wizard/shared";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";

import type { TypeCreate } from "@goauthentik/api";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { html } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { customElement, state } from "lit/decorators.js";

/**
 *
 * @prop wizard - The current state of the application wizard, shared across all steps.
 */
@customElement("ak-application-wizard-provider-choice-step")
export class ApplicationWizardProviderChoiceStep extends WithLicenseSummary(ApplicationWizardStep) {
    label = msg("Choose a Provider");

    @state()
    protected failureMessage = "";

    @consume({ context: applicationWizardProvidersContext, subscribe: true })
    public providerModelsList!: TypeCreate[];

    protected buttons: WizardButton[] = [
        { kind: "cancel" },
        { kind: "back", destination: "application" },
        { kind: "next", destination: "provider" },
    ];

    public override handleButton(button: NavigableButton) {
        this.failureMessage = "";

        if (button.kind === "next") {
            if (!this.wizard.providerModel) {
                this.failureMessage = msg("Please choose a provider type before proceeding.");
                this.dispatchNavigationEvent({ disabled: ["provider", "bindings", "submit"] });

                return;
            }

            return this.dispatchEvents({
                destination: button.destination,
                details: { enable: "provider" },
            });
        }

        return super.handleButton(button);
    }

    protected typeSelectListener = (event: CustomEvent<TypeCreate>) => {
        return this.dispatchEvents({
            update: {
                ...this.wizard,
                providerModel: event.detail.modelName,
            },
            details: { enable: "provider" },
        });
    };

    protected renderMain(): SlottedTemplateResult {
        const { providerModelsList } = this;

        return guard([providerModelsList], () => {
            if (!providerModelsList.length) {
                return html`<ak-empty-state default-label></ak-empty-state>`;
            }

            const selectedTypes = providerModelsList.filter(
                (t) => t.modelName === this.wizard.providerModel,
            );

            return html`<h3 class="pf-c-wizard__main-title">${msg("Choose a Provider Type")}</h3>
                <form class="pf-c-form pf-m-horizontal">
                    <ak-wizard-page-type-create
                        .types=${providerModelsList}
                        layout=${TypeCreateWizardPageLayouts.grid}
                        .selectedType=${selectedTypes.length > 0 ? selectedTypes[0] : null}
                        @ak-type-create-select=${this.typeSelectListener}
                    ></ak-wizard-page-type-create>
                </form>`;
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-choice-step": ApplicationWizardProviderChoiceStep;
    }
}
