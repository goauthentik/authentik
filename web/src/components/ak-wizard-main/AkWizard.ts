import "@goauthentik/components/ak-wizard-main/ak-wizard-frame";
import { AKElement } from "@goauthentik/elements/Base";
import { bound } from "@goauthentik/elements/decorators/bound.js";

import { msg } from "@lit/localize";
import { ReactiveControllerHost, html } from "lit";
import { property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { type WizardStep } from "./AkWizardStep.js";
import { AkWizardFrame } from "./ak-wizard-frame";
import { WizardCloseEvent, WizardNavigationEvent, WizardUpdateEvent } from "./events";
import { type WizardStepLabel } from "./types";

/**
 * Abstract parent class for wizards. This Class activates the Controller, provides the default
 * renderer and handleNav() functions, and organizes the various texts used to describe a Modal
 * Wizard's interaction: its prompt, header, and description.
 */

export class AkWizard<State, Step extends WizardStep = WizardStep>
    extends AKElement
    implements ReactiveControllerHost
{
    // prettier-ignore
    static get styles() { return [PFBase, PFButton]; }

    @property({ type: Boolean, attribute: "can-cancel" })
    canCancel = false;

    @state()
    steps: Step[] = [];

    @state()
    currentStepId = "";

    /**
     * A reference to the frame.  Since the frame implements and inherits from ModalButton,
     * you will need either a reference to or query to the frame in order to call
     * `.close()` on it.
     */
    frame: Ref<AkWizardFrame> = createRef();

    get step() {
        const nextStep = this.findStep(this.currentStepId);
        if (!nextStep) {
            throw new Error("Unable to identify current step.");
        }
        return nextStep;
    }

    prompt = msg("Create");

    header: string;

    description?: string;

    // BEGIN PUBLIC API

    constructor(prompt: string, header: string, description?: string) {
        super();
        this.header = header;
        this.prompt = prompt;
        this.description = description;
        this.reset();
        this.addEventListener(WizardNavigationEvent.eventName, this.onNavigation);
        this.addEventListener(WizardCloseEvent.eventName, this.onClose);
        this.addEventListener(WizardUpdateEvent.eventName, this.onUpdate);
    }

    public newSteps(): Step[] {
        throw new Error("This method must be overridden in the child class.");
    }

    public reset(steps?: Step[]) {
        this.steps = steps ?? this.newSteps();
        this.currentStepId = this.steps[0].id;
        if (this.frame.value) {
            this.frame.value!.open = false;
        }
    }

    /**
     * You should still consider overriding this if you need to consider details like "Is the step
     * requested valid?"
     */
    public navigateTo(stepId: string | undefined) {
        if (stepId === undefined || this.findStep(stepId) === undefined) {
            throw new Error(`Attempt to navigate to undefined step: ${stepId}`);
        }
        this.currentStepId = stepId;
        this.requestUpdate();
    }

    /**
     * This is where all the business logic and special cases go. The Wizard Controller intercepts
     * updates tagged `ak-wizard-update` and forwards the event content here. Business logic about
     * "is the current step valid?" and "should the Next button be made enabled" are controlled
     * here. (Any step implementing WizardStep can do it anyhow it pleases, putting "is the current
     * form valid" and so forth into the step object itself.)
     */
    public handleUpdate(_update: State) {
        throw new Error("This method must be overridden in the child class.");
    }

    public close() {
        this.reset();
    }

    // END PUBLIC API

    public findStep(stepId?: string): Step | undefined {
        return this.steps.find((step) => step.id === stepId);
    }

    /**
     * Derive the labels used by the frame's Breadcrumbs display.
     */
    protected get stepLabels(): WizardStepLabel[] {
        let valid = true;
        return this.steps
            .filter((step) => !step.hidden)
            .map((step) => {
                const nextStep = {
                    label: step.label,
                    active: step.id === this.currentStepId,
                    id: step.id,
                    disabled: !valid,
                };
                valid = valid && step.valid;
                return nextStep;
            });
    }

    @bound
    private onNavigation(ev: WizardNavigationEvent) {
        ev.stopPropagation();
        this.navigateTo(ev.destination);
    }

    @bound
    private onClose(ev: WizardCloseEvent) {
        ev.stopPropagation();
        this.close();
    }

    @bound
    private onUpdate(ev: WizardUpdateEvent<State>) {
        ev.stopPropagation();
        this.handleUpdate(ev.content);
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
                ?can-cancel=${this.canCancel}
            >
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.prompt}</button>
            </ak-wizard-frame>
        `;
    }
}

/**
 * Design:
 *
 * The Wizard has two parts: the logic part and the display part, here called the "frame."
 */
