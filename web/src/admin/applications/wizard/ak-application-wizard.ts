import { merge } from "@goauthentik/common/merge";
import { AkWizard } from "@goauthentik/components/ak-wizard-main/AkWizard";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { ContextProvider } from "@lit-labs/context";
import { msg } from "@lit/localize";
import { customElement, state } from "lit/decorators.js";

import applicationWizardContext from "./ContextIdentity";
import { newSteps } from "./steps";
import {
    ApplicationStep,
    ApplicationWizardState,
    ApplicationWizardStateUpdate,
    OneOfProvider,
} from "./types";

const freshWizardState = () => ({
    providerModel: "",
    app: {},
    provider: {},
});

@customElement("ak-application-wizard")
export class ApplicationWizard extends CustomListenerElement(
    AkWizard<ApplicationWizardStateUpdate, ApplicationStep>,
) {
    constructor() {
        super(msg("Create With Wizard"), msg("New application"), msg("Create a new application"));
        this.steps = newSteps();
    }

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

    maybeProviderSwap(providerModel: string | undefined): boolean {
        if (
            providerModel === undefined ||
            typeof providerModel !== "string" ||
            providerModel === this.wizardState.providerModel
        ) {
            return false;
        }

        this.providerCache.set(this.wizardState.providerModel, this.wizardState.provider);
        const prevProvider = this.providerCache.get(providerModel);
        this.wizardState.provider = prevProvider ?? {
            name: `Provider for ${this.wizardState.app.name}`,
        };
        const method = this.steps.find(({ id }) => id === "provider-details");
        if (!method) {
            throw new Error("Could not find Authentication Method page?");
        }
        method.disabled = false;
        return true;
    }

    // And this is where all the special cases go...
    handleUpdate(detail: ApplicationWizardStateUpdate) {
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

        if (this.maybeProviderSwap(update.providerModel)) {
            this.requestUpdate();
        }

        this.wizardState = merge(this.wizardState, update) as ApplicationWizardState;
        this.wizardStateProvider.setValue(this.wizardState);
        this.requestUpdate();
    }

    close() {
        this.steps = newSteps();
        this.currentStep = 0;
        this.wizardState = freshWizardState();
        this.providerCache = new Map();
        this.wizardStateProvider.setValue(this.wizardState);
        this.frame.value!.open = false;
    }

    handleNav(stepId: number | undefined) {
        if (stepId === undefined || this.steps[stepId] === undefined) {
            throw new Error(`Attempt to navigate to undefined step: ${stepId}`);
        }
        if (stepId > this.currentStep && !this.step.valid) {
            return;
        }
        this.currentStep = stepId;
        this.requestUpdate();
    }
}
