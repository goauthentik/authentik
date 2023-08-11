import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { msg } from "@lit/localize";
import { customElement, property, state } from "@lit/reactive-element/decorators.js";
import { html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";

import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

import { akWizardCurrentStepContextName } from "./akWizardCurrentStepContextName";
import { akWizardStepsContextName } from "./akWizardStepsContextName";
import type { WizardStep } from "./types";

/**
 * AKWizardFrame is the main container for displaying Wizard pages.
 *
 * AKWizardFrame is one component of a total Wizard development environment. It provides the header,
 * titled navigation sidebar, and bottom row button bar. It takes its cues about what to render from
 * two data structure, `this.steps: WizardStep[]`, which lists all the current steps *in order* and
 * doesn't care otherwise about their structure, and `this.currentStep: WizardStep` which must be a
 * _reference_ to a member of `this.steps`.
 *
 * @element ak-wizard-frame
 *
 * @fires ak-wizard-nav - Tell the orchestrator what page the user wishes to move to. This is the
 * only event that causes this wizard to change its appearance.
 *
 * NOTE: The event name is configurable as an attribute.
 *
 */

@customElement("ak-wizard-frame")
export class AkWizardFrame extends CustomEmitterElement(ModalButton) {
    static get styles() {
        return [...super.styles, PFWizard];
    }

    @property({ type: Boolean })
    canCancel = true;

    @property()
    header?: string;

    @property()
    description?: string;

    @property()
    eventName: string = "ak-wizard-nav";

    // @ts-expect-error
    @consume({ context: akWizardStepsContextName, subscribe: true })
    @state()
    steps!: WizardStep[];

    // @ts-expect-error
    @consume({ context: akWizardCurrentStepContextName, subscribe: true })
    @state()
    currentStep!: WizardStep;

    reset() {
        this.open = false;
    }

    get maxStep() {
        return this.steps.length - 1;
    }

    get nextStep() {
        const idx = this.steps.findIndex((step) => step === this.currentStep);
        return idx < this.maxStep ? this.steps[idx + 1] : undefined;
    }

    get backStep() {
        const idx = this.steps.findIndex((step) => step === this.currentStep);
        return idx > 0 ? this.steps[idx - 1] : undefined;
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
            @click=${() => this.reset()}
        >
            <i class="fas fa-times" aria-hidden="true"></i>
        </button>`;
    }

    renderNavigation() {
        return html`<nav class="pf-c-wizard__nav">
            <ol class="pf-c-wizard__nav-list">
                ${this.steps.map((step) => this.renderNavigationStep(step))}
            </ol>
        </nav>`;
    }

    renderNavigationStep(step: WizardStep) {
        const buttonClasses = {
            "pf-c-wizard__nav-link": true,
            "pf-m-current": step.id === this.currentStep.id,
        };

        return html`
            <li class="pf-c-wizard__nav-item">
                <button
                    class=${classMap(buttonClasses)}
                    ?disabled=${step.disabled}
                    @click=${() => this.dispatchCustomEvent(this.eventName, { step: step.id })}
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
            <div class="pf-c-wizard__main-body">${this.currentStep.renderer()}</div>
        </main>`;
    }

    renderFooter() {
        return html`
            <footer class="pf-c-wizard__footer">
                ${this.nextStep ? this.renderFooterNextButton(this.nextStep) : nothing}
                ${this.backStep ? this.renderFooterBackButton(this.backStep) : nothing}
                ${this.canCancel ? this.renderFooterCancelButton() : nothing}
            </footer>
        `;
    }

    renderFooterNextButton(nextStep: WizardStep) {
        return html`<button
            class="pf-c-button pf-m-primary"
            type="submit"
            ?disabled=${!this.currentStep.valid}
            @click=${() => this.dispatchCustomEvent(this.eventName, { step: nextStep.id })}
        >
            ${this.currentStep.nextButtonLabel}
        </button>`;
    }

    renderFooterBackButton(backStep: WizardStep) {
        return html`
            <button
                class="pf-c-button pf-m-secondary"
                type="button"
                @click=${() => this.dispatchCustomEvent(this.eventName, { step: backStep.id })}
            >
                ${this.currentStep.backButtonLabel}
            </button>
        `;
    }

    renderFooterCancelButton() {
        return html`<div class="pf-c-wizard__footer-cancel">
            <button class="pf-c-button pf-m-link" type="button" @click=${() => this.reset()}>
                ${msg("Cancel")}
            </button>
        </div>`;
    }
}

export default AkWizardFrame;
