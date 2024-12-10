import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound";
import { P, match } from "ts-pattern";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

import { wizardStepContext } from "./WizardContexts.js";
import { NavigationUpdate, WizardCloseEvent, WizardNavigationEvent } from "./events.js";
import { WizardStepLabel, WizardStepState } from "./types";
import { type ButtonKind, type NavigableButton, type WizardButton } from "./types";

const isNavigable = (b: WizardButton): b is NavigableButton =>
    "destination" in b && typeof b.destination === "string" && b.destination.length > 0;

const BUTTON_KIND_TO_CLASS: Record<ButtonKind, string> = {
    next: "pf-m-primary",
    back: "pf-m-secondary",
    close: "pf-m-link",
    cancel: "pf-m-link",
};

const BUTTON_KIND_TO_LABEL: Record<ButtonKind, string> = {
    next: msg("Next"),
    back: msg("Back"),
    cancel: msg("Cancel"),
    close: msg("Close"),
};

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

export class WizardStep extends AKElement {
    // These additions are necessary because we don't want to inherit *all* of the modal box
    // modifiers, just the ones related to managing the height of the display box.
    static get styles() {
        return [
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
    }

    @property({ type: Boolean, attribute: true, reflect: true })
    enabled = false;

    /**
     * The name. Should match the slot. Reflected if not present.
     */
    @property({ type: String, attribute: true, reflect: true })
    name?: string;

    @consume({ context: wizardStepContext, subscribe: true })
    wizardStepState: WizardStepState = { currentStep: undefined, stepLabels: [] };

    /**
     * What appears in the titlebar of the Wizard. Usually, but not necessarily, the same for all
     * steps. Recommendation: Set this, the description, and `canCancel` in a subclass, and stop
     * worrying about them.
     */
    wizardTitle = "--unset--";

    /**
     * The text for a descriptive subtitle for the wizard
     */
    wizardDescription?: string;

    /**
     * Show the [Cancel] icon and offer the [Cancel] button
     */
    canCancel = false;

    /**
     * The ID of the current step.
     */
    id = "";

    /**
     *The label of the current step.  Displayed in the navigation bar.
     */
    label: string = "--unset--";

    /**
     * If true, this step's label will not be shown in the navigation bar
     */
    hide = false;

    //  ___      _    _ _        _   ___ ___
    // | _ \_  _| |__| (_)__    /_\ | _ \_ _|
    // |  _/ || | '_ \ | / _|  / _ \|  _/| |
    // |_|  \_,_|_.__/_|_\__| /_/ \_\_| |___|
    //

    // Override this and provide the buttons for this step. The button type is documented in the
    // [types](./types.ts) file, but in short, there are four "kinds": "next", "back", "cancel", and
    // "close."
    public get buttons(): WizardButton[] {
        return [];
    }

    // Override this to provide the form.
    public renderMain() {
        throw new Error("This must be overridden in client classes");
    }

    // Override this to intercept 'next' and 'back' events, perform validation, and include enabling
    // before allowing navigation to continue.
    public handleButton(button: WizardButton, details?: NavigationUpdate) {
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

    public handleEnabling(details: NavigationUpdate) {
        this.dispatchEvent(new WizardNavigationEvent(undefined, details));
    }

    // END Public API

    connectedCallback() {
        super.connectedCallback();
        if (!this.name) {
            const name = this.getAttribute("slot");
            if (!name) {
                throw new Error("Steps must have a unique slot attribute.");
            }
            this.name = name;
        }
    }

    @bound
    onWizardNavigationEvent(ev: Event, button: WizardButton) {
        ev.stopPropagation();
        if (!isNavigable(button)) {
            throw new Error("Non-navigable button sent to handleNavigationEvent");
        }
        this.handleButton(button);
    }

    @bound
    onWizardCloseEvent(ev: Event) {
        ev.stopPropagation();
        this.dispatchEvent(new WizardCloseEvent());
    }

    @bound
    onSidebarNav(ev: PointerEvent) {
        ev.stopPropagation();
        const target = (ev.target as HTMLButtonElement).value;
        this.dispatchEvent(new WizardNavigationEvent(target));
    }

    getButtonLabel(button: WizardButton) {
        return button.label ?? BUTTON_KIND_TO_LABEL[button.kind];
    }

    getButtonClasses(button: WizardButton) {
        return {
            "pf-c-button": true,
            [BUTTON_KIND_TO_CLASS[button.kind]]: true,
        };
    }

    @bound
    renderCloseButton(button: WizardButton) {
        return html`<div class="pf-c-wizard__footer-cancel">
            <button
                class=${classMap(this.getButtonClasses(button))}
                type="button"
                @click=${this.onWizardCloseEvent}
            >
                ${this.getButtonLabel(button)}
            </button>
        </div>`;
    }

    @bound
    renderDisabledButton(button: WizardButton) {
        return html`<button class=${classMap(this.getButtonClasses(button))} type="button" disabled>
            ${this.getButtonLabel(button)}
        </button>`;
    }

    @bound
    renderNavigableButton(button: WizardButton) {
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
    renderButton(button: WizardButton) {
        return match(button)
            .with({ kind: P.union("close", "cancel") }, () => this.renderCloseButton(button))
            .with({ destination: P.string }, () => this.renderNavigableButton(button))
            .otherwise(() => {
                throw new Error("Button type is not close, disabled, or navigable?");
            });
    }

    renderHeaderCancelIcon() {
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
    renderSidebarStep(step: WizardStepLabel) {
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
                        @click=${this.onSidebarNav}
                        value=${step.id}
                    >
                        ${step.label}
                    </button>
                </li>
            </div>
        `;
    }

    render() {
        return this.wizardStepState.currentStep === this.getAttribute("slot")
            ? html` <div class="pf-c-modal-box ak-wizard-box">
                  <div class="pf-c-wizard">
                      <div class="pf-c-wizard__header" data-ouid-component-id="wizard-header">
                          ${this.canCancel ? this.renderHeaderCancelIcon() : nothing}
                          <h1 class="pf-c-title pf-m-3xl pf-c-wizard__title">
                              ${this.wizardTitle}
                          </h1>
                          <p class="pf-c-wizard__description">${this.wizardDescription}</p>
                      </div>

                      <div class="pf-c-wizard__outer-wrap">
                          <div class="pf-c-wizard__inner-wrap">
                              <nav class="pf-c-wizard__nav" data-ouid-component-id="wizard-navbar">
                                  <ol class="pf-c-wizard__nav-list">
                                      ${map(
                                          this.wizardStepState.stepLabels,
                                          this.renderSidebarStep,
                                      )}
                                  </ol>
                              </nav>
                              <main class="pf-c-wizard__main">
                                  <div
                                      id="main-content"
                                      class="pf-c-wizard__main-body"
                                      data-ouid-component-id="wizard-body"
                                  >
                                      ${this.renderMain()}
                                  </div>
                              </main>
                          </div>
                          <footer
                              class="pf-c-wizard__footer"
                              data-ouid-component-id="wizard-footer"
                          >
                              ${this.buttons.map(this.renderButton)}
                          </footer>
                      </div>
                  </div>
              </div>`
            : nothing;
    }
}
