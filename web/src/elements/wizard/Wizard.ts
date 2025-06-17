import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/wizard/ActionWizardPage";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { property } from "@lit/reactive-element/decorators/property.js";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

export interface WizardAction {
    displayName: string;
    subText?: string;
    run: () => Promise<boolean>;
}

export const ApplyActionsSlot = "apply-actions";

@customElement("ak-wizard")
export class Wizard extends ModalButton {
    static styles: CSSResult[] = [
        ...super.styles,
        PFWizard,
        css`
            .pf-c-modal-box {
                height: 75%;
            }
        `,
    ];

    //#region Properties

    /**
     * Whether the wizard can be cancelled.
     */
    @property({ type: Boolean })
    public cancelable = true;

    /**
     * Whether the wizard can go back to the previous step.
     */
    @property({ type: Boolean })
    public canBack = true;

    /**
     * Header title of the wizard.
     */
    @property()
    public header?: string;

    /**
     * Description of the wizard.
     */
    @property()
    public description?: string;

    /**
     * Whether the wizard is valid and can proceed to the next step.
     */
    @property({ type: Boolean })
    public isValid?: boolean;

    /**
     * Actions to display at the end of the wizard.
     */
    @property({ attribute: false })
    public actions: WizardAction[] = [];

    @property({ attribute: false })
    public finalHandler?: () => Promise<void>;

    @property({ attribute: false })
    public state: { [key: string]: unknown } = {};

    //#endregion

    //#region State

    /**
     * Memoized step tag names.
     */
    @state()
    _steps: string[] = [];

    /**
     * Step tag names present in the wizard.
     */
    get steps(): string[] {
        return this._steps;
    }

    set steps(nextSteps: string[]) {
        const addApplyActionsSlot = this._steps.includes(ApplyActionsSlot);

        this._steps = nextSteps;

        if (addApplyActionsSlot) {
            this.steps.push(ApplyActionsSlot);
        }

        for (const step of this._steps) {
            const existingStepElement = this.getStepElementByName(step);

            if (existingStepElement) continue;

            const stepElement = document.createElement(step);

            stepElement.slot = step;
            stepElement.dataset.wizardmanaged = "true";

            this.appendChild(stepElement);
        }

        this.requestUpdate();
    }

    /**
     * Initial steps to reset to.
     */
    _initialSteps: string[] = [];

    @state()
    _activeStep?: WizardPage;

    set activeStepElement(nextActiveStepElement: WizardPage | undefined) {
        this._activeStep = nextActiveStepElement;

        if (!this._activeStep) return;

        this._activeStep.activeCallback();
        this._activeStep.requestUpdate();
    }

    /**
     * The active step element being displayed.
     */
    get activeStepElement(): WizardPage | undefined {
        return this._activeStep;
    }

    getStepElementByIndex(stepIndex: number): WizardPage | null {
        const stepName = this._steps[stepIndex];

        return this.querySelector<WizardPage>(`[slot=${stepName}]`);
    }

    getStepElementByName(stepName: string): WizardPage | null {
        return this.querySelector<WizardPage>(`[slot=${stepName}]`);
    }

    //#endregion

    //#region Lifecycle

    firstUpdated(): void {
        this._initialSteps = this._steps;
    }

    /**
     * Add action to the beginning of the list.
     */
    addActionBefore(displayName: string, run: () => Promise<boolean>): void {
        this.actions.unshift({
            displayName,
            run,
        });
    }

    /**
     * Add action at the end of the list.
     *
     * @todo: Is this used?
     */
    addActionAfter(displayName: string, run: () => Promise<boolean>): void {
        this.actions.push({
            displayName,
            run,
        });
    }

    /**
     * Reset the wizard to it's initial state.
     */
    reset = (ev?: Event) => {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        this.open = false;

        this.querySelectorAll("[data-wizardmanaged=true]").forEach((el) => {
            el.remove();
        });

        for (const step of this.steps) {
            const stepElement = this.getStepElementByName(step);

            stepElement?.reset?.();
        }

        this.steps = this._initialSteps;
        this.actions = [];
        this.state = {};
        this.activeStepElement = undefined;
        this.canBack = true;
        this.cancelable = true;
    };

    //#endregion

    //#region Rendering

    public override renderModalInner(): TemplateResult {
        const firstPage = this.getStepElementByIndex(0);

        if (!this.activeStepElement && firstPage) {
            this.activeStepElement = firstPage;
        }

        const activeStepIndex = this.activeStepElement
            ? this.steps.indexOf(this.activeStepElement.slot)
            : 0;

        let lastPage = activeStepIndex === this.steps.length - 1;

        if (lastPage && !this.steps.includes("ak-wizard-page-action") && this.actions.length > 0) {
            this.steps = this.steps.concat("ak-wizard-page-action");
            lastPage = activeStepIndex === this.steps.length - 1;
        }

        const navigateToPreviousStep = () => {
            const prevPage = this.getStepElementByIndex(activeStepIndex - 1);

            if (prevPage) {
                this.activeStepElement = prevPage;
            }
        };

        return html`<div role="presentation" class="pf-c-wizard">
            <header role="presentation" class="pf-c-wizard__header">
                ${this.cancelable
                    ? html`<button
                          data-test-id="wizard-close"
                          class="pf-c-button pf-m-plain pf-c-wizard__close"
                          type="button"
                          aria-label="${msg("Close")}"
                          @click=${(ev: Event) => this.reset(ev)}
                      >
                          <i class="fas fa-times" aria-hidden="true"></i>
                      </button>`
                    : nothing}
                <h1
                    id="modal-title"
                    role="heading"
                    aria-level="1"
                    class="pf-c-title pf-m-3xl pf-c-wizard__title"
                    data-test-id="wizard-heading"
                >
                    ${this.header}
                </h1>
                <p
                    role="heading"
                    aria-level="2"
                    id="modal-description"
                    class="pf-c-wizard__description"
                >
                    ${this.description}
                </p>
            </header>

            <div role="presentation" class="pf-c-wizard__outer-wrap">
                <div class="pf-c-wizard__inner-wrap">
                    <nav aria-label="${msg("Wizard navigation")}" class="pf-c-wizard__nav">
                        <ol role="presentation" class="pf-c-wizard__nav-list">
                            ${this.steps.map((step, idx) => {
                                const stepEl = this.getStepElementByName(step);

                                if (!stepEl) return html`<p>Unexpected missing step: ${step}</p>`;

                                const sidebarLabel = stepEl.sidebarLabel();

                                return html`
                                    <li role="presentation" class="pf-c-wizard__nav-item">
                                        <button
                                            class=${classMap({
                                                "pf-c-wizard__nav-link": true,
                                                "pf-m-current": idx === activeStepIndex,
                                            })}
                                            ?disabled=${activeStepIndex < idx}
                                            @click=${() => {
                                                this.activeStepElement = stepEl;
                                            }}
                                        >
                                            ${sidebarLabel}
                                        </button>
                                    </li>
                                `;
                            })}
                        </ol>
                    </nav>
                    <main aria-label="${msg("Wizard content")}" class="pf-c-wizard__main">
                        <div role="presentation" class="pf-c-wizard__main-body">
                            <slot name=${this.activeStepElement?.slot || this.steps[0]}></slot>
                        </div>
                    </main>
                </div>
                <nav class="pf-c-wizard__footer" aria-label="${msg("Wizard navigation")}">
                    <button
                        data-test-id="wizard-navigation-next"
                        class="pf-c-button pf-m-primary"
                        type="submit"
                        ?disabled=${!this.isValid}
                        @click=${async () => {
                            const completedStep = await this.activeStepElement?.nextCallback();
                            if (!completedStep) return;

                            if (lastPage) {
                                await this.finalHandler?.();
                                this.reset();

                                return;
                            }

                            const nextPage = this.getStepElementByIndex(activeStepIndex + 1);

                            if (nextPage) {
                                this.activeStepElement = nextPage;
                            }
                        }}
                    >
                        ${lastPage ? msg("Finish") : msg("Next")}
                    </button>
                    ${(this.activeStepElement
                        ? this.steps.indexOf(this.activeStepElement.slot)
                        : 0) > 0 && this.canBack
                        ? html`
                              <button
                                  data-test-id="wizard-navigation-previous"
                                  class="pf-c-button pf-m-secondary"
                                  type="button"
                                  @click=${navigateToPreviousStep}
                              >
                                  ${msg("Back")}
                              </button>
                          `
                        : nothing}
                    ${this.cancelable
                        ? html`<div class="pf-c-wizard__footer-abort">
                              <button
                                  data-test-id="wizard-navigation-cancel"
                                  class="pf-c-button pf-m-link"
                                  type="button"
                                  @click=${(ev: Event) => this.reset(ev)}
                              >
                                  ${msg("Cancel")}
                              </button>
                          </div>`
                        : nothing}
                </nav>
            </div>
        </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard": Wizard;
    }

    interface WizardNavigationTestIDMap {
        next: HTMLButtonElement;
        previous: HTMLButtonElement;
        cancel: HTMLButtonElement;
    }

    interface WizardTestIDMap {
        navigation: WizardNavigationTestIDMap;
    }

    interface TestIDSelectorMap {
        wizard: WizardTestIDMap;
    }
}
