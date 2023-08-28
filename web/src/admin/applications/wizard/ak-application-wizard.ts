import { merge } from "@goauthentik/common/merge";
import "@goauthentik/components/ak-wizard-main";
import { AKElement } from "@goauthentik/elements/Base";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { ContextProvider, ContextRoot } from "@lit-labs/context";
import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import applicationWizardContext from "./ak-application-wizard-context-name";
import { steps } from "./steps";
import { OneOfProvider, WizardState, WizardStateEvent } from "./types";

// my-context.ts

// All this thing is doing is recording the input the user makes to the forms. It should NOT be
// triggering re-renders; that's the wizard frame's jobs.

@customElement("ak-application-wizard")
export class ApplicationWizard extends CustomListenerElement(AKElement) {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    @state()
    wizardState: WizardState = {
        step: 0,
        providerModel: "",
        app: {},
        provider: {},
    };

    /**
     * Providing a context at the root element
     */
    wizardStateProvider = new ContextProvider(this, {
        context: applicationWizardContext,
        initialValue: this.wizardState,
    });

    steps = steps;

    @property()
    prompt = msg("Create");

    providerCache: Map<string, OneOfProvider> = new Map();

    constructor() {
        super();
        this.handleUpdate = this.handleUpdate.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        new ContextRoot().attach(this.parentElement!);
        this.addCustomListener("ak-application-wizard-update", this.handleUpdate);
    }

    disconnectedCallback() {
        this.removeCustomListener("ak-application-wizard-update", this.handleUpdate);
        super.disconnectedCallback();
    }

    // And this is where all the special cases go...
    handleUpdate(event: CustomEvent<WizardStateEvent>) {
        const update = event.detail.update;

        // Are we changing provider type? If so, swap the caches of the various provider types the
        // user may have filled in, and enable the next step.
        const providerModel = update.providerModel;
        if (
            providerModel &&
            typeof providerModel === "string" &&
            providerModel !== this.wizardState.providerModel
        ) {
            this.providerCache.set(this.wizardState.providerModel, this.wizardState.provider);
            const prevProvider = this.providerCache.get(providerModel);
            this.wizardState.provider = prevProvider ?? {
                name: `Provider for ${this.wizardState.app.name}`,
            };
            const newSteps = [...this.steps];
            const method = newSteps.find(({ id }) => id === "auth-method");
            if (!method) {
                throw new Error("Could not find Authentication Method page?");
            }
            method.disabled = false;
            this.steps = newSteps;
        }

        this.wizardState = merge(this.wizardState, update) as WizardState;
        this.wizardStateProvider.setValue(this.wizardState);
    }

    render() {
        return html`
            <ak-wizard-main
                .steps=${this.steps}
                header=${msg("New application")}
                description=${msg("Create a new application.")}
                prompt=${this.prompt}
            >
            </ak-wizard-main>
        `;
    }
}
