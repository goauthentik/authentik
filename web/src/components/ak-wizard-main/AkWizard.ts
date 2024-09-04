import "@goauthentik/components/ak-wizard-main/ak-wizard-frame";
import { AKElement } from "@goauthentik/elements/Base";
import { P, match } from "ts-pattern";

import { msg } from "@lit/localize";
import { ReactiveControllerHost, html } from "lit";
import { state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkWizardFrame } from "./ak-wizard-frame";
import { WizardCloseEvent, WizardNavigationEvent, WizardUpdateEvent } from "./events.js";
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
    currentStep = "";

    public canCancel = false;

    /**
     * A reference to the frame.  Since the frame implements and inherits from ModalButton,
     * you will need either a reference to or query to the frame in order to call
     * `.close()` on it.
     */
    frame: Ref<AkWizardFrame> = createRef();

    get step() {
        const nextstep = this.steps.find((step) => step.id === this.currentStep);
        if (!nextstep) {
            throw new Error(`Requested a step that is not defined: ${this.currentStep}`);
        }
        return nextstep;
    }

    prompt = msg("Create");

    header: string;

    description?: string;

    constructor(prompt: string, header: string, description?: string) {
        super();
        this.header = header;
        this.prompt = prompt;
        this.description = description;
    }

    connectedCallback() {
        super.connectedCallback();
        this.addEventListener(WizardNavigationEvent.eventName, this.onNavigation);
        this.addEventListener(WizardUpdateEvent.eventName, this.onUpdate);
        this.addEventListener(WizardCloseEvent.eventName, this.onClose);
    }

    disconnectedCallback() {
        this.removeEventListener(WizardNavigationEvent.eventName, this.onNavigation);
        this.removeEventListener(WizardUpdateEvent.eventName, this.onUpdate);
        this.removeEventListener(WizardCloseEvent.eventName, this.onClose);
        super.disconnectedCallback();
    }

    /**
     * Derive the labels used by the frame's Breadcrumbs display.
     */
    get stepLabels(): WizardStepLabel[] {
        let disabled = false;
        return this.steps.map((step) => {
            disabled = disabled || step.disabled;
            return {
                label: step.label,
                active: step.id === this.currentStep,
                id: step.id,
                disabled,
            };
        });
    }

    /**
     * You should still consider overriding this if you need to consider details like "Is the step
     * requested valid?"
     */
    navigateTo(stepId: string) {
        const nextstep = this.steps.find((step) => step.id === stepId);
        if (!nextstep) {
            throw new Error(`Navigation request for a step that does not exist: ${stepId}`);
        }
        this.currentStep = nextstep.id;
        this.requestUpdate();
    }

    close() {
        throw new Error("This function must be overridden in the child class.");
    }

    onClose(_event: WizardCloseEvent) {
        this.close();
    }

    /**
     * This is where all the business logic and special cases go. The Wizard Controller intercepts
     * updates tagged `ak-wizard-update` and forwards the event content here. Business logic about
     * "is the current step valid?" and "should the Next button be made enabled" are controlled
     * here. (Any step implementing WizardStep can do it anyhow it pleases, putting "is the current
     * form valid" and so forth into the step object itself.)
     */
    onUpdate(_event: WizardUpdateEvent<D>) {
        throw new Error("This function must be overridden in the child class.");
    }

    onNavigation(event: WizardNavigationEvent) {
        match(event.command)
            .with({ disabled: true }, () => {
                throw new Error("Wizard received a command from a disabled component");
            })
            .with({ kind: P.union("close", "cancel") }, () => {
                this.close();
            })
            .with({ kind: P.union("next", "back"), target: P.string }, ({ target }) => {
                this.navigateTo(target);
            })
            .otherwise(() => {
                throw new Error(
                    `Wizard received a command it does not recognize: ${JSON.stringify(event.command)}`,
                );
            });
    }

    render() {
        return html`
            <ak-wizard-frame
                ${ref(this.frame)}
                header=${this.header}
                description=${ifDefined(this.description)}
                prompt=${this.prompt}
                ?can-cancel=${this.canCancel}
                .buttons=${this.step.buttons}
                .stepLabels=${this.stepLabels}
                .form=${this.step.render.bind(this.step)}
            >
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.prompt}</button>
            </ak-wizard-frame>
        `;
    }
}
