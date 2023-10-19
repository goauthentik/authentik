import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { customElement, property, query } from "@lit/reactive-element/decorators.js";
import { TemplateResult, html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

import { type WizardButton, WizardStepLabel } from "./types";

/**
 * AKWizardFrame is the main container for displaying Wizard pages.
 *
 * AKWizardFrame is one component of a Wizard development environment. It provides the header,
 * titled navigation sidebar, and bottom row button bar. It takes its cues about what to render from
 * two data structure, `this.steps: WizardStep[]`, which lists all the current steps *in order* and
 * doesn't care otherwise about their structure, and `this.currentStep: WizardStep` which must be a
 * _reference_ to a member of `this.steps`.
 *
 * @element ak-wizard-frame
 *
 * @slot - Where the form itself should go
 *
 * @fires ak-wizard-nav - Tell the orchestrator what page the user wishes to move to.
 *
 */

@customElement("ak-wizard-frame")
export class AkWizardFrame extends CustomEmitterElement(ModalButton) {
    static get styles() {
        return [...super.styles, PFWizard];
    }

    /**
     * The text for the title of the wizard
     */
    @property()
    header?: string;

    /**
     * The text for a descriptive subtitle for the wizard
     */
    @property()
    description?: string;

    /**
     * The labels for all current steps, including their availability
     */
    @property({ attribute: false, type: Array })
    stepLabels!: WizardStepLabel[];

    /**
     * What buttons to Show
     */
    @property({ attribute: false, type: Array })
    buttons: WizardButton[] = [];

    /**
     * Show the [Cancel] icon and offer the [Cancel] button
     */
    @property({ type: Boolean, attribute: "can-cancel" })
    canCancel = false;

    /**
     * The form renderer, passed as a function
     */
    @property({ type: Object })
    form!: () => TemplateResult;

    @query("#main-content *:first-child")
    content!: HTMLElement;

    constructor() {
        super();
        this.renderButtons = this.renderButtons.bind(this);
    }

    renderModalInner() {
        // prettier-ignore
        return html`<div class="pf-c-wizard">
            ${this.renderHeader()}
            <div class="pf-c-wizard__outer-wrap">
                <div class="pf-c-wizard__inner-wrap">
                    ${this.renderNavigation()} 
                    ${this.renderMainSection()}
                </div>
                ${this.renderFooter()}
            </div>
        </div>`;
    }

    renderHeader() {
        return html`<div class="pf-c-wizard__header">
            ${this.canCancel ? this.renderHeaderCancelIcon() : nothing}
            <h1 class="pf-c-title pf-m-3xl pf-c-wizard__title">${this.header}</h1>
            <p class="pf-c-wizard__description">${this.description}</p>
        </div>`;
    }

    renderHeaderCancelIcon() {
        return html`<button
            class="pf-c-button pf-m-plain pf-c-wizard__close"
            type="button"
            aria-label="${msg("Close")}"
            @click=${() => this.dispatchCustomEvent("ak-wizard-nav", { command: "close" })}
        >
            <i class="fas fa-times" aria-hidden="true"></i>
        </button>`;
    }

    renderNavigation() {
        return html`<nav class="pf-c-wizard__nav">
            <ol class="pf-c-wizard__nav-list">
                ${this.stepLabels.map((step) => {
                    return this.renderNavigationStep(step);
                })}
            </ol>
        </nav>`;
    }

    renderNavigationStep(step: WizardStepLabel) {
        const buttonClasses = {
            "pf-c-wizard__nav-link": true,
            "pf-m-current": step.active,
        };

        return html`
            <li class="pf-c-wizard__nav-item">
                <button
                    class=${classMap(buttonClasses)}
                    ?disabled=${step.disabled}
                    @click=${() =>
                        this.dispatchCustomEvent("ak-wizard-nav", {
                            command: "goto",
                            step: step.index,
                        })}
                >
                    ${step.label}
                </button>
            </li>
        `;
    }

    // This is where the panel is shown. We expect the panel to get its information from an
    // independent context.
    renderMainSection() {
        return html`<main class="pf-c-wizard__main">
            <div id="main-content" class="pf-c-wizard__main-body">${this.form()}</div>
        </main>`;
    }

    renderFooter() {
        return html`
            <footer class="pf-c-wizard__footer">${map(this.buttons, this.renderButtons)}</footer>
        `;
    }

    renderButtons([label, command]: WizardButton) {
        switch (command.command) {
            case "next":
                return this.renderButton(label, "pf-m-primary", command.command);
            case "back":
                return this.renderButton(label, "pf-m-secondary", command.command);
            case "close":
                return this.renderLink(label, "pf-m-link");
            default:
                throw new Error(`Button type not understood: ${command} for ${label}`);
        }
    }

    renderButton(label: string, classname: string, command: string) {
        const buttonClasses = { "pf-c-button": true, [classname]: true };
        return html`<button
            class=${classMap(buttonClasses)}
            type="button"
            @click=${() => {
                this.dispatchCustomEvent("ak-wizard-nav", { command });
            }}
        >
            ${label}
        </button>`;
    }

    renderLink(label: string, classname: string) {
        const buttonClasses = { "pf-c-button": true, [classname]: true };
        return html`<div class="pf-c-wizard__footer-cancel">
            <button
                class=${classMap(buttonClasses)}
                type="button"
                @click=${() => this.dispatchCustomEvent("ak-wizard-nav", { command: "close" })}
            >
                ${label}
            </button>
        </div>`;
    }
}

export default AkWizardFrame;
