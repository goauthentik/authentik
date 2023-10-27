import "@goauthentik/app/components/ak-wizard-main/ak-wizard-frame";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { ReactiveControllerHost, html } from "lit";
import { state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkWizardController } from "./AkWizardController";
import { AkWizardFrame } from "./ak-wizard-frame";
import { type WizardStep, type WizardStepLabel } from "./types";

/**
 * Abstract parent class for wizards. This Class activates the Controller, provides the default
 * renderer and handleNav() functions, and organizes the various texts used to describe a Modal
 * Wizard's interaction: its prompt, header, and description.
 */

export class AkWizard<D, Step extends WizardStep = WizardStep>
    extends AKElement
    implements ReactiveControllerHost
{
    // prettier-ignore
    static get styles() { return [PFBase, PFButton]; }

    @state()
    steps: Step[] = [];

    @state()
    currentStep = 0;

    /**
     * A reference to the frame.  Since the frame implements and inherits from ModalButton,
     * you will need either a reference to or query to the frame in order to call
     * `.close()` on it.
     */
    frame: Ref<AkWizardFrame> = createRef();

    get step() {
        return this.steps[this.currentStep];
    }

    prompt = msg("Create");

    header: string;

    description?: string;

    wizard: AkWizardController<D>;

    constructor(prompt: string, header: string, description?: string) {
        super();
        this.header = header;
        this.prompt = prompt;
        this.description = description;
        this.wizard = new AkWizardController(this);
    }

    /**
     * Derive the labels used by the frame's Breadcrumbs display.
     */
    get stepLabels(): WizardStepLabel[] {
        let disabled = false;
        return this.steps.map((step, index) => {
            disabled = disabled || step.disabled;
            return {
                label: step.label,
                active: index === this.currentStep,
                index,
                disabled,
            };
        });
    }

    /**
     * You should still consider overriding this if you need to consider details like "Is the step
     * requested valid?"
     */
    handleNav(stepId: number | undefined) {
        if (stepId === undefined || this.steps[stepId] === undefined) {
            throw new Error(`Attempt to navigate to undefined step: ${stepId}`);
        }
        this.currentStep = stepId;
        this.requestUpdate();
    }

    close() {
        throw new Error("This function must be overridden in the child class.");
    }

    /**
     * This is where all the business logic and special cases go. The Wizard Controller intercepts
     * updates tagged `ak-wizard-update` and forwards the event content here. Business logic about
     * "is the current step valid?" and "should the Next button be made enabled" are controlled
     * here. (Any step implementing WizardStep can do it anyhow it pleases, putting "is the current
     * form valid" and so forth into the step object itself.)
     */
    handleUpdate(_detail: D) {
        throw new Error("This function must be overridden in the child class.");
    }

    render() {
        return html`
            <ak-wizard-frame
                ${ref(this.frame)}
                header=${this.header}
                description=${ifDefined(this.description)}
                prompt=${this.prompt}
                .buttons=${this.step.buttons}
                .stepLabels=${this.stepLabels}
                .form=${this.step.render.bind(this.step)}
            >
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.prompt}</button>
            </ak-wizard-frame>
        `;
    }
}
