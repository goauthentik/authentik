import { AkWizard } from "@goauthentik/components/ak-wizard-main/AkWizard.js";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { ContextProvider } from "@lit/context";
import { msg } from "@lit/localize";
import { customElement, state } from "lit/decorators.js";

import { applicationWizardContext } from "./ContextIdentity";
import { ApplicationStep } from "./application/ak-application-wizard-application-details.js";
import { ProviderMethodStep } from "./auth-method-choice/ak-application-wizard-authentication-method-choice.js";
import { SubmitApplicationStep } from "./commit/ak-application-wizard-commit-application.js";
import { ProviderDetailsStep } from "./methods/ak-application-wizard-authentication-method.js";
import { ApplicationWizardState, ApplicationWizardStateUpdate, OneOfProvider } from "./types";

const freshWizardState = (): ApplicationWizardState => ({
    providerModel: "",
    app: {},
    provider: {},
    errors: {},
});

@customElement("ak-application-wizard")
export class ApplicationWizard extends CustomListenerElement(
    AkWizard<ApplicationWizardStateUpdate, ApplicationStep>,
) {
    /**
     * We're going to be managing the content of the forms by percolating all of the data up to this
     * class, which will ultimately transmit all of it to the server as a transaction. The
     * WizardFramework doesn't know anything about the nature of the data itself; it just forwards
     * valid updates to us. So here we maintain a state object *and* update it so all child
     * components can access the wizard state.
     *
     */
    @state()
    wizardState: ApplicationWizardState = freshWizardState();

    wizardStateProvider = new ContextProvider(this, {
        context: applicationWizardContext,
        initialValue: this.wizardState,
    });

    /**
     * One of our steps has multiple display variants, one for each type of service provider. We
     * want to *preserve* a customer's decisions about different providers; never make someone "go
     * back and type it all back in," even if it's probably rare that someone will chose one
     * provider, realize it's the wrong one, and go back to chose a different one, *and then go
     * back*. Nonetheless, strive to *never* lose customer input.
     *
     */
    providerCache: Map<string, OneOfProvider> = new Map();

    constructor() {
        super(msg("Create With Wizard"), msg("New application"), msg("Create a new application"));
    }

    public override newSteps() {
        return [
            new ApplicationStep(),
            new ProviderMethodStep(),
            new ProviderDetailsStep(),
            new SubmitApplicationStep(),
        ];
    }

    // And this is where all the special cases go...
    public override handleUpdate(detail: ApplicationWizardStateUpdate) {
        if (detail.status === "submitted") {
            this.step.valid = true;
            this.requestUpdate();
            return;
        }

        this.step.valid = this.step.valid || detail.status === "valid";
        const update = detail.update;

        if (!update) {
            return;
        }

        // When the providerModel enum changes, retrieve the customer's prior work for *this* wizard
        // session (and only this wizard session) or provide an empty model with a default provider
        // name.
        if (update.providerModel && update.providerModel !== this.wizardState.providerModel) {
            const requestedProvider = this.providerCache.get(update.providerModel) ?? {
                name: `Provider for ${this.wizardState.app.name}`,
            };
            if (this.wizardState.providerModel) {
                this.providerCache.set(this.wizardState.providerModel, this.wizardState.provider);
            }
            update.provider = requestedProvider;
        }

        this.wizardState = update as ApplicationWizardState;
        this.wizardStateProvider.setValue(this.wizardState);
        this.requestUpdate();
    }

    close() {
        super.close();
        this.wizardState = freshWizardState();
        this.providerCache = new Map();
        this.wizardStateProvider.setValue(this.wizardState);
    }

    navigateTo(stepId: string | undefined) {
        if (stepId === undefined || this.findStep(stepId) === undefined) {
            throw new Error(`Attempt to navigate to undefined step: ${stepId}`);
        }
        this.currentStepId = stepId;
        this.requestUpdate();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard": ApplicationWizard;
    }
}
