import { NavigationEventInit, WizardNavigationEvent } from "./events.js";
import {
    ButtonKindClassnameRecord,
    ButtonKindLabelRecord,
    DialogDismissalKinds,
    isNavigable,
    type WizardButton,
    WizardStepLabel,
    WizardStepState,
} from "./shared.js";
import { wizardStepContext } from "./WizardContexts.js";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";
import { findNearestDialog } from "#elements/utils/render-roots";

import { ConsoleLogger } from "#logger/browser";

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
 */
export abstract class WizardStep extends AKElement {
    public static styles = [
        PFWizard,
        PFContent,
        PFTitle,
        css`
            :host {
                display: contents;
            }

            .pf-c-wizard__main-body {
                display: flex;
                flex-flow: row wrap;

                & > * {
                    flex: 1 1 auto;
                }
            }
        `,
    ];

    /**
     * A prefixed logger for this component.
     */
    protected logger = ConsoleLogger.prefix(this.localName);

    @property({ type: Boolean, attribute: true, reflect: true })
    public enabled = false;

    @property({ attribute: false })
    public dialog: HTMLDialogElement | null = null;

    /**
     * The name. Should match the slot. Reflected if not present.
     */
    @property({ type: String, attribute: true, reflect: true })
    public name?: string;

    @consume({ context: wizardStepContext, subscribe: true })
    protected wizardStepState: WizardStepState = { currentStep: null, stepLabels: [] };

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
    protected abstract buttons: WizardButton[];

    /**
     * Render the main content of the step. This is where the form or other content for the step should be rendered.
     *
     * @abstract
     */
    protected abstract renderMain(): SlottedTemplateResult;

    // Override this to intercept 'next' and 'back' events, perform validation, and include enabling
    // before allowing navigation to continue.
    public handleButton(button: WizardButton, details?: NavigationEventInit) {
        if (DialogDismissalKinds.has(button.kind)) {
            return this.requestClose(button.kind);
        }

        if (isNavigable(button)) {
            return this.dispatchEvent(new WizardNavigationEvent(details, button.destination));
        }

        throw new Error(`Incoherent button passed: ${JSON.stringify(button, null, 2)}`);
    }

    public dispatchNavigationEvent(details: NavigationEventInit) {
        this.dispatchEvent(new WizardNavigationEvent(details));
    }

    //#endregion

    //#region Lifecycle

    public override connectedCallback() {
        super.connectedCallback();

        this.dialog ??= findNearestDialog(this);

        if (!this.name) {
            const name = this.getAttribute("slot");

            if (!name) {
                throw new Error("Steps must have a unique slot attribute.");
            }

            this.name = name;
        }
    }

    //#endregion

    protected navigateWizardStep(button: WizardButton, event?: Event) {
        event?.stopPropagation();

        if (!isNavigable(button)) {
            throw new Error("Non-navigable button sent to handleNavigationEvent");
        }

        if (button.kind === "next" || button.kind === "finish") {
            // Check and report form validation to the user before allowing navigation to proceed.
            if (!this.reportValidity()) {
                return;
            }
        }

        if (button.kind === "finish") {
            this.requestClose("finish");
            return;
        }

        return this.handleButton(button);
    }

    public requestClose = (returnValue?: string) => {
        if (!this.dialog) {
            this.logger.warn("Skipping close request: No dialog found for wizard.");
            return;
        }

        this.dialog.requestClose(returnValue);
    };

    protected getButtonLabel(button: WizardButton): SlottedTemplateResult {
        return button.label ?? ButtonKindLabelRecord[button.kind]();
    }

    protected getButtonClasses(button: WizardButton) {
        return {
            "pf-c-button": true,
            [ButtonKindClassnameRecord[button.kind]]: true,
        };
    }

    //#region Rendering

    protected renderCloseButton(button: WizardButton) {
        return html`<div class="pf-c-wizard__footer-cancel">
            <button
                data-test-id="wizard-navigation-abort"
                class=${classMap(this.getButtonClasses(button))}
                type="button"
                @click=${() => this.requestClose("cancel")}
            >
                ${this.getButtonLabel(button)}
            </button>
        </div>`;
    }

    protected renderDisabledButton(button: WizardButton) {
        return html`<button class=${classMap(this.getButtonClasses(button))} type="button" disabled>
            ${this.getButtonLabel(button)}
        </button>`;
    }

    protected renderNavigableButton(button: WizardButton) {
        return html`<button
            class=${classMap(this.getButtonClasses(button))}
            type="button"
            @click=${this.navigateWizardStep.bind(this, button)}
            data-ouid-button-kind="wizard-${button.kind}"
        >
            ${this.getButtonLabel(button)}
        </button>`;
    }

    protected renderButton = (button: WizardButton) => {
        return match(button)
            .with({ kind: P.union("close", "cancel") }, () => this.renderCloseButton(button))
            .with({ destination: P.string }, () => this.renderNavigableButton(button))
            .otherwise(() => {
                throw new Error("Button type is not close, disabled, or navigable?");
            });
    };

    protected renderHeaderCancelIcon() {
        return html`<button
            class="pf-c-button pf-m-plain pf-c-wizard__close"
            type="button"
            aria-label="${msg("Close")}"
            @click=${() => this.requestClose("cancel")}
        >
            <i class="fas fa-times" aria-hidden="true"></i>
        </button>`;
    }

    protected renderSidebarStep = (step: WizardStepLabel) => {
        const buttonClasses = {
            "pf-c-wizard__nav-link": true,
            "pf-m-disabled": !step.enabled,
            "pf-m-current": step.id === this.wizardStepState.currentStep,
        };

        return html`<li class="pf-c-wizard__nav-item">
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
    };

    protected override render() {
        if (this.wizardStepState.currentStep !== this.getAttribute("slot")) {
            return nothing;
        }

        return html`<div class="pf-c-wizard">
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
                    <main
                        part="wizard-main"
                        class="pf-c-wizard__main ak-m-thin-scrollbar ak-m-scroll-shadows"
                        aria-label=${msg("Wizard content")}
                    >
                        <div id="main-content" class="pf-c-wizard__main-body">
                            ${this.renderMain()}
                        </div>
                    </main>
                </div>
                <nav class="pf-c-wizard__footer" aria-label="${msg("Wizard navigation")}">
                    ${this.buttons.map(this.renderButton)}
                </nav>
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
