import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { property } from "@lit/reactive-element/decorators/property.js";
import { CSSResult, TemplateResult, html } from "lit";
import { state } from "lit/decorators.js";

import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

import { ModalButton } from "../buttons/ModalButton";
import "./ActionWizardPage";
import { WizardPage } from "./WizardPage";

export interface WizardAction {
    displayName: string;
    subText?: string;
    run: () => Promise<boolean>;
}

export const ApplyActionsSlot = "apply-actions";

@customElement("ak-wizard")
export class Wizard extends ModalButton {
    @property()
    header?: string;

    @property()
    description?: string;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFWizard);
    }

    @property({ attribute: false })
    steps: string[] = [];

    _initialSteps: string[] = [];

    @property({ attribute: false })
    actions: WizardAction[] = [];

    @state()
    _currentStep?: WizardPage;

    set currentStep(value: WizardPage | undefined) {
        this._currentStep = value;
        if (this._currentStep) {
            this._currentStep.activeCallback();
            this._currentStep.requestUpdate();
        }
    }

    get currentStep(): WizardPage | undefined {
        return this._currentStep;
    }

    @property({ attribute: false })
    finalHandler: () => Promise<void> = () => {
        return Promise.resolve();
    };

    @property({ attribute: false })
    state: { [key: string]: unknown } = {};

    firstUpdated(): void {
        this._initialSteps = this.steps;
    }

    setSteps(...steps: string[]): void {
        const addApplyActionsSlot = this.steps.includes(ApplyActionsSlot);
        this.steps = steps;
        if (addApplyActionsSlot) {
            this.steps.push(ApplyActionsSlot);
        }
        this.requestUpdate();
    }

    addActionBefore(displayName: string, run: () => Promise<boolean>): void {
        this.actions.unshift({
            displayName,
            run,
        });
    }

    addActionAfter(displayName: string, run: () => Promise<boolean>): void {
        this.actions.push({
            displayName,
            run,
        });
    }

    renderModalInner(): TemplateResult {
        const firstPage = this.querySelector<WizardPage>(`[slot=${this.steps[0]}]`);
        if (!this.currentStep && firstPage) {
            this.currentStep = firstPage;
        }
        this.currentStep?.requestUpdate();
        const currentIndex = this.currentStep ? this.steps.indexOf(this.currentStep.slot) : 0;
        const lastPage = currentIndex === this.steps.length - 1;
        if (lastPage && !this.steps.includes(ApplyActionsSlot) && this.actions.length > 0) {
            this.steps.push(ApplyActionsSlot);
            const applyActionsPage = document.createElement("ak-wizard-page-action");
            applyActionsPage.slot = ApplyActionsSlot;
            this.appendChild(applyActionsPage);
        }
        return html`<div class="pf-c-wizard">
            <div class="pf-c-wizard__header">
                <button
                    class="pf-c-button pf-m-plain pf-c-wizard__close"
                    type="button"
                    aria-label="${t`Close`}"
                    @click=${() => {
                        this.reset();
                    }}
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
                <h1 class="pf-c-title pf-m-3xl pf-c-wizard__title">${this.header}</h1>
                <p class="pf-c-wizard__description">${this.description}</p>
            </div>
            <div class="pf-c-wizard__outer-wrap">
                <div class="pf-c-wizard__inner-wrap">
                    <nav class="pf-c-wizard__nav">
                        <ol class="pf-c-wizard__nav-list">
                            ${this.steps.map((step, idx) => {
                                const currentIdx = this.currentStep
                                    ? this.steps.indexOf(this.currentStep.slot)
                                    : 0;
                                return html`
                                    <li class="pf-c-wizard__nav-item">
                                        <button
                                            class="pf-c-wizard__nav-link ${idx === currentIdx
                                                ? "pf-m-current"
                                                : ""}"
                                            ?disabled=${currentIdx < idx}
                                            @click=${() => {
                                                const stepEl = this.querySelector<WizardPage>(
                                                    `[slot=${step}]`,
                                                );
                                                if (stepEl) {
                                                    this.currentStep = stepEl;
                                                }
                                            }}
                                        >
                                            ${this.querySelector<WizardPage>(
                                                `[slot=${step}]`,
                                            )?.sidebarLabel()}
                                        </button>
                                    </li>
                                `;
                            })}
                        </ol>
                    </nav>
                    <main class="pf-c-wizard__main">
                        <div class="pf-c-wizard__main-body">
                            <slot name=${this.currentStep?.slot || this.steps[0]}></slot>
                        </div>
                    </main>
                </div>
                <footer class="pf-c-wizard__footer">
                    <button
                        class="pf-c-button pf-m-primary"
                        type="submit"
                        ?disabled=${!this._currentStep?.isValid()}
                        @click=${async () => {
                            const cb = await this.currentStep?.nextCallback();
                            if (!cb) {
                                return;
                            }
                            if (lastPage) {
                                await this.finalHandler();
                                this.reset();
                            } else {
                                const nextPage = this.querySelector<WizardPage>(
                                    `[slot=${this.steps[currentIndex + 1]}]`,
                                );
                                if (nextPage) {
                                    this.currentStep = nextPage;
                                }
                            }
                        }}
                    >
                        ${lastPage ? t`Finish` : t`Next`}
                    </button>
                    ${(this.currentStep ? this.steps.indexOf(this.currentStep.slot) : 0) > 0
                        ? html`
                              <button
                                  class="pf-c-button pf-m-secondary"
                                  type="button"
                                  @click=${() => {
                                      const prevPage = this.querySelector<WizardPage>(
                                          `[slot=${this.steps[currentIndex - 1]}]`,
                                      );
                                      if (prevPage) {
                                          this.currentStep = prevPage;
                                      }
                                  }}
                              >
                                  ${t`Back`}
                              </button>
                          `
                        : html``}
                    <div class="pf-c-wizard__footer-cancel">
                        <button
                            class="pf-c-button pf-m-link"
                            type="button"
                            @click=${() => {
                                const firstPage = this.querySelector<WizardPage>(
                                    `[slot=${this.steps[0]}]`,
                                );
                                if (firstPage) {
                                    this.currentStep = firstPage;
                                }
                                this.reset();
                            }}
                        >
                            ${t`Cancel`}
                        </button>
                    </div>
                </footer>
            </div>
        </div>`;
    }

    reset(): void {
        this.open = false;
        this.querySelectorAll<WizardPage>("*").forEach((el) => {
            if ("_isValid" in el) {
                el._isValid = false;
            }
        });
        this.steps = this._initialSteps;
    }
}
