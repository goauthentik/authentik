import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";

import { msg } from "@lit/localize";
import { property } from "@lit/reactive-element/decorators/property.js";
import { state } from "@lit/reactive-element/decorators/state.js";
import { html, nothing } from "lit";
import type { TemplateResult } from "lit";

/**
 * @class AkWizard
 *
 * @element ak-wizard
 *
 * The ak-wizard element exists to guide users through a complex task by dividing it into sections
 * and granting them successive access to future sections. Our wizard has four "zones": The header,
 * the breadcrumb toolbar, the navigation controls, and the content of the panel.
 *
 */

type WizardStep = {
    name: string;
    constructor: () => TemplateResult;
};

export class AkWizard extends ModalButton {
    @property({ type: Boolean })
    required = false;

    @property()
    wizardtitle?: string;

    @property()
    description?: string;

    constructor() {
        super();
        this.handleClose = this.handleClose.bind(this);
    }

    handleClose() {
        this.open = false;
    }

    renderModalInner() {
        return html`<div class="pf-c-wizard">
            ${this.renderWizardHeader()}
            <div class="pf-c-wizard__outer-wrap">
                <div class="pf-c-wizard__inner-wrap">${this.renderWizardNavigation()}</div>
            </div>
        </div> `;
    }

    renderWizardHeader() {
        const renderCancelButton = () =>
            html`<button
                class="pf-c-button pf-m-plain pf-c-wizard__close"
                type="button"
                aria-label="${msg("Close")}"
                @click=${this.handleClose}
            >
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>`;

        return html`<div class="pf-c-wizard__header">
            ${this.required ? nothing : renderCancelButton()}
            <h1 class="pf-c-title pf-m-3xl pf-c-wizard__title">${this.wizardtitle}</h1>
            <p class="pf-c-wizard__description">${this.description}</p>
        </div>`;
    }

    renderWizardNavigation() {
        const currentIdx = this.currentStep ? this.steps.indexOf(this.currentStep.slot) : 0;

        const renderNavStep = (step: string, idx: number) => {
            return html`
                <li class="pf-c-wizard__nav-item">
                    <button
                        class="pf-c-wizard__nav-link ${idx === currentIdx ? "pf-m-current" : ""}"
                        ?disabled=${currentIdx < idx}
                        @click=${() => {
                            const stepEl = this.querySelector<WizardPage>(`[slot=${step}]`);
                            if (stepEl) {
                                this.currentStep = stepEl;
                            }
                        }}
                    >
                        ${this.querySelector<WizardPage>(`[slot=${step}]`)?.sidebarLabel()}
                    </button>
                </li>
            `;
        };

        return html` <nav class="pf-c-wizard__nav">
            <ol class="pf-c-wizard__nav-list">
                ${map(this.steps, renderNavStep)}
            </ol>
        </nav>`;
    }
}
