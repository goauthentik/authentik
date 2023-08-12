import "@goauthentik/components/ak-wizard-main";
import { AKElement } from "@goauthentik/elements/Base";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { provide } from "@lit-labs/context";
import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import applicationWizardContext from "./ak-application-wizard-context-name";
import { steps } from "./steps";
import { WizardState, WizardStateEvent } from "./types";

// my-context.ts

// All this thing is doing is recording the input the user makes to the forms. It should NOT be
// triggering re-renders; that's the wizard frame's jobs.

@customElement("ak-application-wizard")
export class ApplicationWizard extends CustomListenerElement(AKElement) {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    /**
     * Providing a context at the root element
     */
    @provide({ context: applicationWizardContext })
    wizardState: WizardState = {
        step: 0,
        providerType: "",
        application: {},
        provider: {},
    };

    @state()
    steps = steps;

    @property()
    prompt = msg("Create");

    constructor() {
        super();
        this.handleUpdate = this.handleUpdate.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        this.addCustomListener("ak-application-wizard-update", this.handleUpdate);
    }

    disconnectedCallback() {
        this.removeCustomListener("ak-application-wizard-update", this.handleUpdate);
        super.disconnectedCallback();
    }

    // And this is where all the special cases go...
    handleUpdate(event: CustomEvent<WizardStateEvent>) {
        delete event.detail.target;
        const newWizardState: WizardState = event.detail;

        // When the user sets the authentication method type, the corresponding authentication
        // method page becomes available.
        if (newWizardState.providerType !== "") {
            const newSteps = [...this.steps];
            const method = newSteps.find(({ id }) => id === "auth-method");
            if (!method) {
                throw new Error("Could not find Authentication Method page?");
            }
            method.disabled = false;
            this.steps = newSteps;
        }
        this.wizardState = newWizardState;
    }

    render(): TemplateResult {
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
