import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import { bound } from "@goauthentik/elements/decorators/bound";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { customElement, property, query } from "@lit/reactive-element/decorators.js";
import { TemplateResult, css, html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

import { WizardCloseEvent, WizardNavigationEvent } from "./events";
import {
    type ButtonKind,
    type DisabledWizardButton,
    type NavigableButton,
    type WizardButton,
    WizardStepLabel,
} from "./types";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isDisabledButton = (v: any): v is DisabledWizardButton =>
    typeof v === "object" && v !== null && "disabled" in v && v.disabled;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isNavigableButton = (v: any): v is NavigableButton =>
    !isDisabledButton(v) && "destination" in v && typeof v.destination === "string";

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
 * @slot trigger - (Inherited from ModalButton) Define the "summon modal" button here
 *
 * @fires ak-wizard-nav - Tell the orchestrator what page the user wishes to move to.
 *
 */

@customElement("ak-wizard-frame")
export class AkWizardFrame extends CustomEmitterElement(ModalButton) {
    static get styles() {
        return [
            ...super.styles,
            PFWizard,
            css`
                .pf-c-modal-box {
                    height: 75%;
                }
            `,
        ];
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
            @click=${(ev: Event) => {
                ev.stopPropagation();
                this.dispatchEvent(new WizardCloseEvent());
            }}
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
                    @click=${(ev: Event) => {
                        ev.stopPropagation();
                        this.dispatchEvent(new WizardNavigationEvent(step.id));
                    }}
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

    @bound
    renderButton(button: WizardButton) {
        const buttonClasses = {
            "pf-c-button": true,
            [BUTTON_KIND_TO_CLASS[button.kind]]: true,
        };

        const label = button.label ?? BUTTON_KIND_TO_LABEL[button.kind];

        if (["close", "cancel"].includes(button.kind)) {
            return html`<div class="pf-c-wizard__footer-cancel">
                <button
                    class=${classMap(buttonClasses)}
                    type="button"
                    @click=${(ev: Event) => {
                        ev.stopPropagation();
                        this.dispatchEvent(new WizardCloseEvent());
                    }}
                >
                    ${label}
                </button>
            </div>`;
        }

        if (isDisabledButton(button)) {
            return html`<button class=${classMap(buttonClasses)} type="button" disabled>
                ${label}
            </button>`;
        }

        if (isNavigableButton(button)) {
            return html`<button
                class=${classMap(buttonClasses)}
                type="button"
                @click=${(ev: Event) => {
                    ev.stopPropagation();
                    this.dispatchEvent(new WizardNavigationEvent(button.destination));
                }}
            >
                ${label}
            </button>`;
        }

        console.warn(button);
        throw new Error("Button type is not close, disabled, or navigable?");
    }

    renderFooter() {
        return html`
            <footer class="pf-c-wizard__footer">${map(this.buttons, this.renderButton)}</footer>
        `;
    }
}

export default AkWizardFrame;

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-frame": AkWizardFrame;
    }
}
