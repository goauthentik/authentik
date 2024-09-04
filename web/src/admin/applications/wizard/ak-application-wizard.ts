import { AkWizard } from "@goauthentik/components/ak-wizard-main/AkWizard.js";
import {
    WizardNavigationEvent,
    WizardUpdateEvent,
} from "@goauthentik/components/ak-wizard-main/events.js";

import { ContextProvider } from "@lit/context";
import { msg } from "@lit/localize";
import { customElement, state } from "lit/decorators.js";

import { applicationWizardContext } from "./ContextIdentity";
import { ApplicationStep } from "./application/ApplicationStep.js";
import { ProviderChoiceStep } from "./provider-choice/ProviderChoiceStep.js";
import { ProviderStep } from "./provider/ProviderStep.js";
import { SubmitStep } from "./submit/SubmitStep.js";
import {
    ApplicationWizardState,
    ApplicationWizardStateUpdate,
    ApplicationWizardStep,
    OneOfProvider,
} from "./types";

const freshWizardState = (): ApplicationWizardState => ({
    providerModel: "",
    app: {},
    provider: {},
    errors: {},
});

export const newSteps = (): ApplicationWizardStep[] => [
    new ApplicationStep(),
    new ProviderChoiceStep(),
    new ProviderStep(),
    new SubmitStep(),
];

@customElement("ak-application-wizard")
export class ApplicationWizard extends AkWizard<
    ApplicationWizardStateUpdate,
    ApplicationWizardStep
> {
    canCancel = true;

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

    providerCache: Map<string, OneOfProvider> = new Map();

    constructor() {
        super(msg("Create With Wizard"), msg("New application"), msg("Create a new application"));
        this.reset(newSteps());
    }

    /**
     * One of our steps has multiple display variants, one for each type of service provider. We
     * want to *preserve* a customer's decisions about different providers; never make someone "go
     * back and type it all back in," even if it's probably rare that someone will chose one
     * provider, realize it's the wrong one, and go back to chose a different one, *and then go
     * back*. Nonetheless, strive to *never* lose customer input.
     *
     */
    // And this is where all the special cases go...
    onUpdate(event: WizardUpdateEvent<ApplicationWizardStateUpdate>) {
        const { content } = event;

        if (content.status === "submitted") {
            this.step.valid = true;
            this.requestUpdate();
            return;
        }

        this.step.valid = this.step.valid || content.status === "valid";
        const { update } = content;

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
        this.frame.value!.open = false;
        this.reset(newSteps());
        this.wizardState = freshWizardState();
        this.providerCache = new Map();
        this.wizardStateProvider.setValue(this.wizardState);
    }

    onNavigation(event: WizardNavigationEvent) {
        if (!this.step.valid) {
            return;
        }
        super.onNavigation(event);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard": ApplicationWizard;
    }
}
