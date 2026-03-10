import { NavigationEventInit, WizardCloseEvent, WizardNavigationEvent } from "./events.js";
import {
    ButtonKindClassnameRecord,
    ButtonKindLabelRecord,
    isNavigable,
    type WizardButton,
    WizardStepLabel,
    WizardStepState,
} from "./shared.js";
import { wizardStepContext } from "./WizardContexts.js";

import { AKElement } from "#elements/Base";
import { bound } from "#elements/decorators/bound";
import { SlottedTemplateResult } from "#elements/types";

import { ConsoleLogger, Logger } from "#logger/browser";

import { match, P } from "ts-pattern";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

/**
 * @class WizardStep
 *
 * Superclass for a single step in the wizard.  Contains all of the styling for the Patternfly
 * wizard pattern.  Child classes must:
 *
 * - Specify the *Wizard* title, optional description, and if to show the cancel icon in the upper
 *   right hand corner. Ideally, this is the same for all child classes, so for simplicity these
 *   could be overridden
 * - Specify what goes into the main content for this step.
 * - Specify what buttons to render for this step, and to what step(s) the navigable button(s) must go.
 * - Specify what validation must be done before the 'next' button can be honored.
 *
 * Events
 *
 * @fires WizardNavigationEvent - request ak-wizard-steps to move to another step
 * @fires WizardCloseEvent - request parent container (Wizard) to close the wizard
 */

export abstract class WizardStep extends AKElement {
    // These additions are necessary because we don't want to inherit *all* of the modal box
    // modifiers, just the ones related to managing the height of the display box.
    public static styles = [
        PFWizard,
        PFContent,
        PFTitle,
        css`
            .ak-wizard-box {
                height: 75%;
                height: 75vh;
                display: flex;
                flex-direction: column;
                position: relative;
                z-index: 500;
            }
        `,
    ];

    /**
     * A prefixed logger for this component.
     */
    protected logger: Logger;

    @property({ type: Boolean, attribute: true, reflect: true })
    public enabled = false;

    /**
     * The name. Should match the slot. Reflected if not present.
     */
    @property({ type: String, attribute: true, reflect: true })
    public name?: string;

    @consume({ context: wizardStepContext, subscribe: true })
    protected wizardStepState: WizardStepState = { currentStep: undefined, stepLabels: [] };

    /**
     * What appears in the titlebar of the Wizard. Usually, but not necessarily, the same for all
     * steps. Recommendation: Set this, the description, and `canCancel` in a subclass, and stop
     * worrying about them.
     */
    protected wizardTitle = "--unset--";

    /**
     * The text for a descriptive subtitle for the wizard
     */
    protected wizardDescription?: string;

    /**
     * Show the [Cancel] icon and offer the [Cancel] button
     */
    public canCancel = false;

    /**
     * Report the validity of the element, triggering client-side validation.
     *
     * @returns Whether the form is valid.
     */
    public abstract reportValidity(): boolean;

    /**
     * Check the validity of the element.
     *
     * @returns Whether the form is valid.
     */
    public abstract checkValidity(): boolean;

    /**
     * The ID of the current step.
     */
    declare public id: string;

    /**
     *The label of the current step.  Displayed in the navigation bar.
     */
    public label: string = "--unset--";

    /**
     * If true, this step's label will not be shown in the navigation bar
     */
    public hide = false;

    //  ___      _    _ _        _   ___ ___
    // | _ \_  _| |__| (_)__    /_\ | _ \_ _|
    // |  _/ || | '_ \ | / _|  / _ \|  _/| |
    // |_|  \_,_|_.__/_|_\__| /_/ \_\_| |___|
    //

    //#region Public API

    // Override this and provide the buttons for this step. The button type is documented in the
    // [types](./types.ts) file, but in short, there are four "kinds": "next", "back", "cancel", and
    // "close."
    public get buttons(): WizardButton[] {
        return [];
    }

    /**
     * Render the main content of the step. This is where the form or other content for the step should be rendered.
     *
     * @abstract
     */
    protected abstract renderMain(): SlottedTemplateResult;

    // Override this to intercept 'next' and 'back' events, perform validation, and include enabling
    // before allowing navigation to continue.
    public handleButton(button: WizardButton, details?: NavigationEventInit) {
        if (["close", "cancel"].includes(button.kind)) {
            this.dispatchEvent(new WizardCloseEvent());
            return;
        }

        if (isNavigable(button)) {
            this.dispatchEvent(new WizardNavigationEvent(button.destination, details));
            return;
        }

        throw new Error(`Incoherent button passed: ${JSON.stringify(button, null, 2)}`);
    }

    public handleEnabling(details: NavigationEventInit) {
        this.dispatchEvent(new WizardNavigationEvent(undefined, details));
    }

    //#endregion

    //#region Lifecycle

    public constructor() {
        super();
        this.logger = ConsoleLogger.prefix(this.tagName.toLowerCase());
    }

    public override connectedCallback() {
        super.connectedCallback();

        if (!this.name) {
            const name = this.getAttribute("slot");

            if (!name) {
                throw new Error("Steps must have a unique slot attribute.");
            }

            this.name = name;
        }
    }

    //#endregion

    @bound
    protected onWizardNavigationEvent(ev: Event, button: WizardButton) {
        ev.stopPropagation();

        if (!isNavigable(button)) {
            throw new Error("Non-navigable button sent to handleNavigationEvent");
        }

        if (button.kind === "next" && !this.reportValidity()) {
            return;
        }

        this.handleButton(button);
    }

    @bound
    protected onWizardCloseEvent(ev: Event) {
        ev.stopPropagation();
        this.dispatchEvent(new WizardCloseEvent());
    }

    protected getButtonLabel(button: WizardButton): string {
        return button.label ?? ButtonKindLabelRecord[button.kind]();
    }

    protected getButtonClasses(button: WizardButton) {
        return {
            "pf-c-button": true,
            [ButtonKindClassnameRecord[button.kind]]: true,
        };
    }

    //#region Rendering

    @bound
    protected renderCloseButton(button: WizardButton) {
        return html`<div class="pf-c-wizard__footer-cancel">
            <button
                data-test-id="wizard-navigation-abort"
                class=${classMap(this.getButtonClasses(button))}
                type="button"
                @click=${this.onWizardCloseEvent}
            >
                ${this.getButtonLabel(button)}
            </button>
        </div>`;
    }

    @bound
    protected renderDisabledButton(button: WizardButton) {
        return html`<button class=${classMap(this.getButtonClasses(button))} type="button" disabled>
            ${this.getButtonLabel(button)}
        </button>`;
    }

    @bound
    protected renderNavigableButton(button: WizardButton) {
        return html`<button
            class=${classMap(this.getButtonClasses(button))}
            type="button"
            @click=${(ev: Event) => this.onWizardNavigationEvent(ev, button)}
            data-ouid-button-kind="wizard-${button.kind}"
        >
            ${this.getButtonLabel(button)}
        </button>`;
    }

    @bound
    protected renderButton(button: WizardButton) {
        return match(button)
            .with({ kind: P.union("close", "cancel") }, () => this.renderCloseButton(button))
            .with({ destination: P.string }, () => this.renderNavigableButton(button))
            .otherwise(() => {
                throw new Error("Button type is not close, disabled, or navigable?");
            });
    }

    protected renderHeaderCancelIcon() {
        return html`<button
            class="pf-c-button pf-m-plain pf-c-wizard__close"
            type="button"
            aria-label="${msg("Close")}"
            @click=${this.onWizardCloseEvent}
        >
            <i class="fas fa-times" aria-hidden="true"></i>
        </button>`;
    }

    @bound
    protected renderSidebarStep(step: WizardStepLabel) {
        const buttonClasses = {
            "pf-c-wizard__nav-link": true,
            "pf-m-disabled": !step.enabled,
            "pf-m-current": step.id === this.wizardStepState.currentStep,
        };

        return html`
                <li class="pf-c-wizard__nav-item">
                    <button
                        class=${classMap(buttonClasses)}
                        ?disabled=${!step.enabled}
                        @click=${WizardNavigationEvent.toListener(this, step.id)}
                        value=${step.id}
                    >
                        ${step.label}
                    </button>
                </li>
            </div>
        `;
    }

    protected override render() {
        if (this.wizardStepState.currentStep !== this.getAttribute("slot")) {
            return nothing;
        }

        return html`<div class="pf-c-modal-box ak-wizard-box">
            <div class="pf-c-wizard">
                <header class="pf-c-wizard__header" data-ouid-component-id="wizard-header">
                    ${this.canCancel ? this.renderHeaderCancelIcon() : nothing}
                    <h1 class="pf-c-title pf-m-3xl pf-c-wizard__title" data-test-id="wizard-title">
                        ${this.wizardTitle}
                    </h1>
                    <p class="pf-c-wizard__description">${this.wizardDescription}</p>
                </header>

                <div class="pf-c-wizard__outer-wrap">
                    <div class="pf-c-wizard__inner-wrap">
                        <aside
                            class="pf-c-wizard__nav"
                            role="group"
                            aria-label="${msg("Wizard steps")}"
                        >
                            <ol class="pf-c-wizard__nav-list">
                                ${map(this.wizardStepState.stepLabels, this.renderSidebarStep)}
                            </ol>
                        </aside>
                        <main class="pf-c-wizard__main">
                            <div id="main-content" class="pf-c-wizard__main-body">
                                ${this.renderMain()}
                            </div>
                        </main>
                    </div>
                    <nav class="pf-c-wizard__footer" aria-label="${msg("Wizard navigation")}">
                        ${this.buttons.map(this.renderButton)}
                    </nav>
                </div>
            </div>
        </div>`;
    }

    //#endregion
}

declare global {
    interface WizardNavigationTestIDMap {
        abort: HTMLButtonElement;
    }

    interface WizardTestIDMap {
        navigation: WizardNavigationTestIDMap;
        title: HTMLHeadingElement;
    }

    interface TestIDSelectorMap {
        wizard: WizardTestIDMap;
    }
}
