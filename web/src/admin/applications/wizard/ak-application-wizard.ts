import { type AkWizardMain } from "@goauthentik/app/components/ak-wizard-main/ak-wizard-main";
import { merge } from "@goauthentik/common/merge";
import "@goauthentik/components/ak-wizard-main";
import { AKElement } from "@goauthentik/elements/Base";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { ContextProvider, ContextRoot } from "@lit-labs/context";
import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { type Ref, createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import applicationWizardContext from "./ak-application-wizard-context-name";
import { steps } from "./steps";
import { OneOfProvider, WizardState, WizardStateEvent } from "./types";

@customElement("ak-application-wizard")
export class ApplicationWizard extends CustomListenerElement(AKElement) {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    @state()
    wizardState: WizardState = {
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

    @state()
    steps = steps;

    @property()
    prompt = msg("Create");

    providerCache: Map<string, OneOfProvider> = new Map();

    wizardRef: Ref<AkWizardMain> = createRef();

    get step() {
        return this.wizardRef.value?.currentStep ?? -1;
    }

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
    }

    // And this is where all the special cases go...
    handleUpdate(event: CustomEvent<WizardStateEvent>) {
        const update = event.detail.update;

        if (this.maybeProviderSwap(update.providerModel)) {
            this.steps = [...this.steps];
        }

        if (event.detail.status === "valid" && this.steps[this.step + 1]) {
            this.steps[this.step + 1].disabled = false;
            this.steps = [...this.steps];            
        }

        this.wizardState = merge(this.wizardState, update) as WizardState;
        this.wizardStateProvider.setValue(this.wizardState);
    }

    render() {
        return html`
            <ak-wizard-main
                ${ref(this.wizardRef)}
                .steps=${this.steps}
                header=${msg("New application")}
                description=${msg("Create a new application.")}
                prompt=${this.prompt}
            >
            </ak-wizard-main>
        `;
    }
}
